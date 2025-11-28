from datetime import date

from fastapi import FastAPI, HTTPException, Response, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from authx import AuthX, AuthXConfig
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import dotenv_values
import base64
import tempfile
import ecg_plot
from scipy.io import loadmat

from postgres_db import get_session
from models import User, patients
from schemas import UserLoginSchema


app = FastAPI()

tokens_and_keys = dotenv_values(".env")

origins = [
    "http://localhost",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = AuthXConfig()
config.JWT_SECRET_KEY = tokens_and_keys['SECRET_KEY']
config.JWT_ACCESS_COOKIE_NAME = "my_access_token"
config.JWT_TOKEN_LOCATION = ["cookies"]
config.JWT_COOKIE_CSRF_PROTECT = False

security = AuthX(config=config)


@app.post("/login")
async def login(
    creds: UserLoginSchema,
    response: Response,
    session=Depends(get_session)
):
    query = select(User).where(User.email == creds.email)
    result = await session.execute(query)
    user = result.scalar()
    if not user:
        raise HTTPException(status_code=401, detail="incorrect username or password")
    if creds.password != user.password:
        raise HTTPException(status_code=401, detail="incorrect username or password")
    token = security.create_access_token(uid=str(user.id))
    response.set_cookie(config.JWT_ACCESS_COOKIE_NAME, token, max_age=288000)

    return {"access_token": token}


@app.get("/check-auth")
async def check_auth(user_id: str = Depends(security.access_token_required)):
    return {"status": "ok", "user_id": user_id}

@app.post("/upload-ecg")
async def upload_ecg(
    last_name: str = Form(...),
    first_name: str = Form(...),
    middle_name: str = Form(None),
    exam_date: date = Form(...),
    file: UploadFile = File(...),
    payload = Depends(security.access_token_required),
    session: AsyncSession = Depends(get_session),
):
    doctor_id = int(payload.sub)

    raw_bytes = await file.read()

    # --- 2. Сохраняем во временный .mat файл
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mat") as temp_raw:
        temp_raw.write(raw_bytes)
        temp_raw_path = temp_raw.name

    # --- 3. Загружаем mat-данные
    try:
        mat_data = loadmat(temp_raw_path)
    except Exception:
        raise HTTPException(status_code=400, detail="Ошибка чтения MAT файла")

    # --- 4. Проверяем ключ "data"
    if "data" not in mat_data:
        raise HTTPException(status_code=400, detail="MAT файл не содержит ключ 'data'")

    ecg_signal = mat_data["data"]  # <- ваше поле

    # --- 5. Генерация PNG через ecg_plot
    with tempfile.TemporaryDirectory() as temp_dir:
        png_name = "ecg_output"
        png_path = f"{temp_dir}/{png_name}.png"

        try:
            ecg_plot.plot(ecg_signal, sample_rate=500, title = 'ECG 12')  # при необходимости заменить 500 на реальную частоту
            ecg_plot.save_as_png(png_name, path=temp_dir + "/")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка построения графика: {e}")

        # --- 6. Читаем PNG в память
        with open(png_path, "rb") as img_file:
            png_bytes = img_file.read()

    # --- 7. Сохраняем в базу PostgreSQL
    stmt = patients.insert().values(
        doctor_id=doctor_id,
        last_name=last_name,
        first_name=first_name,
        middle_name=middle_name,
        exam_date=exam_date,
        raw_file=raw_bytes,
        image_png=png_bytes,
        description="test description"
    )

    await session.execute(stmt)
    await session.commit()

    # --- 8. Отправляем PNG на фронт
    return {
        "status": "ok",
        "image_png": base64.b64encode(png_bytes).decode("utf-8")
    }

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, port=8000)
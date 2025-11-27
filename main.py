from fastapi import FastAPI, HTTPException, Response, Depends
import uvicorn
from authx import AuthX, AuthXConfig
from sqlalchemy import select
from dotenv import dotenv_values

from postgres_db import get_session
from models import User
from schemas import UserLoginSchema


app = FastAPI()
tokens_and_keys = dotenv_values(".env")

config = AuthXConfig()
config.JWT_SECRET_KEY = tokens_and_keys['SECRET_KEY']
config.JWT_ACCESS_COOKIE_NAME = "my_access_token"
config.JWT_TOKEN_LOCATION = ["cookies"]

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
    response.set_cookie(config.JWT_ACCESS_COOKIE_NAME, token)

    return {"access_token": token}

@app.post("/protected", dependencies=[Depends(security.access_token_required)])
def protected():
    ...

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
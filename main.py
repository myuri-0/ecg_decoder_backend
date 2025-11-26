from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/login")
def login():
    pass


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
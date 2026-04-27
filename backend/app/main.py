from fastapi import FastAPI
from .database import init_db
from .auth.routes import auth_router
from .routes import game_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(game_router)

@app.get("/")
def test() -> dict[str, str]:
    return {
        "status": "OK"
    }


@app.on_event("startup")
async def startup():
    await init_db()

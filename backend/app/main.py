from fastapi import FastAPI


app = FastAPI()

@app.get("/")
def test() -> dict[str, str]:
    return {
        "status": "OK"
    }

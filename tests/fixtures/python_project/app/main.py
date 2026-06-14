from typing import Optional

from fastapi import FastAPI

app = FastAPI(title="Mock FastAPI App")

@app.get("/")
def read_root():
    return {"message": "Hello from mock FastAPI app"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    print("🧪 SIMPLE TEST ROOT CALLED!")
    return {"message": "Simple FastAPI test working!"}

@app.get("/test")
async def test():
    print("🧪 SIMPLE TEST ENDPOINT CALLED!")
    return {"status": "ok", "message": "Simple test endpoint working!"} 
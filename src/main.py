from fastapi import FastAPI

app = FastAPI(title="FastAPI Webhook Automation")


@app.get("/")
def root():
    return {"message": "FastAPI Webhook Automation is working."}
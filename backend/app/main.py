from fastapi import FastAPI

app = FastAPI(title="Planner Resource API")


@app.get("/health")
def health_check():
    return {"status": "ok"}
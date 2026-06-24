from .database import Base, engine
from fastapi import FastAPI
from .models import AssetPrice
from backend.app.routes.risk import router as risk_router
from backend.app.routes.assets import router as assets_router

app = FastAPI(title="RiskLens-AI API")
Base.metadata.create_all(bind=engine)

app.include_router(risk_router)
app.include_router(assets_router)

@app.get("/")
def root():
    return {"message": "RiskLens-AI API is running"}
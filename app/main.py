from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.database import engine
from app import models
from app.routers import auth, users, calculations, reports

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Calculator API - Final Project", version="7.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(calculations.router)
app.include_router(reports.router)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/static/login.html")


@app.get("/health")
def health():
    return {"status": "ok"}

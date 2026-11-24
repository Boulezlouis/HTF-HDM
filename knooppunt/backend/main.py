"""KnoopPunt — FastAPI-app met CORS, DB-init en demo-seed."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models  # noqa: F401 — registreert alle tabellen op Base.metadata
from database import Base, SessionLocal, engine
from routers import achievements, courses, metrics, nodes
from seed import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    yield


app = FastAPI(title="KnoopPunt", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(courses.router)
app.include_router(nodes.router)
app.include_router(achievements.router)
app.include_router(metrics.router)

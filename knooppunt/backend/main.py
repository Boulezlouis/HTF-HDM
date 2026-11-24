"""KnoopPunt — FastAPI-app met CORS, DB-init en demo-seed."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models  # noqa: F401 — registreert alle tabellen op Base.metadata
from config import settings
from database import Base, SessionLocal, engine
from routers import achievements, courses, metrics, nodes
from seed import ensure_demo_node_sizes, seed_if_empty


def _migrate_node_size_columns() -> None:
    """Idempotente SQLite-migratie voor bestaande databases.

    `create_all` voegt geen kolommen toe aan een bestaande tabel; daarom
    controleren we expliciet via PRAGMA table_info en voegen we de kolommen
    toe met ALTER TABLE wanneer ze ontbreken.
    """
    if not settings.DATABASE_URL.startswith("sqlite"):
        return

    with engine.begin() as connection:
        rows = connection.exec_driver_sql("PRAGMA table_info(nodes)").fetchall()
        columns = {row[1] for row in rows}
        if "difficulty" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE nodes ADD COLUMN difficulty INTEGER NOT NULL DEFAULT 3"
            )
        if "content_volume" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE nodes ADD COLUMN content_volume INTEGER NOT NULL DEFAULT 3"
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _migrate_node_size_columns()
    db = SessionLocal()
    try:
        seed_if_empty(db)
        ensure_demo_node_sizes(db)
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

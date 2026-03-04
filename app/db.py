from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from flask import Flask, g
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


@dataclass(frozen=True)
class Database:
    engine: Engine
    session_factory: Callable[[], Session]


def init_app(app: Flask) -> None:
    database_url = app.config.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    engine = create_engine(database_url, pool_pre_ping=True, future=True)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    app.extensions["database"] = Database(engine=engine, session_factory=session_factory)

    @app.teardown_appcontext
    def _remove_session(_: BaseException | None) -> None:
        db_session: Session | None = getattr(g, "db_session", None)
        if hasattr(g, "db_session"):
            delattr(g, "db_session")
        if db_session is not None:
            db_session.close()


def get_session() -> Session:
    db_session: Session | None = getattr(g, "db_session", None)
    if db_session is not None:
        return db_session

    database: Database | None = getattr(g, "database", None)
    if database is None:
        database = _get_database_from_app()
        setattr(g, "database", database)

    db_session = database.session_factory()
    setattr(g, "db_session", db_session)
    return db_session


def _get_database_from_app() -> Database:
    from flask import current_app

    database = current_app.extensions.get("database")
    if database is None:
        raise RuntimeError("Database is not initialized. Call db.init_app(app) in create_app().")
    return database

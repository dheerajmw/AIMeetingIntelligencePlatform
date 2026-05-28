from __future__ import annotations

from .base import Base
from .session import engine
from . import models  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


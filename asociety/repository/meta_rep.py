from sqlalchemy import Column, String
from sqlalchemy.orm import Mapped
from asociety.repository.database import Base, get_engine

# The per-DB experiment settings. Every pipeline DB carries these; human baselines do not.
META_KEYS = ("llm", "request_method", "question_prompt", "persona_prompt", "model")


class Meta(Base):
    __tablename__ = "meta"
    key: Mapped[str] = Column(String, primary_key=True)
    value: Mapped[str] = Column(String)


def get_meta() -> dict:
    """The current DB's meta as {key: value}; keys absent from the table are missing entirely."""
    from sqlalchemy.orm import Session
    with Session(get_engine()) as session:
        rows = session.query(Meta).all()
    return {r.key: r.value for r in rows}


def set_meta(items: dict) -> None:
    """Upsert the given key/value pairs into the current DB's meta table."""
    from sqlalchemy.orm import Session
    with Session(get_engine()) as session:
        for key, value in items.items():
            existing = session.get(Meta, key)
            if existing is None:
                session.add(Meta(key=key, value=value))
            else:
                existing.value = value
        session.commit()

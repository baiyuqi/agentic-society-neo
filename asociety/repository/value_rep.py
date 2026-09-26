from typing import Optional
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column
from asociety.repository.database import Base, get_engine

# Schwartz PVQ: 10 primary values, each the within-person-centred mean of its items.
VALUE_COLUMNS = [
    'self_direction', 'power', 'universalism', 'achievement', 'security',
    'stimulation', 'conformity', 'tradition', 'hedonism', 'benevolence',
]

# The four higher-order values, each the mean of its constituent primary values.
HIGHER_ORDER_COLUMNS = [
    'openness_to_change', 'self_enhancement', 'self_transcendence', 'conservation',
]

ALL_VALUE_COLUMNS = VALUE_COLUMNS + HIGHER_ORDER_COLUMNS


class Value(Base):
    __tablename__ = "value"
    persona_id: Mapped[int] = Column(Integer, primary_key=True)
    theory: Mapped[str] = mapped_column(String(30), nullable=True)
    question: Mapped[int] = Column(Integer)
    value_json: Mapped[Optional[str]]

    self_direction: Mapped[float] = Column(Float)
    power: Mapped[float] = Column(Float)
    universalism: Mapped[float] = Column(Float)
    achievement: Mapped[float] = Column(Float)
    security: Mapped[float] = Column(Float)
    stimulation: Mapped[float] = Column(Float)
    conformity: Mapped[float] = Column(Float)
    tradition: Mapped[float] = Column(Float)
    hedonism: Mapped[float] = Column(Float)
    benevolence: Mapped[float] = Column(Float)

    openness_to_change: Mapped[float] = Column(Float)
    self_enhancement: Mapped[float] = Column(Float)
    self_transcendence: Mapped[float] = Column(Float)
    conservation: Mapped[float] = Column(Float)

    def __repr__(self) -> str:
        return (f"Value(persona_id={self.persona_id!r}, self_direction={self.self_direction!r}, "
                f"benevolence={self.benevolence!r}, conservation={self.conservation!r})")


# Age buckets mirror persona_personality so the two trees are analysed identically.
_AGE_RANGE_CASE = """CASE
   WHEN persona.age BETWEEN 16 AND 20 THEN '16_19'
  WHEN persona.age BETWEEN 20 AND 30 THEN '20_29'
  WHEN persona.age BETWEEN 30 AND 40 THEN '30_39'
  WHEN persona.age BETWEEN 40 AND 50 THEN '40_49'
  WHEN persona.age BETWEEN 50 AND 60 THEN '50_59'
  WHEN persona.age BETWEEN 60 AND 70 THEN '60_69'
  WHEN persona.age BETWEEN 70 AND 80 THEN '70_79'
  WHEN persona.age BETWEEN 80 AND 90 THEN '80_89'
  WHEN persona.age BETWEEN 90 AND 100 THEN '90_99'
  WHEN persona.age BETWEEN 100 AND 110 THEN '100_109'
END"""

PERSONA_VALUE_VIEW = (
    'CREATE VIEW "persona_value" AS select\n '
    + _AGE_RANGE_CASE
    + ' AS age_range,\npersona.*, value.* from persona, value '
      'where persona.id = value.persona_id'
)


def create_value_view():
    """(Re)create the persona_value view on the current engine."""
    from sqlalchemy import text
    with get_engine().begin() as conn:
        conn.execute(text('DROP VIEW IF EXISTS "persona_value"'))
        conn.execute(text(PERSONA_VALUE_VIEW))


def saveValues(vs):
    from sqlalchemy.orm import Session
    from tqdm import tqdm
    with Session(get_engine()) as session:
        for v in tqdm(vs, desc="Saving values"):
            exists = session.query(Value).filter(Value.persona_id == v.persona_id).first()
            if exists:
                continue
            session.add(v)
        session.commit()


if __name__ == "__main__":
    Base.metadata.create_all(get_engine())

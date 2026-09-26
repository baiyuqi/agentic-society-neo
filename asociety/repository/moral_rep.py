from typing import Optional
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column
from asociety.repository.database import Base, get_engine

# Moral Foundations Questionnaire: 5 foundations, each the raw mean of its items (no centring).
FOUNDATION_COLUMNS = ['care', 'fairness', 'loyalty', 'authority', 'sanctity']

# The two higher-order clusters, each the mean of its constituent foundations.
HIGHER_ORDER_COLUMNS = ['individualizing', 'binding']

ALL_MORALITY_COLUMNS = FOUNDATION_COLUMNS + HIGHER_ORDER_COLUMNS


class Morality(Base):
    __tablename__ = "morality"
    persona_id: Mapped[int] = Column(Integer, primary_key=True)
    theory: Mapped[str] = mapped_column(String(30), nullable=True)
    question: Mapped[int] = Column(Integer)
    morality_json: Mapped[Optional[str]]

    care: Mapped[float] = Column(Float)
    fairness: Mapped[float] = Column(Float)
    loyalty: Mapped[float] = Column(Float)
    authority: Mapped[float] = Column(Float)
    sanctity: Mapped[float] = Column(Float)

    individualizing: Mapped[float] = Column(Float)
    binding: Mapped[float] = Column(Float)

    def __repr__(self) -> str:
        return (f"Morality(persona_id={self.persona_id!r}, care={self.care!r}, "
                f"binding={self.binding!r})")


# Age buckets mirror persona_personality and persona_value so all three trees are analysed
# identically.
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

PERSONA_MORALITY_VIEW = (
    'CREATE VIEW "persona_morality" AS select\n '
    + _AGE_RANGE_CASE
    + ' AS age_range,\npersona.*, morality.* from persona, morality '
      'where persona.id = morality.persona_id'
)


def create_morality_view():
    """(Re)create the persona_morality view on the current engine."""
    from sqlalchemy import text
    with get_engine().begin() as conn:
        conn.execute(text('DROP VIEW IF EXISTS "persona_morality"'))
        conn.execute(text(PERSONA_MORALITY_VIEW))


def saveMorality(ms):
    from sqlalchemy.orm import Session
    from tqdm import tqdm
    with Session(get_engine()) as session:
        for m in tqdm(ms, desc="Saving morality"):
            exists = session.query(Morality).filter(Morality.persona_id == m.persona_id).first()
            if exists:
                continue
            session.add(m)
        session.commit()


if __name__ == "__main__":
    Base.metadata.create_all(get_engine())

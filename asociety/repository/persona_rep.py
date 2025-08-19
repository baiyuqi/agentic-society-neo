from typing import List, Optional
from sqlalchemy import ForeignKey, DateTime, func, Column, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from asociety.repository.database import Base, get_engine

# --- ORM Classes (as designed by user) ---

class SkeletonPersona(Base):
    __tablename__ = "skeleton_persona"
    # All columns from the original census data, minus persona_desc and elicited
    id: Mapped[int] = Column(Integer, primary_key=True)
    age: Mapped[int]
    workclass: Mapped[Optional[str]] = mapped_column(String(30))
    education: Mapped[Optional[str]] = mapped_column(String(30))
    education_num: Mapped[Optional[int]]
    marital_status: Mapped[Optional[str]] = mapped_column(String(30))
    occupation: Mapped[Optional[str]] = mapped_column(String(30))
    relationship: Mapped[Optional[str]] = mapped_column(String(30))
    race: Mapped[Optional[str]] = mapped_column(String(30))
    sex: Mapped[Optional[str]] = mapped_column(String(30))
    capital_gain: Mapped[Optional[int]]
    capital_loss: Mapped[Optional[int]]
    hours_per_week: Mapped[Optional[int]]
    native_country: Mapped[Optional[str]] = mapped_column(String(30))
    income: Mapped[Optional[str]] = mapped_column(String(30))

class Persona(Base):
    __tablename__ = "persona"
    id: Mapped[int] = Column(Integer, primary_key=True)
    sourcePersonaId: Mapped[Optional[str]] = mapped_column(String(30))
    age: Mapped[int]
    workclass: Mapped[Optional[str]] = mapped_column(String(30))
    education: Mapped[Optional[str]] = mapped_column(String(30))
    marital_status: Mapped[Optional[str]] = mapped_column(String(30))
    occupation: Mapped[Optional[str]] = mapped_column(String(30))
    race: Mapped[Optional[str]] = mapped_column(String(30))
    sex: Mapped[Optional[str]] = mapped_column(String(30))
    native_country: Mapped[Optional[str]] = mapped_column(String(30))
    persona_desc: Mapped[Optional[str]]
    elicited: Mapped[Optional[str]]

# --- Data Conversion Functions ---

def to_skeleton_persona(data: dict) -> SkeletonPersona:
    # This function now expects a dictionary from the census CSV
    # and prepares it for the skeleton table.

    
    return SkeletonPersona(
        id = None,
        age=data.get('age'),
        workclass=data.get('workclass'),
        education=data.get('education'),
        education_num=data.get('education.num'),
        marital_status=data.get('marital.status'),
        occupation=data.get('occupation'),
        relationship=data.get('relationship'),
        race=data.get('race'),
        sex=data.get('sex'),
        capital_gain=data.get('capital.gain'),
        capital_loss=data.get('capital.loss'),
        hours_per_week=data.get('hours.per.week'),
        native_country=data.get('native.country'),
        income=data.get('income')
    )

def to_persona(data: dict) -> Persona:
    """Converts a dictionary (usually from a skeleton + enriched desc) to a Persona object."""
    return Persona(
        id=data.get("id"),
        sourcePersonaId=f"{data.get('id')}@skeleton",
        age=data.get("age"),
        workclass=data.get("workclass"),
        education=data.get("education"),
        marital_status=data.get("marital.status"),
        occupation=data.get("occupation"),
        race=data.get("race"),
        sex=data.get("sex"),
        native_country=data.get("native.country"),
        persona_desc=data.get("persona_desc"),
        elicited=data.get("elicited")
    )

def from_skeleton_persona(skeleton: SkeletonPersona) -> dict:
    """Converts a SkeletonPersona object to a dictionary."""
    return {
        'id': skeleton.id,
        'age': skeleton.age,
        'workclass': skeleton.workclass,
        'education': skeleton.education,
        'education.num': skeleton.education_num,
        'marital.status': skeleton.marital_status,
        'occupation': skeleton.occupation,
        'relationship': skeleton.relationship,
        'race': skeleton.race,
        'sex': skeleton.sex,
        'capital.gain': skeleton.capital_gain,
        'capital.loss': skeleton.capital_loss,
        'hours.per.week': skeleton.hours_per_week,
        'native.country': skeleton.native_country,
        'income': skeleton.income
    }

# --- Database Interaction Functions ---

def save_skeleton_personas(skeletons_data: List[dict]):
    """Saves a list of skeleton dictionaries to the database."""


    with Session(get_engine()) as session:
        skeletons = [to_skeleton_persona(p) for p in skeletons_data]
        session.add_all(skeletons)
        session.commit()

def save_enriched_persona(persona_data: dict):
    """Saves a new, complete Persona object to the database."""
    with Session(get_engine()) as session:
        new_persona = to_persona(persona_data)
        session.add(new_persona)
        session.commit()

def get_unprocessed_skeletons() -> List[dict]:
    """
    Retrieves all skeletons that do not have a corresponding entry in the persona table
    by comparing ID sets, without using an ORM-level relationship.
    """
    with Session(get_engine()) as session:
        # Step 1: Get all IDs from skeleton_persona
        skeleton_ids = session.query(SkeletonPersona.id).all()
        skeleton_id_set = {s_id for s_id, in skeleton_ids}

        # Step 2: Get all IDs from persona
        persona_ids = session.query(Persona.id).all()
        persona_id_set = {p_id for p_id, in persona_ids}
        
        # Step 3: Find the difference
        unprocessed_ids = skeleton_id_set - persona_id_set
        
        if not unprocessed_ids:
            return []
            
        # Step 4: Query for the actual skeleton objects
        unprocessed_skeletons = session.query(SkeletonPersona).filter(SkeletonPersona.id.in_(unprocessed_ids)).all()
        
        return [from_skeleton_persona(s) for s in unprocessed_skeletons]

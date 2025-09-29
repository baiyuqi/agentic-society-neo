from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String,Float
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String
from asociety.repository.database import Base

class Question(Base):
    __tablename__ = "question"
    __table_args__ = {'extend_existing': True} 
    id: Mapped[int] =  Column(Integer, primary_key=True, autoincrement=True)
    question:  Mapped[Optional[str]]
    options:  Mapped[Optional[str]]
    answer:  Mapped[Optional[str]]
    def __repr__(self) -> str:
        return f"Question(id={self.id!r}, question='{self.question[:30] if self.question else ''}...')"

class QuestionAnswer(Base):
    __tablename__ = "question_answer"
    __table_args__ = {'extend_existing': True} 
    persona_id: Mapped[str] = mapped_column(String(30),nullable=False,primary_key=True)
    question_id: Mapped[str] = mapped_column(String(30),nullable=False,primary_key=True)
    agent_answer: Mapped[Optional[str]]
    agent_solution: Mapped[Optional[str]]
    response: Mapped[Optional[str]]
    def __repr__(self) -> str:
        return f"QuestionAnswer(persona_id={self.persona_id!r}, question_id={self.question_id!r}, answer={self.agent_answer!r})"
class QuizAnswer(Base):
    __tablename__ = "quiz_answer"

    sheet_id: Mapped[str] = mapped_column(String(30),nullable=True,primary_key=True)
    persona_id: Mapped[str] = mapped_column(String(30),nullable=True,primary_key=True)
    agent_answer: Mapped[Optional[str]]
    response: Mapped[Optional[str]]



class QuizSheet(Base):
    __tablename__ = "quiz_sheet"
    id: Mapped[int] =  Column(Integer, primary_key=True)
    sheet: Mapped[Optional[str]]  # Content of the quiz sheet, likely JSON


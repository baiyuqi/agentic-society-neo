import sys
import os

# Add the project root to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from asociety.repository.database import Base, get_engine

# Import all the models that need to be created.
# SQLAlchemy's Base collects metadata from all imported classes that inherit from it.
from asociety.repository.experiment_rep import Question, QuestionAnswer, QuizAnswer, QuizSheet
from asociety.repository.persona_rep import Persona
from asociety.repository.personality_rep import Personality

def initialize_database():
    """
    Connects to the database and creates all tables defined by the models
    that inherit from the Base class.
    """
    print("Initializing database...")
    engine = get_engine()
    
    print("Creating all tables based on imported models...")
    # This command checks for the existence of each table before creating it,
    # so it's safe to run multiple times.
    Base.metadata.create_all(engine)
    
    print("Database tables created successfully (if they didn't already exist).")

if __name__ == "__main__":
    initialize_database()

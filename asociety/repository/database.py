import os
from sqlalchemy import create_engine
from asociety import config
from sqlalchemy.orm import DeclarativeBase
import threading

class Base(DeclarativeBase):
    pass

# 全局 currentdb 路径和 engine
_currentdb_path = None
_engine = None
_engine_lock = threading.Lock()

def get_default_db_path():
    """
    Constructs the correct SQLite database path from the config setting.
    It handles cases where the setting may or may not include the 'data/db/' prefix
    and may or may not include the '.db' suffix.
    """
    db_setting = config.configuration['database']
    
    # The root of the project is three levels up from this file's location
    # (asociety/repository/database.py -> asociety/ -> repository/ -> root)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # 1. Determine the correct relative path
    if str(db_setting).startswith('data/db/'):
        relative_path = db_setting
    else:
        relative_path = os.path.join('data', 'db', db_setting)

    # 2. Ensure the path ends with .db
    if not relative_path.endswith('.db'):
        relative_path += '.db'
        
    # 3. Create the absolute path for the sqlite URI
    absolute_path = os.path.join(project_root, relative_path).replace('\\', '/')
    
    return f'sqlite:///{absolute_path}'

def get_engine():
    global _engine, _currentdb_path
    with _engine_lock:
        if _engine is None:
            _currentdb_path = get_default_db_path()
            _engine = create_engine(_currentdb_path)
        return _engine

def set_currentdb(db_path):
    '''db_path: 绝对或相对sqlite文件路径，如 data/db/xxx.db'''
    global _engine, _currentdb_path
    with _engine_lock:
        if db_path.startswith('sqlite:///'):
            new_path = db_path
        else:
            # When setting a path manually, we need to resolve it to an absolute path
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            absolute_path = os.path.join(project_root, db_path).replace('\\', '/')
            new_path = 'sqlite:///' + absolute_path

        if new_path != _currentdb_path:
            _currentdb_path = new_path
            _engine = create_engine(_currentdb_path)

def get_currentdb_path():
    global _currentdb_path
    if _currentdb_path is None:
        _currentdb_path = get_default_db_path()
    return _currentdb_path

def create_tables():
    """
    Creates all tables defined in the Base metadata if they don't already exist.
    This is safe to call on every run.
    """
    engine = get_engine()
    # The import is done here to avoid circular dependencies
    from asociety.repository import persona_rep, personality_rep, experiment_rep
    Base.metadata.create_all(engine)
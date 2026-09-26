import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
import threading

class Base(DeclarativeBase):
    pass

# 全局 currentdb 路径和 engine
_currentdb_path = None
_engine = None
_engine_lock = threading.Lock()

def get_default_db_path():
    """There is no default database: every entry point selects one explicitly."""
    raise RuntimeError(
        "No database selected. Call set_currentdb(db_path) or config.load_from_db(db_path) "
        "before get_engine().")

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
    from asociety.repository import (persona_rep, personality_rep, experiment_rep, value_rep,
                                     moral_rep, meta_rep)
    Base.metadata.create_all(engine)
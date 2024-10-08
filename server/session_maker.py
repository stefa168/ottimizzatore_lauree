from threading import Lock

import sqlalchemy
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker


class SessionMakerSingleton:
    _session_maker: sessionmaker | None = None
    _engine: Engine | None = None
    _lock = Lock()  # To ensure thread-safety during initialization

    @classmethod
    def initialize(cls, connection_string: str | sqlalchemy.URL, **kwargs):
        with cls._lock:
            if cls._session_maker is None:
                cls._engine = create_engine(connection_string, **kwargs)
                cls._session_maker = sessionmaker(bind=cls._engine)

    @classmethod
    def get_session_maker(cls) -> sessionmaker:
        if cls._session_maker is None:
            raise Exception("SessionMakerSingleton is not initialized.")
        return cls._session_maker

    @classmethod
    def get_engine(cls) -> Engine:
        if cls._session_maker is None:
            raise Exception("SessionMakerSingleton is not initialized.")
        return cls._engine

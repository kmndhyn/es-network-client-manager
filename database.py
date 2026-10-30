from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from paths import DB_PATH

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class ImportMeta(Base):
    __tablename__ = "import_meta"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_file = Column(String(255), unique=True)
    columns = Column(Text)  # JSON list of original column names
    imported_at = Column(DateTime, server_default=func.now())


class ClientRow(Base):
    __tablename__ = "client_rows"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_file = Column(String(255))
    row_index = Column(Integer)  # original Excel row, -1 = manually added
    data = Column(Text)  # JSON dict of column -> value
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()

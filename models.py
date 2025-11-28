from sqlalchemy import Column, Integer, String, Table, Date, LargeBinary, MetaData, Text
from postgres_db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)


metadata = MetaData()

patients = Table(
    "patients",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("doctor_id", Integer, nullable=False),
    Column("last_name", String(100), nullable=False),
    Column("first_name", String(100), nullable=False),
    Column("middle_name", String(100)),
    Column("exam_date", Date, nullable=False),
    Column("raw_file", LargeBinary),
    Column("image_png", LargeBinary),
    Column("description", Text)
)
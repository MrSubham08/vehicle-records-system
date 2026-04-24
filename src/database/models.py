# This file is intended for defining database models using an ORM (Object-Relational Mapper)
# such as SQLAlchemy or Peewee.

# Using an ORM can simplify database interactions by representing tables as Python classes
# and rows as objects.

# If you are using the direct SQL approach in db_manager.py, this file may not be necessary.

# Example using SQLAlchemy (requires installation: pip install SQLAlchemy)
# from sqlalchemy import create_engine, Column, Integer, String, DateTime, Enum
# from sqlalchemy.orm import sessionmaker, declarative_base
# import datetime
# import enum

# Base = declarative_base()

# class EventTypeEnum(enum.Enum):
#     ENTRY = "ENTRY"
#     EXIT = "EXIT"
#     DETECTED = "DETECTED"

# class VehicleLog(Base):
#     __tablename__ = 'vehicle_logs' # Matches the table name in db_manager.py

#     id = Column(Integer, primary_key=True)
#     timestamp = Column(DateTime, default=datetime.datetime.now, nullable=False)
#     camera_id = Column(String, nullable=False)
#     license_plate = Column(String, nullable=True)
#     event_type = Column(Enum(EventTypeEnum), nullable=False)
#     image_path = Column(String, nullable=True)

#     def __repr__(self):
#         return f"<VehicleLog(id={self.id}, timestamp='{self.timestamp}', plate='{self.license_plate}', event='{self.event_type.value}')>"

# # --- How you might use it (elsewhere in the code, typically replacing db_manager functions) ---
# # from .models import Base, VehicleLog
# # from sqlalchemy import create_engine
# # from sqlalchemy.orm import sessionmaker
# # import yaml

# # # Load DB path from config
# # try:
# #     with open('config/config.yaml', 'r') as f:
# #         config = yaml.safe_load(f)
# #     DB_PATH = config['database']['path']
# #     SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}" # Adjust for other DBs (e.g., postgresql://...)
# # except (FileNotFoundError, KeyError, yaml.YAMLError):
# #     SQLALCHEMY_DATABASE_URL = "sqlite:///./vehicle_log_default.db"

# # engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}) # check_same_thread for SQLite
# # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # def init_db():
# #    # Create tables
# #    Base.metadata.create_all(bind=engine)

# # def get_db():
# #     db = SessionLocal()
# #     try:
# #         yield db
# #     finally:
# #         db.close()

# # # Example usage (e.g., within a function that receives a db session):
# # # def log_event_orm(db: Session, camera_id: str, event_type: EventTypeEnum, license_plate: str = None):
# # #     db_log = VehicleLog(camera_id=camera_id, event_type=event_type, license_plate=license_plate)
# # #     db.add(db_log)
# # #     db.commit()
# # #     db.refresh(db_log)
# # #     return db_log
# # ---------------------------------------------------------------------
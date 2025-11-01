from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 🔹 Your Render PostgreSQL connection URL
SQLALCHEMY_DATABASE_URL = "postgresql://fastapi_db_jne5_user:LYFP0O10Tb5rcjbvxSHFKPsFZVk1Dr5j@dpg-d42slkv5r7bs73bbgv40-a/fastapi_db_jne5"

# Create engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

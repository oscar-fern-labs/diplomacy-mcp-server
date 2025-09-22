import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", "")
    secret_key: str = os.getenv("SECRET_KEY", "change-me")

settings = Settings()

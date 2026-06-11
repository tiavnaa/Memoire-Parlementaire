from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    app_name: str = "Parlement Madagascar Explorer"
    app_version: str = "1.0.0"
    debug: bool = True
    
    elastic_cloud_id: str = os.getenv("ELASTIC_CLOUD_ID", "")
    elasticsearch_url: str = os.getenv("ELASTICSEARCH_URL", "")
    elasticsearch_api_key: str = os.getenv("ELASTICSEARCH_API_KEY", "")
    elasticsearch_username: str = os.getenv("ELASTICSEARCH_USERNAME", "elastic")
    elasticsearch_password: str = os.getenv("ELASTICSEARCH_PASSWORD", "")
    
    index_debats: str = "debats_publics"
    index_deputes: str = "deputes"
    index_seances: str = "seances"
    index_legislatifs: str = "textes_legislatifs"
    
    cors_origins: List[str] = eval(os.getenv("CORS_ORIGINS", '["http://localhost:8000"]'))
    
    class Config:
        env_file = ".env"

settings = Settings()
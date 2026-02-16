# File: config/settings.py
from dataclasses import dataclass


@dataclass
class APIConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True


class Config:
    api = APIConfig()

    # Пути к данным
    DATABASE_PATH = "data/app.db"
    EXCEL_PATH = "data/articles.xlsx"

# File: api/schemas.py
from pydantic import BaseModel, validator
from typing import Optional, List, Dict

class QuestionRequest(BaseModel):
    question: str
    user_id: Optional[str] = None

class RecommendationResponse(BaseModel):
    answer: str
    recommended_article: Dict
    suggested_actions: List[str]
    session_id: str
    confidence: float

class SessionStatsResponse(BaseModel):
    user_id: str
    created_at: str
    interaction_count: int
    total_reward: float
    avg_reward: float

class TrainingResponse(BaseModel):
    status: str
    episodes_completed: int
    average_reward: float

# Схемы для работы со статьями
class ArticleCreate(BaseModel):
    title: str
    content: str
    url: str
    tags: List[str] = []

    @validator('title')
    def validate_title(cls, v):
        if len(v) < 3 or len(v) > 200:
            raise ValueError('Title must be 3-200 characters')
        return v

    @validator('content')
    def validate_content(cls, v):
        if len(v) < 10:
            raise ValueError('Content must be at least 10 characters')
        return v

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    url: Optional[str] = None
    tags: Optional[List[str]] = None

    @validator('title')
    def validate_title(cls, v):
        if v is not None and (len(v) < 3 or len(v) > 200):
            raise ValueError('Title must be 3-200 characters')
        return v

    @validator('content')
    def validate_content(cls, v):
        if v is not None and len(v) < 10:
            raise ValueError('Content must be at least 10 characters')
        return v

class ArticleResponse(BaseModel):
    id: int
    title: str
    content: str
    url: Optional[str] = ""
    tags: List[str]

class ArticleListResponse(BaseModel):
    articles: List[ArticleResponse]
    total: int
    offset: int
    limit: int

# Схемы для истории чата
class ChatMessage(BaseModel):
    timestamp: str
    sender: str  # "user" или "bot"
    message: str
    article: Optional[Dict] = None  # Для ответов бота с рекомендацией

class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessage]
    total: int
# File: api/app.py
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import Dict, List, Optional
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
import os
import tempfile
from security import create_access_token, get_current_user, get_admin_user, TokenData
from auth.user_db import UserDatabase
from .schemas import (
    QuestionRequest, RecommendationResponse, SessionStatsResponse,
    ArticleCreate, ArticleUpdate, ArticleResponse, ArticleListResponse,
    ChatHistoryResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecommendationAPI:
    def __init__(self, article_db, session_manager, rag_pipeline):
        self.article_db = article_db
        self.session_manager = session_manager
        self.rag_pipeline = rag_pipeline
        self.user_db = UserDatabase()
        if not self.user_db.get_user("admin"):
            self.user_db.create_user("admin", "admin", role="admin")

        # Инициализация менеджера тегов
        from database.tag_manager import TagManager
        self.tag_manager = TagManager(self.article_db)

        self.app = FastAPI(title="RL Recommendation System API")
        self.setup_middleware()
        self.setup_routes()
        self.setup_static_files()

    def setup_middleware(self):
        """Настройка CORS middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_static_files(self):
        """Настройка статических файлов для фронтенда"""
        # Создаем директорию frontend если не существует
        os.makedirs("frontend", exist_ok=True)
        
        # Mount static files
        self.app.mount("/static", StaticFiles(directory="frontend"), name="static")
    
    def setup_routes(self):
        @self.app.post("/register")
        async def register(form_data: OAuth2PasswordRequestForm = Depends()):
            success = self.user_db.create_user(form_data.username, form_data.password)
            if not success:
                raise HTTPException(status_code=400, detail="Username already exists")
            return {"message": "User created successfully"}

        @self.app.post("/login")
        async def login(form_data: OAuth2PasswordRequestForm = Depends()):
            if not self.user_db.authenticate_user(form_data.username, form_data.password):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            # Получаем роль пользователя
            role = self.user_db.get_user_role(form_data.username)
            token = create_access_token(data={"sub": form_data.username, "role": role})
            return {"access_token": token, "token_type": "bearer", "role": role}

        @self.app.get("/verify")
        async def verify_token(current_user: TokenData = Depends(get_current_user)):
            """Проверка валидности токена и получение актуальной роли из БД"""
            # Получаем актуальную роль из базы данных, а не из токена
            actual_role = self.user_db.get_user_role(current_user.user_id)
            return {"valid": True, "username": current_user.user_id, "role": actual_role}

        @self.app.get("/users")
        async def get_all_users(current_user: TokenData = Depends(get_current_user)):
            """Получение списка всех пользователей (только имена)"""
            usernames = list(self.user_db.users.keys())
            return {"users": usernames, "total": len(usernames)}

        # Endpoints для управления пользователями (только для админов)
        @self.app.get("/admin/users")
        async def get_all_users_admin(current_user: TokenData = Depends(get_admin_user)):
            """Получение полного списка пользователей (только для админов)"""
            try:
                users = self.user_db.get_all_users()
                return {"users": users, "total": len(users)}
            except Exception as e:
                logger.error(f"Error getting users: {e}")
                raise HTTPException(500, str(e))

        @self.app.post("/admin/users")
        async def create_user_admin(
            username: str = Form(...),
            password: str = Form(...),
            role: str = Form("user"),
            current_user: TokenData = Depends(get_admin_user)
        ):
            """Создание нового пользователя (только для админов)"""
            try:
                if role not in ["admin", "user"]:
                    raise HTTPException(400, "Invalid role")
                success = self.user_db.create_user(username, password, role)
                if not success:
                    raise HTTPException(400, "Username already exists")
                return {"status": "success", "username": username}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error creating user: {e}")
                raise HTTPException(500, str(e))

        @self.app.delete("/admin/users/{username}")
        async def delete_user_admin(
            username: str,
            current_user: TokenData = Depends(get_admin_user)
        ):
            """Удаление пользователя (только для админов)"""
            try:
                if username == current_user.user_id:
                    raise HTTPException(400, "Cannot delete yourself")
                success = self.user_db.delete_user(username)
                if not success:
                    raise HTTPException(400, "Cannot delete user (user not found or last admin)")
                return {"status": "success", "username": username}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error deleting user: {e}")
                raise HTTPException(500, str(e))

        @self.app.put("/admin/users/{username}/role")
        async def update_user_role(
            username: str,
            role: str = Form(...),
            current_user: TokenData = Depends(get_admin_user)
        ):
            """Изменение роли пользователя (только для админов)"""
            try:
                success = self.user_db.set_user_role(username, role)
                if not success:
                    raise HTTPException(400, "Cannot update role")
                return {"status": "success", "username": username, "role": role}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error updating role: {e}")
                raise HTTPException(500, str(e))

        @self.app.put("/admin/users/{username}/toggle-active")
        async def toggle_user_active(
            username: str,
            current_user: TokenData = Depends(get_admin_user)
        ):
            """Активация/деактивация пользователя (только для админов)"""
            try:
                if username == current_user.user_id:
                    raise HTTPException(400, "Cannot deactivate yourself")
                success = self.user_db.toggle_user_active(username)
                if not success:
                    raise HTTPException(400, "Cannot toggle user (user not found or last active admin)")
                return {"status": "success", "username": username}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error toggling user: {e}")
                raise HTTPException(500, str(e))

        @self.app.put("/admin/users/{username}/password")
        async def update_user_password(
            username: str,
            new_password: str = Form(...),
            current_user: TokenData = Depends(get_admin_user)
        ):
            """Изменение пароля пользователя (только для админов)"""
            try:
                success = self.user_db.update_password(username, new_password)
                if not success:
                    raise HTTPException(404, "User not found")
                return {"status": "success", "username": username}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error updating password: {e}")
                raise HTTPException(500, str(e))

        @self.app.get("/")
        async def root():
            return {"message": "RL Recommendation System API", "status": "running"}
        
        @self.app.post("/ask", response_model=RecommendationResponse)
        async def ask_question(
            request: QuestionRequest,
            current_user: TokenData = Depends(get_current_user)
        ):
            """Основной endpoint для вопросов с RAG"""
            try:
                user_id = current_user.user_id
                # Создаем или получаем сессию
                if user_id not in self.session_manager.sessions:
                    self.session_manager.create_session(user_id)

                # Используем RAG pipeline для генерации ответа
                logger.info(f"Processing question with RAG: {request.question}")
                rag_result = self.rag_pipeline.query(
                    question=request.question,
                    language="ru"
                )

                # Формируем рекомендуемую статью из источников
                if rag_result.get('sources'):
                    primary_source = rag_result['sources'][0]
                    raw_score = primary_source.get('relevance_score', 0)
                    # Нормализуем score к диапазону 0-1 для confidence
                    normalized_confidence = max(0, min(1, raw_score / 10))
                    recommended_article_info = {
                        "id": primary_source.get('id', 0),  # Добавляем ID статьи
                        "title": primary_source['title'],
                        "url": primary_source['url'],
                        "confidence": round(normalized_confidence, 2)
                    }
                else:
                    # Fallback если источников нет
                    recommended_article_info = {
                        "id": 0,
                        "title": "Информация не найдена",
                        "url": "",
                        "confidence": 0.0
                    }

                # Формируем список всех источников для ответа
                all_sources = rag_result.get('sources', [])

                # Используем ответ как есть, без добавления источников
                # (источник уже отображается на зеленом поле)
                answer_with_sources = rag_result['answer']

                # Сохраняем взаимодействие (используем первый источник как "статью")
                if all_sources:
                    # Создаем псевдо-статью для совместимости с session_manager
                    pseudo_article = {
                        'id': primary_source.get('id', 0),  # Используем реальный ID статьи
                        'title': all_sources[0]['title'],
                        'url': all_sources[0]['url'],
                        'content': rag_result['answer'][:200]  # Краткое содержание
                    }
                    reward = 1.0  # Считаем успешным
                    self.session_manager.add_interaction(
                        user_id, request.question, pseudo_article, reward
                    )

                # Формируем предложенные действия
                suggested_actions = [
                    "Задать уточняющий вопрос",
                    "Получить дополнительную информацию",
                    "Оценить полезность ответа"
                ]

                return RecommendationResponse(
                    answer=answer_with_sources,
                    recommended_article=recommended_article_info,
                    suggested_actions=suggested_actions,
                    session_id=user_id,
                    confidence=recommended_article_info["confidence"]
                )

            except Exception as e:
                logger.error(f"Error processing question: {e}")
                import traceback
                logger.error(traceback.format_exc())
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/session/{user_id}", response_model=SessionStatsResponse)
        async def get_session_stats(
            user_id: str,
            current_user: TokenData = Depends(get_current_user)
        ):
            if current_user.user_id != user_id:
                raise HTTPException(status_code=403, detail="Access forbidden")

            """Получение статистики сессии"""
            stats = self.session_manager.get_session_stats(user_id)
            if not stats:
                raise HTTPException(status_code=404, detail="Session not found")
            return SessionStatsResponse(**stats)

        @self.app.get("/chat/history", response_model=ChatHistoryResponse)
        async def get_chat_history(
            limit: int = 100,
            current_user: TokenData = Depends(get_current_user)
        ):
            """Получение истории чата текущего пользователя"""
            try:
                user_id = current_user.user_id
                messages = self.session_manager.get_formatted_chat_history(user_id, limit)
                return ChatHistoryResponse(messages=messages, total=len(messages))
            except Exception as e:
                logger.error(f"Error getting chat history: {e}")
                raise HTTPException(500, str(e))

        @self.app.delete("/chat/history")
        async def clear_chat_history(
            current_user: TokenData = Depends(get_current_user)
        ):
            """Очистка истории чата текущего пользователя"""
            try:
                user_id = current_user.user_id
                success = self.session_manager.clear_chat_history(user_id)
                if not success:
                    raise HTTPException(500, "Failed to clear chat history")
                return {"status": "success", "message": "История чата успешно очищена"}
            except Exception as e:
                logger.error(f"Error clearing chat history: {e}")
                raise HTTPException(500, str(e))

        @self.app.get("/articles")
        async def get_articles():
            """Получение всех статей"""
            articles = self.article_db.get_all_articles()
            return {"articles": articles}
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "articles_count": len(self.article_db.get_all_articles()),
                "sessions_count": len(self.session_manager.sessions)
            }
        @self.app.get("/chat")
        async def chat_interface():
            """Serve the chat interface"""
            return FileResponse("frontend/chat.html")
        
        @self.app.get("/")
        async def root():
            return {
                "message": "RL Recommendation System API",
                "status": "running",
                "endpoints": {
                    "api_docs": "/docs",
                    "chat_interface": "/chat",
                    "ask_question": "/ask",
                    "health_check": "/health",
                    "admin_panel": "/admin"
                }
            }

        # CRUD endpoints для админ-панели
        @self.app.post("/admin/articles", response_model=ArticleResponse)
        async def create_article(
            article: ArticleCreate,
            current_user: TokenData = Depends(get_admin_user)
        ):
            """Создание новой статьи (только для админов)"""
            try:
                article_dict = article.dict()
                article_id = self.article_db.add_article(article_dict)
                created = self.article_db.get_article(article_id)
                if not created:
                    raise HTTPException(500, "Failed to create article")
                return ArticleResponse(**created)
            except Exception as e:
                logger.error(f"Error creating article: {e}")
                raise HTTPException(500, str(e))

        @self.app.put("/admin/articles/{article_id}", response_model=ArticleResponse)
        async def update_article(
            article_id: int,
            article: ArticleUpdate,
            current_user: TokenData = Depends(get_admin_user)
        ):
            """Обновление статьи (только для админов)"""
            try:
                update_data = {k: v for k, v in article.dict().items() if v is not None}
                success = self.article_db.update_article(article_id, update_data)
                if not success:
                    raise HTTPException(404, "Article not found")
                updated = self.article_db.get_article(article_id)
                return ArticleResponse(**updated)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error updating article: {e}")
                raise HTTPException(500, str(e))

        @self.app.delete("/admin/articles/{article_id}")
        async def delete_article(
            article_id: int,
            current_user: TokenData = Depends(get_admin_user)
        ):
            """Удаление статьи (только для админов)"""
            try:
                success = self.article_db.delete_article(article_id)
                if not success:
                    raise HTTPException(404, "Article not found")
                return {"status": "deleted", "article_id": article_id}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error deleting article: {e}")
                raise HTTPException(500, str(e))

        @self.app.get("/admin/articles/{article_id}", response_model=ArticleResponse)
        async def get_article_admin(
            article_id: int,
            current_user: TokenData = Depends(get_admin_user)
        ):
            """Получение одной статьи по ID (только для админов)"""
            try:
                article = self.article_db.get_article(article_id)
                if not article:
                    raise HTTPException(404, "Article not found")
                return ArticleResponse(**article)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting article: {e}")
                raise HTTPException(500, str(e))

        @self.app.get("/admin/articles", response_model=ArticleListResponse)
        async def list_articles_admin(
            offset: int = 0,
            limit: int = 20,
            search: str = None,
            tags: str = None,
            current_user: TokenData = Depends(get_admin_user)
        ):
            """Список статей с фильтрацией и пагинацией (только для админов)"""
            try:
                tag_list = [t.strip() for t in tags.split(",")] if tags else None
                result = self.article_db.get_articles_paginated(offset, limit, search, tag_list)
                return ArticleListResponse(**result)
            except Exception as e:
                logger.error(f"Error listing articles: {e}")
                raise HTTPException(500, str(e))

        @self.app.get("/admin")
        async def serve_admin_panel():
            """Отдача админ-панели (проверка прав на клиенте)"""
            return FileResponse("frontend/admin.html")

        @self.app.get("/favicon.svg")
        async def serve_favicon():
            """Отдача favicon"""
            return FileResponse("frontend/favicon.svg", media_type="image/svg+xml")

        @self.app.get("/favicon.ico")
        async def serve_favicon_ico():
            """Редирект на SVG favicon для старых браузеров"""
            return FileResponse("frontend/favicon.svg", media_type="image/svg+xml")

        @self.app.post("/admin/upload")
        async def upload_document(
            file: UploadFile = File(...),
            url: Optional[str] = Form(None),
            tags: str = Form(""),
            current_user: TokenData = Depends(get_admin_user)
        ):
            """Загрузка и парсинг документа (только для админов)"""
            try:
                # Валидация размера
                content = await file.read()
                if len(content) > 10 * 1024 * 1024:  # 10 MB
                    raise HTTPException(400, "File too large (max 10MB)")

                # Валидация типа
                ext = os.path.splitext(file.filename)[1].lower()
                if ext not in ['.pdf', '.docx', '.md', '.markdown']:
                    raise HTTPException(400, f"Unsupported file type: {ext}")

                # Сохранение временного файла
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name

                try:
                    # Парсинг
                    from utils.document_parsers import DocumentProcessor
                    processor = DocumentProcessor()
                    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                    article_dict = processor.process_file(tmp_path, url, tag_list)

                    # Добавление в БД
                    article_id = self.article_db.add_article(article_dict)
                    created_article = self.article_db.get_article(article_id)

                    return {
                        "status": "success",
                        "article_id": article_id,
                        "article": created_article
                    }
                finally:
                    # Удаление временного файла
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Upload processing error: {e}")
                raise HTTPException(500, f"Processing failed: {str(e)}")

        # Endpoints для управления тегами
        @self.app.get("/admin/tags")
        async def get_tags(current_user: TokenData = Depends(get_admin_user)):
            """Получение всех тегов с количеством использований"""
            try:
                tags = self.tag_manager.get_all_tags()
                return {"tags": tags, "total": len(tags)}
            except Exception as e:
                logger.error(f"Error getting tags: {e}")
                raise HTTPException(500, str(e))

        @self.app.put("/admin/tags/{old_tag}")
        async def rename_tag(
            old_tag: str,
            new_tag: str = Form(...),
            current_user: TokenData = Depends(get_admin_user)
        ):
            """Переименование тега"""
            try:
                count = self.tag_manager.rename_tag(old_tag, new_tag)
                return {"status": "success", "updated_articles": count}
            except Exception as e:
                logger.error(f"Error renaming tag: {e}")
                raise HTTPException(500, str(e))

        @self.app.delete("/admin/tags/{tag}")
        async def delete_tag(
            tag: str,
            current_user: TokenData = Depends(get_admin_user)
        ):
            """Удаление тега из всех статей"""
            try:
                count = self.tag_manager.delete_tag(tag)
                return {"status": "success", "updated_articles": count}
            except Exception as e:
                logger.error(f"Error deleting tag: {e}")
                raise HTTPException(500, str(e))
        # Endpoints для аналитики
        @self.app.get("/admin/analytics/overview")
        async def get_analytics_overview(current_user: TokenData = Depends(get_admin_user)):
            """Общая аналитика системы"""
            try:
                analytics = self.session_manager.get_global_analytics()
                return analytics
            except Exception as e:
                logger.error(f"Error getting analytics: {e}")
                raise HTTPException(500, str(e))

        @self.app.get("/admin/analytics/articles/{article_id}")
        async def get_article_analytics(
            article_id: int,
            current_user: TokenData = Depends(get_admin_user)
        ):
            """Аналитика по статье"""
            try:
                analytics = self.session_manager.get_article_analytics(article_id)
                return analytics
            except Exception as e:
                logger.error(f"Error getting article analytics: {e}")
                raise HTTPException(500, str(e))

        @self.app.get("/admin/analytics/timeline")
        async def get_timeline_analytics(
            days: int = 7,
            current_user: TokenData = Depends(get_admin_user)
        ):
            """Временная аналитика"""
            try:
                analytics = self.session_manager.get_timeline_analytics(days)
                return analytics
            except Exception as e:
                logger.error(f"Error getting timeline analytics: {e}")
                raise HTTPException(500, str(e))

        # Endpoints для RAG
        @self.app.post("/admin/rag/reindex")
        async def reindex_articles(
            rebuild: bool = False,
            current_user: TokenData = Depends(get_admin_user)
        ):
            """Переиндексация статей в векторное хранилище"""
            try:
                articles = self.article_db.get_all_articles()
                logger.info(f"Reindexing {len(articles)} articles (rebuild={rebuild})...")
                self.rag_pipeline.index_articles(articles, rebuild=rebuild)
                stats = self.rag_pipeline.get_stats()
                return {
                    "status": "success",
                    "articles_indexed": len(articles),
                    "stats": stats
                }
            except Exception as e:
                logger.error(f"Error reindexing articles: {e}")
                raise HTTPException(500, str(e))

        @self.app.get("/admin/rag/stats")
        async def get_rag_stats(current_user: TokenData = Depends(get_admin_user)):
            """Получить статистику RAG pipeline"""
            try:
                stats = self.rag_pipeline.get_stats()
                return stats
            except Exception as e:
                logger.error(f"Error getting RAG stats: {e}")
                raise HTTPException(500, str(e))

# File: main.py
import uvicorn
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth.user_db import UserDatabase
from config.settings import Config
from database.article_db import ArticleDatabase
from database.session_manager import SessionManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def initialize_system():
    """Инициализация системы"""
    logger.info("Initializing RAG Recommendation System...")

    try:
        config = Config()
        logger.info("Configuration loaded")

        # Инициализация базы данных статей
        article_db = ArticleDatabase()
        articles = article_db.get_all_articles()
        logger.info(f"Loaded {len(articles)} articles")

        # Инициализация базы пользователей
        user_db = UserDatabase()
        if not user_db.get_user("admin"):
            user_db.create_user("admin", "admin", role="admin")
        logger.info("User database initialized")

        if not articles:
            logger.error("No articles available. System cannot start.")
            return None

        # Инициализация менеджера сессий
        session_manager = SessionManager()
        logger.info(f"Loaded {len(session_manager.sessions)} existing sessions")

        # Инициализация RAG Pipeline
        from rag.rag_pipeline import RAGPipeline
        from api.app import RecommendationAPI

        logger.info("Initializing RAG Pipeline...")
        rag_pipeline = RAGPipeline(
            chunk_size=800,  # Увеличено для лучшего контекста (было 512)
            chunk_overlap=100,  # Увеличено для плавного перехода (было 50)
            persist_directory="data/chroma_db",
            collection_name="articles",
            embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",  # Multilingual модель для русского
            reranker_model="cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",  # Multilingual reranker
            llm_model="qwen2.5:7b",  # Модель с отличной поддержкой русского языка
            llm_base_url="http://localhost:11434",
            retrieval_top_k=30,  # Увеличено для лучшего покрытия (было 20)
            rerank_top_k=5
        )

        # Индексируем статьи в векторное хранилище
        logger.info("Indexing articles in vector store...")
        rag_pipeline.index_articles(articles, rebuild=False)
        stats = rag_pipeline.get_stats()
        logger.info(f"RAG Pipeline ready! Stats: {stats}")

        return {
            'config': config,
            'article_db': article_db,
            'user_db': user_db,
            'session_manager': session_manager,
            'rag_pipeline': rag_pipeline,
            'api_class': RecommendationAPI
        }

    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def main():
    components = initialize_system()

    if components is None:
        logger.error("System initialization failed. Exiting.")
        return

    try:
        # Создание API
        api = components['api_class'](
            article_db=components['article_db'],
            session_manager=components['session_manager'],
            rag_pipeline=components['rag_pipeline']
        )

        logger.info("Starting FastAPI server...")
        logger.info(f"API will be available at: http://{components['config'].api.host}:{components['config'].api.port}")
        logger.info(f"API documentation: http://{components['config'].api.host}:{components['config'].api.port}/docs")
        logger.info(f"Chat UI: http://{components['config'].api.host}:{components['config'].api.port}/chat")

        uvicorn.run(
            api.app,
            host=components['config'].api.host,
            port=components['config'].api.port,
            log_level="info"
        )

    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()

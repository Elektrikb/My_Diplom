# File: test_rag.py
"""
Тестовый скрипт для проверки RAG pipeline
"""
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.article_db import ArticleDatabase
from rag.rag_pipeline import RAGPipeline
from config.settings import Config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_rag_pipeline():
    """Тест RAG pipeline"""
    print("=" * 80)
    print("RAG PIPELINE TEST")
    print("=" * 80)

    # Инициализация
    config = Config()
    article_db = ArticleDatabase(config.ARTICLES_PATH, config.EXCEL_PATH)
    articles = article_db.get_all_articles()

    print(f"\n✓ Loaded {len(articles)} articles from database")

    # Создание RAG pipeline
    print("\n" + "=" * 80)
    print("Initializing RAG Pipeline...")
    print("=" * 80)

    rag_pipeline = RAGPipeline(
        chunk_size=512,
        chunk_overlap=50,
        persist_directory="data/chroma_db_test",  # Тестовая директория
        collection_name="test_articles",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2",
        llm_model="llama3.2",
        llm_base_url="http://localhost:11434",
        retrieval_top_k=10,
        rerank_top_k=3
    )

    # Индексация статей
    print("\n" + "=" * 80)
    print("Indexing articles...")
    print("=" * 80)
    rag_pipeline.index_articles(articles, rebuild=True)

    # Статистика
    stats = rag_pipeline.get_stats()
    print(f"\n✓ RAG Pipeline Stats:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")

    # Тестовые вопросы
    test_questions = [
        "Как начать программировать на Python?",
        "Что такое машинное обучение?",
        "Расскажи о рекомендательных системах",
        "Какие алгоритмы используются в ML?",
    ]

    print("\n" + "=" * 80)
    print("Testing RAG Pipeline with sample questions")
    print("=" * 80)

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'=' * 80}")
        print(f"QUESTION {i}: {question}")
        print("=" * 80)

        try:
            result = rag_pipeline.query(question, language="ru")

            print(f"\n📝 ANSWER:")
            print(result['answer'])

            print(f"\n📚 SOURCES ({len(result.get('sources', []))}):")
            for j, source in enumerate(result.get('sources', []), 1):
                score = source.get('relevance_score', 0)
                print(f"  {j}. {source['title']} (score: {score:.3f})")
                print(f"     URL: {source['url']}")

            print(f"\n📊 PIPELINE STATS:")
            pipeline_steps = result.get('pipeline_steps', {})
            print(f"  - Retrieved chunks: {pipeline_steps.get('retrieval', 0)}")
            print(f"  - Reranked chunks: {pipeline_steps.get('reranking', 0)}")
            print(f"  - Generation: {pipeline_steps.get('generation', 'unknown')}")
            print(f"  - Model: {result.get('model', 'unknown')}")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    print("\n🚀 Starting RAG Pipeline Test...\n")
    print("⚠️  Make sure Ollama is running: ollama serve")
    print("⚠️  Make sure llama3.2 model is installed: ollama pull llama3.2\n")

    try:
        test_rag_pipeline()
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

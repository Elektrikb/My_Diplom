# File: test_system.py
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_question(question, user_id=None):
    """Тестирование одного вопроса"""
    print(f"\n{'='*60}")
    print(f"📝 ВОПРОС: {question}")
    print(f"{'='*60}")
    
    payload = {"question": question}
    if user_id:
        payload["user_id"] = user_id
    
    try:
        response = requests.post(f"{BASE_URL}/ask", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            
            print("🤖 ОТВЕТ СИСТЕМЫ:")
            print(result["answer"])
            print(f"\n📊 ДЕТАЛИ:")
            print(f"   Уверенность: {result['confidence']:.2f}")
            print(f"   Session ID: {result['session_id']}")
            print(f"   Рекомендованная статья: {result['recommended_article']['title']}")
            print(f"   Ссылка: {result['recommended_article']['url']}")
            
            return result["session_id"]
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"❌ Ошибка соединения: {e}")
        return None

def get_session_stats(session_id):
    """Получение статистики сессии"""
    print(f"\n📈 СТАТИСТИКА СЕССИИ {session_id}:")
    
    try:
        response = requests.get(f"{BASE_URL}/session/{session_id}")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"   Создана: {stats['created_at']}")
            print(f"   Взаимодействий: {stats['interaction_count']}")
            print(f"   Общий reward: {stats['total_reward']:.2f}")
            print(f"   Средний reward: {stats['avg_reward']:.2f}")
        else:
            print(f"   Ошибка получения статистики: {response.status_code}")
            
    except Exception as e:
        print(f"   Ошибка соединения: {e}")

def test_multiple_questions():
    """Тестирование нескольких вопросов в одной сессии"""
    print("🚀 ТЕСТИРОВАНИЕ RL-РЕКОМЕНДАТЕЛЬНОЙ СИСТЕМЫ")
    print("=" * 60)
    
    # Первый вопрос - создаем новую сессию
    session_id = test_question("Как начать программировать на Python?")
    
    if session_id:
        # Второй вопрос в той же сессии
        time.sleep(1)
        test_question("Какие фреймворки для веб-разработки есть в Python?", session_id)
        
        # Третий вопрос
        time.sleep(1)
        test_question("Что такое машинное обучение?", session_id)
        
        # Получаем статистику сессии
        get_session_stats(session_id)

def test_different_topics():
    """Тестирование разных тем"""
    print("\n🎯 ТЕСТИРОВАНИЕ РАЗНЫХ ТЕМ")
    print("=" * 60)
    
    questions = [
        "Как установить PyTorch?",
        "Что такое reinforcement learning?",
        "Объясните основы компьютерных сетей",
        "Какие базы данных лучше использовать?",
        "Что такое DevOps?"
    ]
    
    for question in questions:
        test_question(question)
        time.sleep(1)

if __name__ == "__main__":
    # Тестируем последовательность вопросов в одной сессии
    test_multiple_questions()
    
    # Тестируем разные темы
    test_different_topics()
# File: rag/llm_generator.py
"""
Модуль для генерации ответов с использованием Ollama LLM
"""
import logging
import requests
import re
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class LLMGenerator:
    """Класс для генерации ответов с помощью Ollama"""

    def __init__(
        self,
        model_name: str = "llama3.2",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ):
        """
        Args:
            model_name: Имя модели Ollama
            base_url: URL Ollama API
            temperature: Температура для генерации
            max_tokens: Максимальное количество токенов в ответе
        """
        self.model_name = model_name
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_url = f"{base_url}/api/generate"

        # Проверяем доступность Ollama
        self._check_ollama_availability()

    def _check_ollama_availability(self):
        """Проверить доступность Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"Ollama is available at {self.base_url}")
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                if self.model_name not in model_names and f"{self.model_name}:latest" not in model_names:
                    logger.warning(
                        f"Model '{self.model_name}' not found in Ollama. "
                        f"Available models: {model_names}. "
                        f"Please run: ollama pull {self.model_name}"
                    )
            else:
                logger.warning(f"Ollama returned status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.warning(
                f"Cannot connect to Ollama at {self.base_url}. "
                f"Error: {e}. Please make sure Ollama is running."
            )

    def _create_prompt(
        self,
        question: str,
        context_chunks: List[Dict],
        language: str = "ru"
    ) -> str:
        """
        Создать промпт для LLM

        Args:
            question: Вопрос пользователя
            context_chunks: Релевантные чанки с контекстом
            language: Язык ответа

        Returns:
            Промпт для LLM
        """
        # Формируем контекст из чанков
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            metadata = chunk.get('metadata', {})
            article_title = metadata.get('article_title', 'Unknown')
            article_url = metadata.get('article_url', '')
            text = chunk.get('text', '')

            context_parts.append(
                f"[Источник {i}: {article_title}]\n{text}\nURL: {article_url}\n"
            )

        context = "\n\n".join(context_parts)

        # Создаем промпт
        if language == "ru":
            prompt = f"""Ты - русскоязычный ассистент-эксперт. КРИТИЧЕСКИ ВАЖНО: отвечай ИСКЛЮЧИТЕЛЬНО на русском языке!

КОНТЕКСТ:
{context}

ВОПРОС: {question}

СТРОГИЕ ТРЕБОВАНИЯ:
1. Отвечай ТОЛЬКО на русском языке - никаких латинских букв, иностранных слов или символов (кроме цифр и знаков препинания)
2. Используй ИСКЛЮЧИТЕЛЬНО информацию из предоставленного контекста выше
3. Если информации недостаточно для полного ответа, честно скажи: "В предоставленном контексте недостаточно информации для полного ответа на этот вопрос"
4. Обязательно указывай источники номерами в квадратных скобках: [1], [2] и т.д.
5. Структурируй ответ для максимальной читаемости и понятности
6. Будь конкретным и информативным
7. НЕ добавляй информацию, которой нет в контексте
8. НЕ используй английские технические термины без крайней необходимости

ОТВЕТ (строго на русском языке):"""
        else:
            prompt = f"""You are an expert assistant. CRITICAL: Answer EXCLUSIVELY in English!

CONTEXT:
{context}

QUESTION: {question}

STRICT REQUIREMENTS:
1. Answer ONLY in English - use proper English grammar and vocabulary
2. Use EXCLUSIVELY information from the provided context above
3. If there's insufficient information, honestly state: "The provided context does not contain enough information to fully answer this question"
4. Always cite sources with numbers in square brackets: [1], [2], etc.
5. Structure your answer for maximum readability and clarity
6. Be specific and informative
7. Do NOT add information not present in the context
8. Avoid unnecessary technical jargon

ANSWER (strictly in English):"""

        return prompt

    def _clean_answer(self, answer: str, language: str = "ru") -> str:
        """
        Очистка ответа от нежелательных символов и форматирования

        Args:
            answer: Сгенерированный ответ
            language: Язык ответа

        Returns:
            Очищенный ответ
        """
        if not answer:
            return answer

        # Удаляем лишние пробелы и переносы строк
        answer = re.sub(r'\n{3,}', '\n\n', answer)  # Максимум 2 переноса подряд
        answer = re.sub(r' {2,}', ' ', answer)  # Удаляем множественные пробелы
        answer = answer.strip()

        # Для русского языка - проверяем наличие подозрительных паттернов
        if language == "ru":
            # Удаляем артефакты вроде "ANSWER:", "ОТВЕТ:" в начале
            answer = re.sub(r'^(ANSWER|ОТВЕТ|Answer|Ответ)\s*:\s*', '', answer, flags=re.IGNORECASE)

            # Если ответ начинается с латинских букв (кроме [1], [2] и т.д.), предупреждаем
            if re.match(r'^[A-Za-z]{3,}', answer):
                logger.warning(f"Answer may contain foreign text at start: {answer[:50]}...")

        return answer

    def generate(
        self,
        question: str,
        context_chunks: List[Dict],
        language: str = "ru"
    ) -> Dict:
        """
        Сгенерировать ответ на вопрос с использованием контекста

        Args:
            question: Вопрос пользователя
            context_chunks: Релевантные чанки
            language: Язык ответа

        Returns:
            Словарь с ответом и метаданными
        """
        try:
            # Создаем промпт
            prompt = self._create_prompt(question, context_chunks, language)

            # Отправляем запрос к Ollama
            logger.info(f"Generating answer with {self.model_name}...")

            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            }

            response = requests.post(
                self.api_url,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                answer_text = result.get('response', '').strip()

                # Очищаем ответ от нежелательных символов
                answer_text = self._clean_answer(answer_text, language)

                # Извлекаем источники из контекста
                sources = []
                for chunk in context_chunks:
                    metadata = chunk.get('metadata', {})
                    source = {
                        'id': int(metadata.get('article_id', 0)),  # Добавляем ID статьи
                        'title': metadata.get('article_title', 'Unknown'),
                        'url': metadata.get('article_url', ''),
                        'relevance_score': chunk.get('rerank_score', chunk.get('score', 0))
                    }
                    # Избегаем дубликатов
                    if source not in sources:
                        sources.append(source)

                logger.info("Answer generated successfully")

                return {
                    'answer': answer_text,
                    'sources': sources,
                    'model': self.model_name,
                    'num_chunks_used': len(context_chunks)
                }
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return self._fallback_answer(question, context_chunks)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to Ollama: {e}")
            return self._fallback_answer(question, context_chunks)
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return self._fallback_answer(question, context_chunks)

    def _fallback_answer(self, question: str, context_chunks: List[Dict]) -> Dict:
        """
        Создать резервный ответ, если LLM недоступен

        Args:
            question: Вопрос пользователя
            context_chunks: Релевантные чанки

        Returns:
            Словарь с ответом
        """
        logger.warning("Using fallback answer generation")

        # Простой ответ на основе первого чанка
        if context_chunks:
            first_chunk = context_chunks[0]
            metadata = first_chunk.get('metadata', {})
            text = first_chunk.get('text', '')

            answer = f"По вашему вопросу '{question}' найдена релевантная информация:\n\n{text}\n\n"
            answer += f"Источник: {metadata.get('article_title', 'Unknown')}"

            sources = [{
                'id': int(metadata.get('article_id', 0)),  # Добавляем ID статьи
                'title': metadata.get('article_title', 'Unknown'),
                'url': metadata.get('article_url', ''),
                'relevance_score': first_chunk.get('rerank_score', first_chunk.get('score', 0))
            }]
        else:
            answer = "К сожалению, не удалось найти релевантную информацию для ответа на ваш вопрос."
            sources = []

        return {
            'answer': answer,
            'sources': sources,
            'model': 'fallback',
            'num_chunks_used': len(context_chunks)
        }

    def set_model(self, model_name: str):
        """Сменить модель"""
        self.model_name = model_name
        logger.info(f"Switched to model: {model_name}")

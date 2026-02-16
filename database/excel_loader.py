import pandas as pd
import requests
from typing import List, Dict
import logging
import os
from urllib.parse import urlparse
import time

logger = logging.getLogger(__name__)

class ExcelArticleLoader:
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
    
    def load_articles_from_excel(self) -> List[Dict]:
        """Загрузка статей из Excel файла"""
        try:
            # Читаем Excel файл
            df = pd.read_excel(self.excel_path)
            logger.info(f"Loaded Excel file with {len(df)} rows")
            
            articles = []
            
            for index, row in df.iterrows():
                try:
                    article = self._process_row(row, index)
                    if article:
                        articles.append(article)
                        logger.info(f"Processed article: {article['title']}")
                    
                    # Небольшая задержка чтобы не перегружать сервер
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error processing row {index}: {e}")
                    continue
            
            logger.info(f"Successfully processed {len(articles)} articles")
            return articles
            
        except Exception as e:
            logger.error(f"Error loading Excel file: {e}")
            return []
    
    def _process_row(self, row, index: int) -> Dict:
        """Обработка одной строки Excel"""
        url = str(row.iloc[0]).strip()  # Первая колонка - URL
        
        if not url or url.lower() == 'nan':
            return None
        
        # Получаем заголовок и контент по URL
        title, content = self._fetch_article_content(url)
        
        if not title:
            # Если не удалось получить заголовок, создаем из URL
            title = self._generate_title_from_url(url)
        
        return {
            'id': index,
            'title': title,
            'content': content or 'Содержание статьи недоступно',
            'url': url,
            'tags': self._extract_tags(content) if content else []
        }
    
    def _fetch_article_content(self, url: str) -> tuple:
        """Получение заголовка и контента статьи по URL"""
        try:
            # Для Habr и других популярных сайтов можно использовать API
            if 'habr.com' in url:
                return self._fetch_habr_content(url)
            else:
                # Общий метод для других сайтов
                return self._fetch_generic_content(url)
                
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {e}")
            return None, None
    
    def _fetch_habr_content(self, url: str) -> tuple:
        """Получение контента с Habr"""
        try:
            # Habr имеет API, но для простоты используем заглушки
            # В реальном проекте нужно использовать официальное API
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                # Парсим HTML для получения заголовка
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Ищем заголовок
                title_tag = soup.find('h1') or soup.find('title')
                title = title_tag.get_text().strip() if title_tag else "Статья с Habr"
                
                # Ищем основной контент
                content_div = soup.find('div', {'class': 'article-formatted-body'})
                content = content_div.get_text().strip() if content_div else "Содержание недоступно"
                
                return title, content
            else:
                return f"Статья с Habr {url}", None
                
        except Exception as e:
            logger.error(f"Error parsing Habr content: {e}")
            return f"Статья с Habr {url}", None
    
    def _fetch_generic_content(self, url: str) -> tuple:
        """Общий метод получения контента"""
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Удаляем скрипты и стили
                for script in soup(["script", "style"]):
                    script.decompose()
                
                title = soup.find('title')
                title_text = title.get_text().strip() if title else self._generate_title_from_url(url)
                
                # Получаем текст из body
                content = soup.get_text()
                lines = (line.strip() for line in content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                content = ' '.join(chunk for chunk in chunks if chunk)
                
                # Обрезаем контент до разумной длины
                content = content[:2000] + "..." if len(content) > 2000 else content
                
                return title_text, content
            else:
                return self._generate_title_from_url(url), None
                
        except Exception as e:
            logger.error(f"Error fetching generic content: {e}")
            return self._generate_title_from_url(url), None
    
    def _generate_title_from_url(self, url: str) -> str:
        """Генерация заголовка из URL"""
        parsed = urlparse(url)
        domain = parsed.netloc
        path_parts = [part for part in parsed.path.split('/') if part]
        
        if path_parts:
            # Берем последнюю часть пути как заголовок
            title = path_parts[-1].replace('-', ' ').replace('_', ' ')
            return title.capitalize()
        else:
            return f"Статья с {domain}"
    
    def _extract_tags(self, content: str) -> List[str]:
        """Извлечение тегов из контента (упрощенная версия)"""
        if not content:
            return []
        
        # Ключевые слова для тегов
        keywords = {
            'python': ['python', 'питон', 'django', 'flask'],
            'ml': ['машинное обучение', 'machine learning', 'нейронные', 'ai'],
            'web': ['веб', 'web', 'html', 'css', 'javascript'],
            'devops': ['devops', 'docker', 'kubernetes', 'ci/cd'],
            'database': ['база данных', 'sql', 'postgresql', 'mysql'],
            'algorithms': ['алгоритм', 'структура данных', 'сортировка']
        }
        
        content_lower = content.lower()
        tags = []
        
        for tag, keyword_list in keywords.items():
            if any(keyword in content_lower for keyword in keyword_list):
                tags.append(tag)
        
        return tags[:3]  # Максимум 3 тега
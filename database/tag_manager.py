# File: database/tag_manager.py
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class TagManager:
    def __init__(self, article_db):
        self.article_db = article_db

    def get_all_tags(self) -> Dict[str, int]:
        """Возврат всех тегов с количеством использований"""
        tag_counts = {}
        for article in self.article_db.get_all_articles():
            for tag in article.get('tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True))

    def rename_tag(self, old_tag: str, new_tag: str) -> int:
        """Переименование тега во всех статьях. Возврат количества обновленных статей."""
        count = 0
        for article in self.article_db.get_all_articles():
            if old_tag in article.get('tags', []):
                article['tags'] = [new_tag if t == old_tag else t for t in article['tags']]
                self.article_db.update_article(article['id'], article)
                count += 1
        logger.info(f"Renamed tag '{old_tag}' to '{new_tag}' in {count} articles")
        return count

    def delete_tag(self, tag: str) -> int:
        """Удаление тега из всех статей. Возврат количества обновленных статей."""
        count = 0
        for article in self.article_db.get_all_articles():
            if tag in article.get('tags', []):
                article['tags'] = [t for t in article['tags'] if t != tag]
                self.article_db.update_article(article['id'], article)
                count += 1
        logger.info(f"Deleted tag '{tag}' from {count} articles")
        return count

    def merge_tags(self, source_tags: List[str], target_tag: str) -> int:
        """Объединение нескольких тегов в один. Возврат количества обновленных статей."""
        count = 0
        for article in self.article_db.get_all_articles():
            tags = article.get('tags', [])
            has_source = any(t in source_tags for t in tags)
            if has_source:
                # Удаляем все source_tags и добавляем target_tag
                new_tags = [t for t in tags if t not in source_tags]
                if target_tag not in new_tags:
                    new_tags.append(target_tag)
                article['tags'] = new_tags
                self.article_db.update_article(article['id'], article)
                count += 1
        logger.info(f"Merged tags {source_tags} into '{target_tag}' in {count} articles")
        return count

    def get_articles_by_tag(self, tag: str) -> List[Dict]:
        """Получение всех статей с указанным тегом"""
        return [a for a in self.article_db.get_all_articles() if tag in a.get('tags', [])]

# File: utils/document_parsers.py
from abc import ABC, abstractmethod
from typing import Dict, Optional, List
import os
import logging

logger = logging.getLogger(__name__)

class BaseDocumentParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> Dict[str, str]:
        """Парсинг документа. Возврат: {title, content, metadata}"""
        pass

    @abstractmethod
    def supports(self, extension: str) -> bool:
        """Проверка поддержки расширения"""
        pass

class PDFParser(BaseDocumentParser):
    def supports(self, extension: str) -> bool:
        return extension.lower() == '.pdf'

    def parse(self, file_path: str) -> Dict[str, str]:
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)

            full_text = "\n".join(text_parts)
            # Первая строка как заголовок (или имя файла)
            title = full_text.split('\n')[0][:100] if full_text else os.path.basename(file_path)

            return {
                "title": title.strip(),
                "content": full_text,
                "metadata": {"pages": len(text_parts)}
            }
        except ImportError:
            logger.error("pdfplumber not installed. Install it with: pip install pdfplumber")
            raise ValueError("PDF parsing library not installed")
        except Exception as e:
            logger.error(f"PDF parsing error: {e}")
            raise ValueError(f"Failed to parse PDF: {str(e)}")

class DOCXParser(BaseDocumentParser):
    def supports(self, extension: str) -> bool:
        return extension.lower() == '.docx'

    def parse(self, file_path: str) -> Dict[str, str]:
        try:
            from docx import Document
            doc = Document(file_path)

            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            full_text = "\n".join(paragraphs)

            title = paragraphs[0][:100] if paragraphs else os.path.basename(file_path)

            return {
                "title": title.strip(),
                "content": full_text,
                "metadata": {"paragraphs": len(paragraphs)}
            }
        except ImportError:
            logger.error("python-docx not installed. Install it with: pip install python-docx")
            raise ValueError("DOCX parsing library not installed")
        except Exception as e:
            logger.error(f"DOCX parsing error: {e}")
            raise ValueError(f"Failed to parse DOCX: {str(e)}")

class MarkdownParser(BaseDocumentParser):
    def supports(self, extension: str) -> bool:
        return extension.lower() in ['.md', '.markdown']

    def parse(self, file_path: str) -> Dict[str, str]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Извлечение заголовка (первый # Title)
            lines = content.split('\n')
            title = None
            for line in lines:
                if line.strip().startswith('#'):
                    title = line.strip('#').strip()[:100]
                    break

            if not title:
                title = os.path.basename(file_path)

            return {
                "title": title,
                "content": content,
                "metadata": {"lines": len(lines)}
            }
        except Exception as e:
            logger.error(f"Markdown parsing error: {e}")
            raise ValueError(f"Failed to parse Markdown: {str(e)}")

class DocumentProcessor:
    def __init__(self):
        self.parsers = {
            'pdf': PDFParser(),
            'docx': DOCXParser(),
            'md': MarkdownParser(),
            'markdown': MarkdownParser()
        }

    def process_file(self, file_path: str, url: Optional[str] = None,
                     tags: Optional[List[str]] = None) -> Dict:
        """
        Обработка файла и возврат структуры статьи
        """
        ext = os.path.splitext(file_path)[1].lower()
        parser_key = ext[1:]  # убираем точку

        if parser_key not in self.parsers:
            raise ValueError(f"Unsupported file type: {ext}")

        parser = self.parsers[parser_key]
        parsed = parser.parse(file_path)

        # Формирование статьи
        article = {
            "title": parsed["title"],
            "content": parsed["content"],
            "url": url or f"file://{os.path.abspath(file_path)}",
            "tags": tags or []
        }

        return article

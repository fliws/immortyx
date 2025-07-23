#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Парсер-агент для мультиагентной системы сбора информации о продлении жизни
Работает под управлением координатора, загружает метаданные и PDF статей
"""

import requests
import xml.etree.ElementTree as ET
import time
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote, urljoin, urlparse
import re
from datetime import datetime
import hashlib

from pubmed_parser import PubMedParser
from agent_coordinator import AgentCoordinator


class AgentParser(PubMedParser):
    """Расширенный парсер-агент с поддержкой загрузки PDF и работы с координатором"""
    
    def __init__(self, coordinator: AgentCoordinator, 
                 email: str = None, api_key: str = None,
                 pdf_dir: str = "longevity_pdfs"):
        """
        Инициализация парсера-агента
        
        Args:
            coordinator: Экземпляр координатора
            email: Email для API PubMed
            api_key: API ключ PubMed
            pdf_dir: Директория для сохранения PDF файлов
        """
        super().__init__(email=email, api_key=api_key)
        self.coordinator = coordinator
        self.pdf_dir = Path(pdf_dir)
        self.pdf_dir.mkdir(exist_ok=True)
        
        # Настройки PDF загрузки
        self.pdf_sources = [
            'pmc',           # PubMed Central
            'doi_redirect',  # Переадресация через DOI
            'unpaywall',     # Unpaywall API
            'arxiv',         # ArXiv препринты
            'biorxiv'        # BioRxiv препринты
        ]
        
        # Статистика парсера
        self.session_stats = {
            'queries_processed': 0,
            'articles_found': 0,
            'pdfs_attempted': 0,
            'pdfs_downloaded': 0,
            'errors': 0
        }
        
        print(f"🤖 Парсер-агент инициализирован. PDF директория: {self.pdf_dir}")

    def run_autonomous_session(self, max_queries: int = 20, 
                             download_pdfs: bool = True) -> Dict:
        """
        Автономный режим работы с координатором
        
        Args:
            max_queries: Максимальное количество запросов для обработки
            download_pdfs: Скачивать ли PDF файлы
            
        Returns:
            Статистика сессии
        """
        print(f"🚀 Запуск автономной сессии: {max_queries} запросов, PDF={'ВКЛ' if download_pdfs else 'ВЫКЛ'}")
        
        session_start = datetime.now()
        processed_queries = 0
        
        try:
            while processed_queries < max_queries:
                # Получаем запросы от координатора
                queries = self.coordinator.get_next_queries(min(5, max_queries - processed_queries))
                
                if not queries:
                    print("📋 Координатор не предоставил новых запросов. Сессия завершена.")
                    break
                
                # Обрабатываем каждый запрос
                for query_info in queries:
                    try:
                        self._process_single_query(query_info, download_pdfs)
                        processed_queries += 1
                        
                        # Пауза между запросами
                        if processed_queries < len(queries):
                            time.sleep(1)
                            
                    except Exception as e:
                        print(f"❌ Ошибка обработки запроса {query_info['hash'][:8]}: {e}")
                        self.coordinator.report_query_results(
                            query_info['hash'], [], 0, str(e)
                        )
                        self.session_stats['errors'] += 1
                        continue
                
                # Показываем промежуточную статистику
                if processed_queries % 5 == 0:
                    self._print_session_progress()
        
        except KeyboardInterrupt:
            print("\n⛔ Сессия прервана пользователем")
        
        except Exception as e:
            print(f"\n❌ Критическая ошибка сессии: {e}")
        
        # Финальная статистика
        session_time = datetime.now() - session_start
        final_stats = self._get_final_stats(session_time, processed_queries)
        
        print(f"\n🏁 Сессия завершена за {session_time}")
        print(f"📊 Обработано запросов: {processed_queries}")
        print(f"📄 Найдено статей: {self.session_stats['articles_found']}")
        print(f"📁 Скачано PDF: {self.session_stats['pdfs_downloaded']}")
        
        return final_stats
    
    def _process_single_query(self, query_info: Dict, download_pdfs: bool = True):
        """Обработка одного запроса"""
        query_hash = query_info['hash']
        query_text = query_info['query']
        theme = query_info['theme']
        
        print(f"\n🔍 Обрабатываю: {query_text} (тема: {theme})")
        
        # Выполняем поиск
        articles = self.search_and_fetch(
            query=query_text,
            max_results=query_info['max_results'],
            date_from=query_info.get('date_from'),
            date_to=query_info.get('date_to')
        )
        
        self.session_stats['queries_processed'] += 1
        self.session_stats['articles_found'] += len(articles)
        
        # Загружаем PDF если требуется
        pdfs_downloaded = 0
        if download_pdfs and articles:
            pdfs_downloaded = self._download_pdfs_for_articles(articles, theme)
        
        # Отчитываемся координатору
        self.coordinator.report_query_results(query_hash, articles, pdfs_downloaded)
        
        print(f"✅ Запрос обработан: {len(articles)} статей, {pdfs_downloaded} PDF")
    
    def _download_pdfs_for_articles(self, articles: List[Dict], theme: str) -> int:
        """
        Загрузка PDF файлов для списка статей
        
        Args:
            articles: Список статей
            theme: Тема исследования для организации файлов
            
        Returns:
            Количество успешно скачанных PDF
        """
        if not articles:
            return 0
        
        # Создаем папку для темы
        theme_dir = self.pdf_dir / theme
        theme_dir.mkdir(exist_ok=True)
        
        downloaded_count = 0
        
        print(f"📥 Начинаю загрузку PDF для {len(articles)} статей...")
        
        for i, article in enumerate(articles, 1):
            pmid = article.get('pmid', '')
            doi = article.get('doi', '')
            title = article.get('title', '')[:50]  # Ограничиваем длину
            
            if not pmid:
                continue
            
            try:
                # Пытаемся найти и скачать PDF
                pdf_path = self._download_single_pdf(article, theme_dir)
                
                if pdf_path:
                    downloaded_count += 1
                    print(f"  ✅ {i}/{len(articles)}: PDF скачан - {pdf_path.name}")
                else:
                    print(f"  ❌ {i}/{len(articles)}: PDF не найден - PMID:{pmid}")
                
                self.session_stats['pdfs_attempted'] += 1
                
                # Пауза между загрузками
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ❌ {i}/{len(articles)}: Ошибка загрузки PDF - {e}")
                continue
        
        self.session_stats['pdfs_downloaded'] += downloaded_count
        return downloaded_count
    
    def _download_single_pdf(self, article: Dict, save_dir: Path) -> Optional[Path]:
        """
        Загрузка PDF для одной статьи
        
        Args:
            article: Информация о статье
            save_dir: Директория для сохранения
            
        Returns:
            Путь к скачанному файлу или None
        """
        pmid = article.get('pmid', '')
        doi = article.get('doi', '')
        title = article.get('title', '').replace('/', '_').replace('\\', '_')
        
        # Генерируем имя файла
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)[:80]  # Безопасное имя файла
        filename = f"PMID_{pmid}_{safe_title}.pdf"
        file_path = save_dir / filename
        
        # Проверяем, не скачан ли уже файл
        if file_path.exists():
            return file_path
        
        # Пробуем различные источники PDF
        for source in self.pdf_sources:
            try:
                pdf_url = self._find_pdf_url(article, source)
                if pdf_url:
                    if self._download_pdf_from_url(pdf_url, file_path):
                        return file_path
            except Exception as e:
                continue
        
        return None
    
    def _find_pdf_url(self, article: Dict, source: str) -> Optional[str]:
        """
        Поиск URL PDF файла из различных источников
        
        Args:
            article: Информация о статье
            source: Источник поиска ('pmc', 'doi_redirect', 'unpaywall', etc.)
            
        Returns:
            URL PDF файла или None
        """
        pmid = article.get('pmid', '')
        doi = article.get('doi', '')
        
        if source == 'pmc':
            return self._get_pmc_pdf_url(pmid)
        
        elif source == 'doi_redirect' and doi:
            return self._get_doi_pdf_url(doi)
        
        elif source == 'unpaywall' and doi:
            return self._get_unpaywall_pdf_url(doi)
        
        elif source == 'arxiv':
            return self._get_arxiv_pdf_url(article)
        
        elif source == 'biorxiv':
            return self._get_biorxiv_pdf_url(article)
        
        return None
    
    def _get_pmc_pdf_url(self, pmid: str) -> Optional[str]:
        """Получение PDF URL из PubMed Central"""
        if not pmid:
            return None
        
        try:
            # Проверяем, есть ли статья в PMC
            url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
            params = {
                'dbfrom': 'pubmed',
                'db': 'pmc',
                'id': pmid,
                'retmode': 'xml'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                return None
            
            root = ET.fromstring(response.content)
            pmc_ids = [id_elem.text for id_elem in root.findall('.//Id')]
            
            if len(pmc_ids) > 1:  # Первый ID - это PMID, остальные - PMC
                pmc_id = pmc_ids[1]
                return f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/"
        
        except Exception:
            pass
        
        return None
    
    def _get_doi_pdf_url(self, doi: str) -> Optional[str]:
        """Получение PDF URL через переадресацию DOI"""
        if not doi:
            return None
        
        try:
            # Попытка получить PDF через sci-hub (осторожно с легальностью!)
            # Здесь можно добавить другие легальные источники
            doi_url = f"https://doi.org/{doi}"
            
            # Простая проверка на открытый доступ
            response = requests.head(doi_url, timeout=5, allow_redirects=True)
            if 'pdf' in response.headers.get('content-type', '').lower():
                return doi_url
        
        except Exception:
            pass
        
        return None
    
    def _get_unpaywall_pdf_url(self, doi: str) -> Optional[str]:
        """Получение PDF URL через Unpaywall API"""
        if not doi:
            return None
        
        try:
            url = f"https://api.unpaywall.org/v2/{doi}"
            params = {'email': self.email or 'user@example.com'}
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('is_oa'):  # Открытый доступ
                    best_oa = data.get('best_oa_location')
                    if best_oa and best_oa.get('url_for_pdf'):
                        return best_oa['url_for_pdf']
        
        except Exception:
            pass
        
        return None
    
    def _get_arxiv_pdf_url(self, article: Dict) -> Optional[str]:
        """Поиск PDF на ArXiv"""
        title = article.get('title', '').lower()
        
        # Простая эвристика для определения ArXiv статей
        if 'arxiv' in title or any(word in title for word in ['preprint', 'submitted']):
            # Здесь можно добавить поиск по ArXiv API
            pass
        
        return None
    
    def _get_biorxiv_pdf_url(self, article: Dict) -> Optional[str]:
        """Поиск PDF на BioRxiv"""
        title = article.get('title', '').lower()
        journal = article.get('journal', '').lower()
        
        if 'biorxiv' in journal or 'biorxiv' in title:
            # Здесь можно добавить поиск по BioRxiv API
            pass
        
        return None
    
    def _download_pdf_from_url(self, url: str, file_path: Path) -> bool:
        """
        Загрузка PDF файла по URL
        
        Args:
            url: URL PDF файла
            file_path: Путь для сохранения
            
        Returns:
            True если успешно скачан
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            # Проверяем, что это действительно PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and not url.endswith('.pdf'):
                return False
            
            # Проверяем размер файла (не слишком маленький и не слишком большой)
            content_length = response.headers.get('content-length')
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                if size_mb < 0.1 or size_mb > 50:  # От 100KB до 50MB
                    return False
            
            # Сохраняем файл
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Проверяем, что файл действительно сохранился
            if file_path.exists() and file_path.stat().st_size > 1000:  # Минимум 1KB
                return True
            else:
                file_path.unlink(missing_ok=True)  # Удаляем битый файл
                return False
        
        except Exception as e:
            # Удаляем частично загруженный файл
            file_path.unlink(missing_ok=True)
            return False
    
    def _print_session_progress(self):
        """Вывод прогресса сессии"""
        stats = self.session_stats
        success_rate = (stats['pdfs_downloaded'] / max(stats['pdfs_attempted'], 1)) * 100
        
        print(f"\n📊 Промежуточная статистика:")
        print(f"   Обработано запросов: {stats['queries_processed']}")
        print(f"   Найдено статей: {stats['articles_found']}")
        print(f"   PDF загружено: {stats['pdfs_downloaded']}/{stats['pdfs_attempted']} ({success_rate:.1f}%)")
        print(f"   Ошибок: {stats['errors']}")
    
    def _get_final_stats(self, session_time, processed_queries: int) -> Dict:
        """Получение финальной статистики сессии"""
        coordinator_stats = self.coordinator.get_session_stats()
        
        return {
            'session_time': str(session_time),
            'queries_processed': processed_queries,
            'articles_found': self.session_stats['articles_found'],
            'pdfs_downloaded': self.session_stats['pdfs_downloaded'],
            'pdf_success_rate': (self.session_stats['pdfs_downloaded'] / 
                               max(self.session_stats['pdfs_attempted'], 1)) * 100,
            'errors': self.session_stats['errors'],
            'coordinator_stats': coordinator_stats,
            'avg_articles_per_query': self.session_stats['articles_found'] / max(processed_queries, 1)
        }
    
    def get_downloaded_pdfs_info(self) -> List[Dict]:
        """Получение информации о скачанных PDF файлах"""
        pdf_info = []
        
        for theme_dir in self.pdf_dir.iterdir():
            if theme_dir.is_dir():
                for pdf_file in theme_dir.glob("*.pdf"):
                    try:
                        stat = pdf_file.stat()
                        pdf_info.append({
                            'theme': theme_dir.name,
                            'filename': pdf_file.name,
                            'size_mb': round(stat.st_size / (1024 * 1024), 2),
                            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            'path': str(pdf_file)
                        })
                    except Exception:
                        continue
        
        return sorted(pdf_info, key=lambda x: x['created'], reverse=True)
    
    def cleanup_failed_downloads(self):
        """Очистка неудачных/битых загрузок"""
        cleaned = 0
        
        for theme_dir in self.pdf_dir.iterdir():
            if theme_dir.is_dir():
                for pdf_file in theme_dir.glob("*.pdf"):
                    try:
                        # Удаляем слишком маленькие файлы (вероятно битые)
                        if pdf_file.stat().st_size < 1000:  # Меньше 1KB
                            pdf_file.unlink()
                            cleaned += 1
                    except Exception:
                        continue
        
        if cleaned > 0:
            print(f"🧹 Очищено {cleaned} битых PDF файлов")
        
        return cleaned


if __name__ == "__main__":
    # Демонстрация работы парсера-агента
    from agent_coordinator import AgentCoordinator
    
    print("🤖 ДЕМОНСТРАЦИЯ ПАРСЕРА-АГЕНТА")
    print("=" * 50)
    
    # Создаем координатора и парсера
    coordinator = AgentCoordinator()
    parser = AgentParser(coordinator, email="your_email@example.com")
    
    # Запускаем короткую демо-сессию
    stats = parser.run_autonomous_session(max_queries=3, download_pdfs=True)
    
    print("\n📋 Информация о скачанных PDF:")
    pdf_info = parser.get_downloaded_pdfs_info()
    for info in pdf_info[:5]:  # Показываем первые 5
        print(f"  - {info['filename']} ({info['size_mb']} MB) - {info['theme']}")
    
    # Закрываем сессию координатора
    coordinator.close_session() 
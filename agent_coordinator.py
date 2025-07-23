#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Координатор мультиагентной системы для сбора информации о продлении жизни
Отвечает за генерацию поисковых запросов, отслеживание результатов и избежание дублирования
"""

import json
import sqlite3
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
import hashlib


class AgentCoordinator:
    """Координатор мультиагентной системы парсинга PubMed по теме продления жизни"""
    
    def __init__(self, db_path: str = "longevity_research.db", config_path: str = "longevity_config.json"):
        """
        Инициализация координатора
        
        Args:
            db_path: Путь к базе данных SQLite
            config_path: Путь к конфигурационному файлу
        """
        self.db_path = db_path
        self.config_path = config_path
        self.config = self._load_config()
        self._init_database()
        
        # Состояние системы
        self.current_session_id = self._create_session()
        self.processed_queries = set()
        self.failed_queries = set()
        
        # Статистика
        self.total_articles_found = 0
        self.total_pdfs_downloaded = 0
        self.session_start_time = datetime.now()
    
    def _load_config(self) -> Dict:
        """Загрузка конфигурации исследования"""
        default_config = {
            "research_themes": [
                "longevity_genetics",
                "aging_interventions", 
                "life_extension_drugs",
                "cellular_senescence",
                "telomeres_aging",
                "caloric_restriction",
                "anti_aging_compounds",
                "regenerative_medicine",
                "biomarkers_aging",
                "aging_mechanisms"
            ],
            "query_templates": {
                "longevity_genetics": [
                    "longevity genes human",
                    "genetic factors life extension",
                    "FOXO3 longevity genetics",
                    "APOE longevity variants",
                    "centenarian genetics study"
                ],
                "aging_interventions": [
                    "life extension interventions",
                    "anti-aging therapies clinical",
                    "longevity interventions human",
                    "aging reversal therapies",
                    "lifespan extension methods"
                ],
                "life_extension_drugs": [
                    "metformin anti-aging effects",
                    "rapamycin longevity studies",
                    "resveratrol life extension",
                    "NAD+ precursors aging",
                    "senolytics aging drugs"
                ],
                "cellular_senescence": [
                    "cellular senescence aging",
                    "senescent cells clearing",
                    "p16 senescence biomarker",
                    "SASP aging inflammation",
                    "senolytic drugs research"
                ],
                "telomeres_aging": [
                    "telomeres aging longevity",
                    "telomerase activation therapy",
                    "telomere length aging",
                    "TA-65 telomerase activator",
                    "telomere shortening interventions"
                ],
                "caloric_restriction": [
                    "caloric restriction longevity",
                    "intermittent fasting aging",
                    "CR mimetics anti-aging",
                    "dietary restriction lifespan",
                    "fasting longevity effects"
                ],
                "anti_aging_compounds": [
                    "spermidine anti-aging effects",
                    "quercetin aging intervention",
                    "curcumin longevity studies",
                    "NMN aging supplement",
                    "astragalus anti-aging"
                ],
                "regenerative_medicine": [
                    "stem cells aging therapy",
                    "tissue regeneration aging",
                    "pluripotent stem cells longevity",
                    "regenerative medicine aging",
                    "cell therapy anti-aging"
                ],
                "biomarkers_aging": [
                    "biological age biomarkers",
                    "aging clock epigenetic",
                    "inflammaging biomarkers",
                    "longevity biomarkers human",
                    "aging assessment tests"
                ],
                "aging_mechanisms": [
                    "hallmarks of aging",
                    "mitochondrial aging theory",
                    "oxidative stress aging",
                    "protein aggregation aging",
                    "DNA damage aging mechanisms"
                ]
            },
            "search_settings": {
                "max_results_per_query": 50,
                "date_range_years": 5,
                "min_articles_per_theme": 20,
                "max_queries_per_session": 100
            },
            "priorities": {
                "recent_research": 0.4,
                "clinical_trials": 0.3,
                "review_articles": 0.2,
                "basic_research": 0.1
            }
        }
        
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Объединяем с дефолтной конфигурацией
                    default_config.update(loaded_config)
            else:
                # Создаем конфигурационный файл с дефолтными настройками
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Ошибка загрузки конфигурации: {e}. Используем дефолтные настройки.")
        
        return default_config
    
    def _init_database(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица сессий
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    total_queries INTEGER DEFAULT 0,
                    total_articles INTEGER DEFAULT 0,
                    total_pdfs INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            # Таблица выполненных запросов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    query_hash TEXT UNIQUE,
                    query_text TEXT NOT NULL,
                    theme TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    articles_found INTEGER DEFAULT 0,
                    pdfs_downloaded INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            ''')
            
            # Таблица найденных статей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id INTEGER,
                    pmid TEXT UNIQUE,
                    title TEXT,
                    authors TEXT,
                    journal TEXT,
                    publication_date TEXT,
                    doi TEXT,
                    abstract TEXT,
                    keywords TEXT,
                    pdf_url TEXT,
                    pdf_downloaded INTEGER DEFAULT 0,
                    pdf_path TEXT,
                    relevance_score REAL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (query_id) REFERENCES queries (id)
                )
            ''')
            
            # Таблица тем исследований и их прогресса
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS theme_progress (
                    theme TEXT PRIMARY KEY,
                    total_queries INTEGER DEFAULT 0,
                    total_articles INTEGER DEFAULT 0,
                    last_updated TEXT,
                    completion_status TEXT DEFAULT 'active'
                )
            ''')
            
            conn.commit()
    
    def _create_session(self) -> int:
        """Создание новой сессии"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (start_time) VALUES (?)",
                (datetime.now().isoformat(),)
            )
            session_id = cursor.lastrowid
            conn.commit()
        
        print(f"🚀 Создана новая сессия: {session_id}")
        return session_id
    
    def _generate_query_hash(self, query: str, theme: str) -> str:
        """Генерация хеша для запроса для избежания дублирования"""
        content = f"{query.lower().strip()}_{theme}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_next_queries(self, count: int = 5) -> List[Dict]:
        """
        Получение следующих запросов для выполнения
        
        Args:
            count: Количество запросов для генерации
            
        Returns:
            Список словарей с информацией о запросах
        """
        queries = []
        themes_progress = self._get_themes_progress()
        
        # Определяем приоритетные темы (с наименьшим количеством статей)
        priority_themes = sorted(
            themes_progress.keys(),
            key=lambda t: themes_progress[t]['total_articles']
        )
        
        for theme in priority_themes:
            if len(queries) >= count:
                break
                
            # Проверяем, не достигли ли лимит для темы
            if themes_progress[theme]['total_articles'] >= self.config["search_settings"]["min_articles_per_theme"]:
                continue
            
            # Генерируем запросы для темы
            theme_queries = self._generate_queries_for_theme(theme, count - len(queries))
            queries.extend(theme_queries)
        
        # Если нужно больше запросов, добавляем из любых тем
        if len(queries) < count:
            for theme in random.sample(priority_themes, min(len(priority_themes), 3)):
                if len(queries) >= count:
                    break
                additional_queries = self._generate_queries_for_theme(theme, count - len(queries))
                queries.extend(additional_queries)
        
        # Записываем запросы в базу данных
        for query_info in queries:
            self._save_query_to_db(query_info)
        
        return queries[:count]
    
    def _get_themes_progress(self) -> Dict:
        """Получение прогресса по темам"""
        progress = {}
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT theme, total_articles FROM theme_progress")
            results = cursor.fetchall()
        
        # Инициализируем все темы
        for theme in self.config["research_themes"]:
            progress[theme] = {'total_articles': 0, 'total_queries': 0}
        
        # Обновляем данными из БД
        for theme, articles in results:
            if theme in progress:
                progress[theme]['total_articles'] = articles
        
        return progress
    
    def _generate_queries_for_theme(self, theme: str, max_count: int) -> List[Dict]:
        """Генерация запросов для конкретной темы"""
        queries = []
        
        if theme not in self.config["query_templates"]:
            return queries
        
        base_queries = self.config["query_templates"][theme]
        date_range = self._get_date_range()
        
        for base_query in base_queries:
            if len(queries) >= max_count:
                break
            
            # Создаем различные вариации запроса
            variations = self._create_query_variations(base_query, theme)
            
            for variation in variations:
                if len(queries) >= max_count:
                    break
                
                query_hash = self._generate_query_hash(variation, theme)
                
                # Проверяем, не выполняли ли уже этот запрос
                if not self._is_query_processed(query_hash):
                    query_info = {
                        'query': variation,
                        'theme': theme,
                        'hash': query_hash,
                        'date_from': date_range['from'],
                        'date_to': date_range['to'],
                        'max_results': self.config["search_settings"]["max_results_per_query"],
                        'priority': self._calculate_query_priority(variation, theme)
                    }
                    queries.append(query_info)
        
        return queries
    
    def _create_query_variations(self, base_query: str, theme: str) -> List[str]:
        """Создание вариаций базового запроса"""
        variations = [base_query]
        
        # Добавляем модификаторы для более специфического поиска
        modifiers = {
            'clinical': [' clinical trial', ' human study', ' clinical research'],
            'recent': [' 2020:2024[PDAT]', ' recent studies'],
            'review': [' systematic review', ' meta-analysis', ' review'],
            'mechanism': [' mechanism', ' pathway', ' molecular'],
            'intervention': [' intervention', ' treatment', ' therapy']
        }
        
        # Добавляем по одной вариации с модификатором
        for mod_type, mod_list in modifiers.items():
            if len(variations) >= 3:  # Ограничиваем количество вариаций
                break
            modifier = random.choice(mod_list)
            if modifier not in base_query.lower():
                variations.append(base_query + modifier)
        
        return variations
    
    def _get_date_range(self) -> Dict[str, str]:
        """Получение диапазона дат для поиска"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * self.config["search_settings"]["date_range_years"])
        
        return {
            'from': start_date.strftime("%Y/%m/%d"),
            'to': end_date.strftime("%Y/%m/%d")
        }
    
    def _calculate_query_priority(self, query: str, theme: str) -> float:
        """Расчет приоритета запроса"""
        priority = 0.5  # Базовый приоритет
        
        # Повышаем приоритет для клинических исследований
        if any(term in query.lower() for term in ['clinical', 'trial', 'human']):
            priority += self.config["priorities"]["clinical_trials"]
        
        # Повышаем приоритет для недавних исследований  
        if any(term in query.lower() for term in ['recent', '2020', '2021', '2022', '2023', '2024']):
            priority += self.config["priorities"]["recent_research"]
        
        # Повышаем приоритет для обзорных статей
        if any(term in query.lower() for term in ['review', 'meta-analysis']):
            priority += self.config["priorities"]["review_articles"]
        
        return min(priority, 1.0)
    
    def _is_query_processed(self, query_hash: str) -> bool:
        """Проверка, выполнялся ли уже запрос"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM queries WHERE query_hash = ?", (query_hash,))
            return cursor.fetchone()[0] > 0
    
    def _save_query_to_db(self, query_info: Dict):
        """Сохранение запроса в базу данных"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO queries 
                (session_id, query_hash, query_text, theme, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                self.current_session_id,
                query_info['hash'],
                query_info['query'],
                query_info['theme'],
                datetime.now().isoformat()
            ))
            conn.commit()
    
    def report_query_results(self, query_hash: str, articles: List[Dict], 
                           pdfs_downloaded: int = 0, error: str = None):
        """
        Отчет о результатах выполнения запроса
        
        Args:
            query_hash: Хеш запроса
            articles: Список найденных статей
            pdfs_downloaded: Количество скачанных PDF
            error: Сообщение об ошибке (если есть)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Обновляем статус запроса
            status = 'error' if error else 'completed'
            cursor.execute('''
                UPDATE queries 
                SET articles_found = ?, pdfs_downloaded = ?, status = ?, error_message = ?
                WHERE query_hash = ?
            ''', (len(articles), pdfs_downloaded, status, error, query_hash))
            
            # Получаем ID запроса
            cursor.execute("SELECT id, theme FROM queries WHERE query_hash = ?", (query_hash,))
            result = cursor.fetchone()
            if not result:
                return
            
            query_id, theme = result
            
            # Сохраняем статьи
            for article in articles:
                self._save_article_to_db(cursor, query_id, article)
            
            # Обновляем прогресс темы
            self._update_theme_progress(cursor, theme, len(articles))
            
            conn.commit()
        
        # Обновляем статистику сессии
        self.total_articles_found += len(articles)
        self.total_pdfs_downloaded += pdfs_downloaded
        
        print(f"✅ Запрос {query_hash[:8]}... завершен: {len(articles)} статей, {pdfs_downloaded} PDF")
    
    def _save_article_to_db(self, cursor, query_id: int, article: Dict):
        """Сохранение статьи в базу данных"""
        cursor.execute('''
            INSERT OR IGNORE INTO articles 
            (query_id, pmid, title, authors, journal, publication_date, 
             doi, abstract, keywords, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            query_id,
            article.get('pmid', ''),
            article.get('title', ''),
            json.dumps(article.get('authors', []), ensure_ascii=False),
            article.get('journal', ''),
            article.get('publication_date', ''),
            article.get('doi', ''),
            article.get('abstract', ''),
            json.dumps(article.get('keywords', []), ensure_ascii=False),
            datetime.now().isoformat()
        ))
    
    def _update_theme_progress(self, cursor, theme: str, new_articles: int):
        """Обновление прогресса темы"""
        cursor.execute('''
            INSERT OR REPLACE INTO theme_progress 
            (theme, total_articles, last_updated)
            VALUES (
                ?, 
                COALESCE((SELECT total_articles FROM theme_progress WHERE theme = ?), 0) + ?,
                ?
            )
        ''', (theme, theme, new_articles, datetime.now().isoformat()))
    
    def get_session_stats(self) -> Dict:
        """Получение статистики текущей сессии"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Статистика запросов
            cursor.execute('''
                SELECT COUNT(*), 
                       SUM(articles_found), 
                       SUM(pdfs_downloaded),
                       COUNT(CASE WHEN status = 'completed' THEN 1 END),
                       COUNT(CASE WHEN status = 'error' THEN 1 END)
                FROM queries WHERE session_id = ?
            ''', (self.current_session_id,))
            
            query_stats = cursor.fetchone()
            
            # Статистика по темам
            cursor.execute('''
                SELECT theme, COUNT(*), SUM(articles_found) 
                FROM queries WHERE session_id = ? 
                GROUP BY theme
            ''', (self.current_session_id,))
            
            theme_stats = cursor.fetchall()
        
        runtime = datetime.now() - self.session_start_time
        
        return {
            'session_id': self.current_session_id,
            'runtime': str(runtime),
            'total_queries': query_stats[0] or 0,
            'total_articles': query_stats[1] or 0,
            'total_pdfs': query_stats[2] or 0,
            'completed_queries': query_stats[3] or 0,
            'failed_queries': query_stats[4] or 0,
            'themes': {theme: {'queries': queries, 'articles': articles or 0} 
                      for theme, queries, articles in theme_stats}
        }
    
    def get_research_recommendations(self) -> List[Dict]:
        """Получение рекомендаций для дальнейшего исследования"""
        recommendations = []
        themes_progress = self._get_themes_progress()
        
        # Находим недоисследованные темы
        for theme, progress in themes_progress.items():
            if progress['total_articles'] < self.config["search_settings"]["min_articles_per_theme"]:
                recommendations.append({
                    'type': 'underresearched_theme',
                    'theme': theme,
                    'current_articles': progress['total_articles'],
                    'target_articles': self.config["search_settings"]["min_articles_per_theme"],
                    'priority': 'high'
                })
        
        # Анализируем успешные запросы для рекомендаций
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT theme, AVG(articles_found) as avg_articles
                FROM queries 
                WHERE status = 'completed' AND articles_found > 0
                GROUP BY theme
                ORDER BY avg_articles DESC
            ''')
            
            productive_themes = cursor.fetchall()
        
        for theme, avg_articles in productive_themes[:3]:
            recommendations.append({
                'type': 'expand_productive_theme',
                'theme': theme,
                'avg_articles_per_query': round(avg_articles, 1),
                'priority': 'medium'
            })
        
        return recommendations
    
    def close_session(self):
        """Закрытие текущей сессии"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE sessions 
                SET end_time = ?, total_queries = ?, total_articles = ?, total_pdfs = ?, status = ?
                WHERE id = ?
            ''', (
                datetime.now().isoformat(),
                self.get_session_stats()['total_queries'],
                self.total_articles_found,
                self.total_pdfs_downloaded,
                'completed',
                self.current_session_id
            ))
            conn.commit()
        
        print(f"🏁 Сессия {self.current_session_id} завершена")


if __name__ == "__main__":
    # Пример использования координатора
    coordinator = AgentCoordinator()
    
    print("🧠 ДЕМОНСТРАЦИЯ КООРДИНАТОРА МУЛЬТИАГЕНТНОЙ СИСТЕМЫ")
    print("=" * 60)
    
    # Получаем следующие запросы
    queries = coordinator.get_next_queries(3)
    
    print(f"\n📋 Сгенерировано {len(queries)} запросов:")
    for i, query in enumerate(queries, 1):
        print(f"{i}. Тема: {query['theme']}")
        print(f"   Запрос: {query['query']}")
        print(f"   Приоритет: {query['priority']:.2f}")
        print()
    
    # Показываем статистику
    stats = coordinator.get_session_stats()
    print("📊 Статистика сессии:")
    print(f"   Всего запросов: {stats['total_queries']}")
    print(f"   Время работы: {stats['runtime']}")
    
    # Получаем рекомендации
    recommendations = coordinator.get_research_recommendations()
    print(f"\n💡 Рекомендации ({len(recommendations)}):")
    for rec in recommendations[:3]:
        print(f"   - {rec['type']}: {rec['theme']} (приоритет: {rec['priority']})")
    
    coordinator.close_session() 
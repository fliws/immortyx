#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Расширение координатора для обхода связанных статей и авторов
Дополняет agent_coordinator.py функционалом п.9 из требований
"""

from agent_coordinator import AgentCoordinator
from typing import List, Dict, Set
import sqlite3
import json


class EnhancedAgentCoordinator(AgentCoordinator):
    """Расширенный координатор с логикой обхода связанных исследований"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Дополнительные настройки для связанных исследований
        self.related_search_config = {
            "max_related_queries_per_article": 2,
            "min_citation_threshold": 5,
            "author_follow_limit": 3,
            "journal_follow_enabled": True,
            "related_terms_expansion": True
        }
    
    def generate_related_queries_from_articles(self, limit: int = 10) -> List[Dict]:
        """
        Генерация запросов на основе уже найденных статей
        Реализует п.9: логика обхода связанных статей или авторов
        """
        related_queries = []
        
        # Получаем топ статьи для анализа связей
        top_articles = self._get_top_articles_for_expansion()
        
        for article in top_articles[:limit]:
            # 1. Запросы по авторам
            author_queries = self._generate_author_based_queries(article)
            related_queries.extend(author_queries)
            
            # 2. Запросы по ключевым словам
            keyword_queries = self._generate_keyword_based_queries(article)
            related_queries.extend(keyword_queries)
            
            # 3. Запросы по журналу
            if self.related_search_config["journal_follow_enabled"]:
                journal_queries = self._generate_journal_based_queries(article)
                related_queries.extend(journal_queries)
        
        # Фильтруем уже выполненные запросы
        new_queries = []
        for query_info in related_queries:
            if not self._is_query_processed(query_info['hash']):
                new_queries.append(query_info)
                self._save_query_to_db(query_info)
        
        return new_queries[:limit]
    
    def _get_top_articles_for_expansion(self) -> List[Dict]:
        """Получение топ статей для расширения поиска"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Статьи с наибольшим количеством ключевых слов (предположительно более релевантные)
            cursor.execute('''
                SELECT pmid, title, authors, keywords, journal, doi
                FROM articles 
                WHERE keywords IS NOT NULL AND keywords != '[]'
                ORDER BY LENGTH(keywords) DESC
                LIMIT 20
            ''')
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'pmid': row[0],
                    'title': row[1],
                    'authors': json.loads(row[2]) if row[2] else [],
                    'keywords': json.loads(row[3]) if row[3] else [],
                    'journal': row[4],
                    'doi': row[5]
                })
            
            return articles
    
    def _generate_author_based_queries(self, article: Dict) -> List[Dict]:
        """Генерация запросов по авторам статьи"""
        queries = []
        authors = article.get('authors', [])
        
        # Берем первых N авторов (обычно более значимые)
        top_authors = authors[:self.related_search_config["author_follow_limit"]]
        
        for author in top_authors:
            if len(author.split()) >= 2:  # Имя и фамилия
                # Формируем запрос по автору + тема долголетия
                for theme in ['longevity', 'aging', 'anti-aging']:
                    query_text = f'"{author}"[Author] AND {theme}'
                    
                    query_info = {
                        'query': query_text,
                        'theme': 'related_authors',
                        'hash': self._generate_query_hash(query_text, 'related_authors'),
                        'date_from': self._get_date_range()['from'],
                        'date_to': self._get_date_range()['to'],
                        'max_results': 20,
                        'priority': 0.7,
                        'source_article': article['pmid'],
                        'expansion_type': 'author_follow'
                    }
                    queries.append(query_info)
        
        return queries
    
    def _generate_keyword_based_queries(self, article: Dict) -> List[Dict]:
        """Генерация запросов по ключевым словам статьи"""
        queries = []
        keywords = article.get('keywords', [])
        
        # Фильтруем и комбинируем ключевые слова
        relevant_keywords = [kw for kw in keywords 
                           if len(kw.split()) <= 3 and any(term in kw.lower() 
                           for term in ['aging', 'longevity', 'senescence', 'telomere', 'caloric'])]
        
        for keyword in relevant_keywords[:5]:  # Ограничиваем количество
            # Расширяем поиск по ключевому слову
            expanded_queries = self._expand_keyword_search(keyword)
            queries.extend(expanded_queries)
        
        return queries
    
    def _generate_journal_based_queries(self, article: Dict) -> List[Dict]:
        """Генерация запросов по журналу статьи"""
        queries = []
        journal = article.get('journal', '')
        
        if journal and len(journal) > 5:  # Не пустой журнал
            # Поиск других статей в том же журнале по нашим темам
            for theme_key in self.config["research_themes"][:3]:  # Топ 3 темы
                base_queries = self.config["query_templates"].get(theme_key, [])
                
                for base_query in base_queries[:2]:  # По 2 запроса на тему
                    query_text = f'{base_query} AND "{journal}"[Journal]'
                    
                    query_info = {
                        'query': query_text,
                        'theme': f'{theme_key}_journal_follow',
                        'hash': self._generate_query_hash(query_text, f'{theme_key}_journal_follow'),
                        'date_from': self._get_date_range()['from'],
                        'date_to': self._get_date_range()['to'],
                        'max_results': 15,
                        'priority': 0.6,
                        'source_article': article['pmid'],
                        'expansion_type': 'journal_follow'
                    }
                    queries.append(query_info)
        
        return queries
    
    def _expand_keyword_search(self, keyword: str) -> List[Dict]:
        """Расширение поиска по ключевому слову с синонимами"""
        queries = []
        
        # Словарь синонимов для расширения
        expansion_dict = {
            'aging': ['ageing', 'senescence', 'age-related'],
            'longevity': ['lifespan', 'life extension', 'life span'],
            'senescence': ['cellular aging', 'cell senescence'],
            'telomere': ['telomerase', 'telomeric'],
            'caloric restriction': ['CR', 'dietary restriction', 'calorie restriction'],
            'oxidative stress': ['ROS', 'reactive oxygen species', 'free radicals']
        }
        
        # Находим расширения для ключевого слова
        expanded_terms = [keyword]  # Исходный термин
        
        for base_term, synonyms in expansion_dict.items():
            if base_term.lower() in keyword.lower():
                expanded_terms.extend(synonyms)
        
        # Создаем запросы с расширенными терминами
        for term in expanded_terms[:3]:  # Ограничиваем
            query_text = f'"{term}" AND longevity research'
            
            query_info = {
                'query': query_text,
                'theme': 'keyword_expansion',
                'hash': self._generate_query_hash(query_text, 'keyword_expansion'),
                'date_from': self._get_date_range()['from'],
                'date_to': self._get_date_range()['to'],
                'max_results': 25,
                'priority': 0.65,
                'expansion_type': 'keyword_expansion',
                'source_keyword': keyword
            }
            queries.append(query_info)
        
        return queries
    
    def get_next_queries_with_related(self, count: int = 5, include_related: bool = True) -> List[Dict]:
        """
        Расширенный метод получения запросов с учетом связанных исследований
        """
        # Получаем базовые запросы
        base_queries = super().get_next_queries(count // 2 if include_related else count)
        
        if not include_related:
            return base_queries
        
        # Добавляем запросы по связанным исследованиям
        related_queries = self.generate_related_queries_from_articles(count - len(base_queries))
        
        # Объединяем и сортируем по приоритету
        all_queries = base_queries + related_queries
        all_queries.sort(key=lambda q: q.get('priority', 0.5), reverse=True)
        
        return all_queries[:count]
    
    def get_expansion_stats(self) -> Dict:
        """Статистика по расширению поиска"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Статистика по типам расширения
            cursor.execute('''
                SELECT 
                    COUNT(CASE WHEN theme LIKE '%author%' THEN 1 END) as author_queries,
                    COUNT(CASE WHEN theme LIKE '%journal%' THEN 1 END) as journal_queries,
                    COUNT(CASE WHEN theme = 'keyword_expansion' THEN 1 END) as keyword_queries,
                    COUNT(CASE WHEN theme = 'related_authors' THEN 1 END) as related_author_queries
                FROM queries
            ''')
            
            stats = cursor.fetchone()
            
            return {
                'expansion_stats': {
                    'author_follow_queries': stats[0] or 0,
                    'journal_follow_queries': stats[1] or 0,
                    'keyword_expansion_queries': stats[2] or 0,
                    'related_author_queries': stats[3] or 0
                },
                'total_expansion_queries': sum(stats) if stats else 0
            }


# Пример использования расширенного координатора
if __name__ == "__main__":
    print("🔗 ДЕМОНСТРАЦИЯ РАСШИРЕННОГО КООРДИНАТОРА")
    print("=" * 50)
    
    # Создаем расширенный координатор
    coordinator = EnhancedAgentCoordinator()
    
    # Сначала получаем обычные запросы для создания базы статей
    print("1. Получаем базовые запросы:")
    base_queries = coordinator.get_next_queries(3)
    for query in base_queries:
        print(f"   - {query['query']} (тема: {query['theme']})")
    
    # Имитируем добавление статей (в реальности это делает парсер)
    sample_articles = [
        {
            'pmid': '12345',
            'title': 'Caloric restriction and longevity',
            'authors': ['Smith J', 'Johnson A', 'Williams B'],
            'keywords': ['caloric restriction', 'aging', 'longevity', 'lifespan'],
            'journal': 'Nature Aging',
            'doi': '10.1038/s43587-021-00001-1'
        }
    ]
    
    # Добавляем статью в БД для демонстрации
    with sqlite3.connect(coordinator.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO articles 
            (query_id, pmid, title, authors, journal, doi, keywords, timestamp)
            VALUES (1, ?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            sample_articles[0]['pmid'],
            sample_articles[0]['title'], 
            json.dumps(sample_articles[0]['authors']),
            sample_articles[0]['journal'],
            sample_articles[0]['doi'],
            json.dumps(sample_articles[0]['keywords'])
        ))
        conn.commit()
    
    print("\n2. Генерируем запросы по связанным исследованиям:")
    related_queries = coordinator.generate_related_queries_from_articles(5)
    for query in related_queries:
        expansion_type = query.get('expansion_type', 'unknown')
        print(f"   - {query['query']}")
        print(f"     Тип расширения: {expansion_type}")
        print(f"     Приоритет: {query['priority']:.2f}")
    
    print("\n3. Комбинированные запросы (базовые + связанные):")
    combined_queries = coordinator.get_next_queries_with_related(5, include_related=True)
    for i, query in enumerate(combined_queries, 1):
        print(f"   {i}. {query['query'][:60]}...")
        print(f"      Приоритет: {query['priority']:.2f}")
    
    print("\n4. Статистика расширения:")
    expansion_stats = coordinator.get_expansion_stats()
    for stat_type, count in expansion_stats['expansion_stats'].items():
        print(f"   {stat_type}: {count}")
    
    coordinator.close_session() 
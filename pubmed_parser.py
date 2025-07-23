import requests
import xml.etree.ElementTree as ET
import json
import csv
import time
from typing import List, Dict, Optional, Union
from urllib.parse import quote


class PubMedParser:
    """Парсер для работы с базой данных PubMed через официальный API E-utilities"""
    
    def __init__(self, email: str = None, api_key: str = None):
        """
        Инициализация парсера PubMed
        
        Args:
            email: Email для идентификации при работе с API (рекомендуется)
            api_key: API ключ для увеличения лимитов запросов
        """
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.email = email
        self.api_key = api_key
        self.last_request_time = 0
        self.request_delay = 0.34  # Задержка между запросами (рекомендуется NCBI)
        
    def _wait_between_requests(self):
        """Добавляет задержку между запросами для соблюдения лимитов API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        self.last_request_time = time.time()
    
    def _build_params(self, additional_params: Dict = None) -> Dict:
        """Создает базовые параметры для запроса к API"""
        params = {}
        if self.email:
            params['email'] = self.email
        if self.api_key:
            params['api_key'] = self.api_key
        if additional_params:
            params.update(additional_params)
        return params
    
    def search_articles(self, query: str, max_results: int = 100, 
                       date_from: str = None, date_to: str = None) -> List[str]:
        """
        Поиск статей в PubMed по ключевым словам
        
        Args:
            query: Поисковый запрос
            max_results: Максимальное количество результатов
            date_from: Дата начала поиска в формате YYYY/MM/DD
            date_to: Дата окончания поиска в формате YYYY/MM/DD
            
        Returns:
            Список PMID найденных статей
        """
        self._wait_between_requests()
        
        # Формируем поисковый запрос
        search_term = quote(query)
        if date_from or date_to:
            date_range = ""
            if date_from:
                date_range += date_from
            date_range += ":"
            if date_to:
                date_range += date_to
            search_term += f"[PDAT] AND ({date_range}[PDAT])"
        
        params = self._build_params({
            'db': 'pubmed',
            'term': search_term,
            'retmax': str(max_results),
            'retmode': 'xml'
        })
        
        url = self.base_url + "esearch.fcgi"
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Парсим XML ответ
            root = ET.fromstring(response.content)
            pmids = []
            
            for id_element in root.findall('.//Id'):
                pmids.append(id_element.text)
                
            print(f"Найдено {len(pmids)} статей по запросу: {query}")
            return pmids
            
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при поиске: {e}")
            return []
        except ET.ParseError as e:
            print(f"Ошибка парсинга XML: {e}")
            return []
    
    def get_article_details(self, pmids: Union[str, List[str]]) -> List[Dict]:
        """
        Получение детальной информации о статьях по PMID
        
        Args:
            pmids: PMID статьи или список PMID
            
        Returns:
            Список словарей с информацией о статьях
        """
        if isinstance(pmids, str):
            pmids = [pmids]
        
        if not pmids:
            return []
        
        self._wait_between_requests()
        
        # Ограничиваем количество PMID для одного запроса
        pmid_chunks = [pmids[i:i+100] for i in range(0, len(pmids), 100)]
        all_articles = []
        
        for chunk in pmid_chunks:
            params = self._build_params({
                'db': 'pubmed',
                'id': ','.join(chunk),
                'retmode': 'xml',
                'rettype': 'abstract'
            })
            
            url = self.base_url + "efetch.fcgi"
            
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                
                # Парсим XML ответ
                root = ET.fromstring(response.content)
                articles = self._parse_articles_xml(root)
                all_articles.extend(articles)
                
                if len(pmid_chunks) > 1:
                    self._wait_between_requests()
                
            except requests.exceptions.RequestException as e:
                print(f"Ошибка при получении деталей: {e}")
            except ET.ParseError as e:
                print(f"Ошибка парсинга XML: {e}")
        
        print(f"Получена информация о {len(all_articles)} статьях")
        return all_articles
    
    def _parse_articles_xml(self, root: ET.Element) -> List[Dict]:
        """Парсинг XML с информацией о статьях"""
        articles = []
        
        for article_elem in root.findall('.//PubmedArticle'):
            article = {}
            
            # PMID
            pmid_elem = article_elem.find('.//PMID')
            article['pmid'] = pmid_elem.text if pmid_elem is not None else ''
            
            # Заголовок
            title_elem = article_elem.find('.//ArticleTitle')
            article['title'] = title_elem.text if title_elem is not None else ''
            
            # Авторы
            authors = []
            for author_elem in article_elem.findall('.//Author'):
                lastname = author_elem.find('LastName')
                forename = author_elem.find('ForeName')
                if lastname is not None:
                    author_name = lastname.text
                    if forename is not None:
                        author_name = f"{forename.text} {author_name}"
                    authors.append(author_name)
            article['authors'] = authors
            
            # Журнал
            journal_elem = article_elem.find('.//Journal/Title')
            article['journal'] = journal_elem.text if journal_elem is not None else ''
            
            # Дата публикации
            pub_date = article_elem.find('.//PubDate')
            if pub_date is not None:
                year = pub_date.find('Year')
                month = pub_date.find('Month')
                day = pub_date.find('Day')
                
                date_parts = []
                if year is not None:
                    date_parts.append(year.text)
                if month is not None:
                    date_parts.append(month.text)
                if day is not None:
                    date_parts.append(day.text)
                
                article['publication_date'] = '-'.join(date_parts)
            else:
                article['publication_date'] = ''
            
            # Аннотация
            abstract_elem = article_elem.find('.//Abstract/AbstractText')
            article['abstract'] = abstract_elem.text if abstract_elem is not None else ''
            
            # DOI
            doi_elem = None
            for article_id in article_elem.findall('.//ArticleId'):
                if article_id.get('IdType') == 'doi':
                    doi_elem = article_id
                    break
            article['doi'] = doi_elem.text if doi_elem is not None else ''
            
            # Ключевые слова
            keywords = []
            for keyword_elem in article_elem.findall('.//Keyword'):
                if keyword_elem.text:
                    keywords.append(keyword_elem.text)
            article['keywords'] = keywords
            
            # URL PubMed
            article['pubmed_url'] = f"https://pubmed.ncbi.nlm.nih.gov/{article['pmid']}/"
            
            articles.append(article)
        
        return articles
    
    def search_and_fetch(self, query: str, max_results: int = 100,
                        date_from: str = None, date_to: str = None) -> List[Dict]:
        """
        Комбинированный метод: поиск и получение детальной информации
        
        Args:
            query: Поисковый запрос
            max_results: Максимальное количество результатов
            date_from: Дата начала поиска в формате YYYY/MM/DD
            date_to: Дата окончания поиска в формате YYYY/MM/DD
            
        Returns:
            Список словарей с полной информацией о статьях
        """
        print(f"Поиск статей по запросу: {query}")
        pmids = self.search_articles(query, max_results, date_from, date_to)
        
        if not pmids:
            print("Статьи не найдены")
            return []
        
        print("Получение детальной информации...")
        articles = self.get_article_details(pmids)
        
        return articles
    
    def save_to_json(self, articles: List[Dict], filename: str = "pubmed_results.json"):
        """Сохранение результатов в JSON файл"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
            print(f"Результаты сохранены в {filename}")
        except Exception as e:
            print(f"Ошибка при сохранении JSON: {e}")
    
    def save_to_csv(self, articles: List[Dict], filename: str = "pubmed_results.csv"):
        """Сохранение результатов в CSV файл"""
        if not articles:
            print("Нет данных для сохранения")
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'pmid', 'title', 'authors_str', 'journal', 
                    'publication_date', 'abstract', 'doi', 'keywords_str', 'pubmed_url'
                ])
                writer.writeheader()
                
                for article in articles:
                    # Преобразуем списки в строки для CSV
                    csv_article = article.copy()
                    csv_article['authors_str'] = '; '.join(article.get('authors', []))
                    csv_article['keywords_str'] = '; '.join(article.get('keywords', []))
                    
                    # Удаляем оригинальные списки
                    csv_article.pop('authors', None)
                    csv_article.pop('keywords', None)
                    
                    writer.writerow(csv_article)
            
            print(f"Результаты сохранены в {filename}")
        except Exception as e:
            print(f"Ошибка при сохранении CSV: {e}")


def main():
    """Пример использования парсера"""
    # Создаем экземпляр парсера
    parser = PubMedParser(email="your_email@example.com")  # Рекомендуется указать email
    
    # Поиск статей
    query = "COVID-19"  # Простой популярный запрос для демонстрации
    articles = parser.search_and_fetch(query, max_results=5)
    
    if articles:
        # Выводим информацию о первой статье
        print("\n" + "="*50)
        print("ПРИМЕР НАЙДЕННОЙ СТАТЬИ:")
        print("="*50)
        first_article = articles[0]
        print(f"Заголовок: {first_article['title']}")
        print(f"Авторы: {', '.join(first_article['authors'])}")
        print(f"Журнал: {first_article['journal']}")
        print(f"Дата: {first_article['publication_date']}")
        print(f"DOI: {first_article['doi']}")
        print(f"URL: {first_article['pubmed_url']}")
        print(f"Аннотация: {first_article['abstract'][:200]}...")
        
        # Сохраняем результаты
        parser.save_to_json(articles)
        parser.save_to_csv(articles)
    
    
    print(f"\nПарсинг завершен. Найдено {len(articles)} статей.")


if __name__ == "__main__":
    main() 
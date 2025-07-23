#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Примеры использования парсера PubMed
"""

from pubmed_parser import PubMedParser
import time


def example_basic_search():
    """Базовый пример поиска статей"""
    print("\n🔍 БАЗОВЫЙ ПОИСК СТАТЕЙ")
    print("=" * 50)
    
    # Создаем парсер (желательно указать свой email)
    parser = PubMedParser(email="your_email@example.com")
    
    # Поиск статей о COVID-19
    query = "COVID-19 vaccine effectiveness"
    articles = parser.search_and_fetch(query, max_results=5)
    
    # Выводим результаты
    for i, article in enumerate(articles, 1):
        print(f"\n{i}. {article['title']}")
        print(f"   Авторы: {', '.join(article['authors'][:3])}{'...' if len(article['authors']) > 3 else ''}")
        print(f"   Журнал: {article['journal']}")
        print(f"   Дата: {article['publication_date']}")
        print(f"   PMID: {article['pmid']}")
    
    return articles


def example_date_filter():
    """Пример поиска с фильтром по дате"""
    print("\n📅 ПОИСК С ФИЛЬТРОМ ПО ДАТЕ")
    print("=" * 50)
    
    parser = PubMedParser(email="your_email@example.com")
    
    # Поиск статей за последний год
    query = "artificial intelligence diagnosis"
    articles = parser.search_and_fetch(
        query=query,
        max_results=3,
        date_from="2023/01/01",
        date_to="2024/12/31"
    )
    
    print(f"Найдено {len(articles)} статей за 2023-2024 годы")
    for article in articles:
        print(f"- {article['title']} ({article['publication_date']})")
    
    return articles


def example_specific_pmids():
    """Пример получения информации по конкретным PMID"""
    print("\n🎯 ПОЛУЧЕНИЕ СТАТЕЙ ПО PMID")
    print("=" * 50)
    
    parser = PubMedParser(email="your_email@example.com")
    
    # Известные PMID статей
    pmids = ["38704809", "38704550", "38704392"]
    
    articles = parser.get_article_details(pmids)
    
    for article in articles:
        print(f"\nPMID: {article['pmid']}")
        print(f"Заголовок: {article['title']}")
        print(f"DOI: {article['doi']}")
        print(f"Ключевые слова: {', '.join(article['keywords'][:5])}")
    
    return articles


def example_save_results():
    """Пример сохранения результатов в разных форматах"""
    print("\n💾 СОХРАНЕНИЕ РЕЗУЛЬТАТОВ")
    print("=" * 50)
    
    parser = PubMedParser(email="your_email@example.com")
    
    # Поиск статей
    query = "machine learning medical imaging"
    articles = parser.search_and_fetch(query, max_results=5)
    
    if articles:
        # Сохраняем в JSON
        parser.save_to_json(articles, "ml_medical_imaging.json")
        
        # Сохраняем в CSV
        parser.save_to_csv(articles, "ml_medical_imaging.csv")
        
        print(f"Сохранено {len(articles)} статей в JSON и CSV форматах")
    
    return articles


def example_custom_search():
    """Пример продвинутого поиска с кастомными параметрами"""
    print("\n🔬 ПРОДВИНУТЫЙ ПОИСК")
    print("=" * 50)
    
    parser = PubMedParser(email="your_email@example.com")
    
    # Сложный поисковый запрос
    queries = [
        "deep learning AND medical imaging AND cancer detection",
        "CRISPR gene therapy clinical trial",
        "telemedicine rural healthcare access"
    ]
    
    all_results = {}
    
    for query in queries:
        print(f"\nПоиск: {query}")
        articles = parser.search_and_fetch(query, max_results=3)
        all_results[query] = articles
        
        print(f"Найдено {len(articles)} статей")
        if articles:
            print(f"Пример: {articles[0]['title'][:80]}...")
    
    return all_results


def example_analysis():
    """Пример анализа найденных статей"""
    print("\n📊 АНАЛИЗ СТАТЕЙ")
    print("=" * 50)
    
    parser = PubMedParser(email="your_email@example.com")
    
    # Поиск статей
    query = "cancer immunotherapy"
    articles = parser.search_and_fetch(query, max_results=20)
    
    if not articles:
        print("Статьи не найдены")
        return
    
    # Анализ журналов
    journals = {}
    for article in articles:
        journal = article['journal']
        if journal:
            journals[journal] = journals.get(journal, 0) + 1
    
    print("📰 Топ журналов:")
    for journal, count in sorted(journals.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {journal}: {count} статей")
    
    # Анализ годов публикации
    years = {}
    for article in articles:
        pub_date = article['publication_date']
        if pub_date and '-' in pub_date:
            year = pub_date.split('-')[0]
            if year.isdigit():
                years[year] = years.get(year, 0) + 1
    
    print("\n📅 Распределение по годам:")
    for year, count in sorted(years.items(), reverse=True)[:5]:
        print(f"  {year}: {count} статей")
    
    # Анализ ключевых слов
    all_keywords = []
    for article in articles:
        all_keywords.extend(article.get('keywords', []))
    
    keyword_freq = {}
    for keyword in all_keywords:
        keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
    
    print("\n🔑 Популярные ключевые слова:")
    for keyword, count in sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {keyword}: {count} раз")


def main():
    """Запуск всех примеров"""
    print("🧬 ДЕМОНСТРАЦИЯ ПАРСЕРА PUBMED")
    print("═" * 50)
    
    try:
        # Базовый поиск
        example_basic_search()
        time.sleep(1)  # Пауза между запросами
        
        # Поиск с датами
        example_date_filter()
        time.sleep(1)
        
        # Поиск по PMID
        example_specific_pmids()
        time.sleep(1)
        
        # Сохранение результатов
        example_save_results()
        time.sleep(1)
        
        # Продвинутый поиск
        example_custom_search()
        time.sleep(1)
        
        # Анализ статей
        example_analysis()
        
        print("\n✅ Все примеры выполнены успешно!")
        
    except KeyboardInterrupt:
        print("\n⛔ Выполнение прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")


if __name__ == "__main__":
    main() 
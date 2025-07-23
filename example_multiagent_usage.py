#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Примеры использования мультиагентной системы исследования долголетия
Демонстрирует различные сценарии работы с системой
"""

import time
from pathlib import Path
from longevity_research_system import LongevityResearchSystem


def example_basic_research_session():
    """Базовый пример исследовательской сессии"""
    print("🧬 БАЗОВОЕ ИССЛЕДОВАНИЕ ДОЛГОЛЕТИЯ")
    print("=" * 50)
    
    # Создаем систему
    system = LongevityResearchSystem(
        email="your_email@example.com",  # Укажите свой email
        config_path="example_config.json",
        db_path="example_research.db",
        pdf_dir="example_pdfs"
    )
    
    print("🚀 Запускаем базовую исследовательскую сессию...")
    
    # Запускаем сессию с ограниченным количеством запросов для демонстрации
    stats = system.run_research_session(
        max_queries=5,                    # Небольшое количество для примера
        download_pdfs=True,               # Скачиваем PDF
        target_articles_per_theme=5,      # Цель - 5 статей на тему
        session_name="Demo Session 1"
    )
    
    print(f"\n📊 Результаты сессии:")
    print(f"   Обработано запросов: {stats.get('queries_processed', 0)}")
    print(f"   Найдено статей: {stats.get('articles_found', 0)}")
    print(f"   Скачано PDF: {stats.get('pdfs_downloaded', 0)}")
    
    return stats


def example_focused_research():
    """Пример целенаправленного исследования конкретных тем"""
    print("\n🎯 ЦЕЛЕНАПРАВЛЕННОЕ ИССЛЕДОВАНИЕ")
    print("=" * 40)
    
    # Создаем кастомную конфигурацию для фокусированного исследования
    custom_config = {
        "research_themes": [
            "life_extension_drugs",
            "cellular_senescence", 
            "telomeres_aging"
        ],
        "query_templates": {
            "life_extension_drugs": [
                "metformin longevity clinical trial",
                "rapamycin aging intervention human",
                "resveratrol life extension study",
                "NAD+ precursors aging effects"
            ],
            "cellular_senescence": [
                "senolytic drugs human trials",
                "dasatinib quercetin aging",
                "senescent cells clearance therapy"
            ],
            "telomeres_aging": [
                "telomerase activation longevity",
                "telomere length aging biomarker",
                "TA-65 human studies"
            ]
        },
        "search_settings": {
            "max_results_per_query": 30,
            "date_range_years": 3,
            "min_articles_per_theme": 10,
            "max_queries_per_session": 50
        }
    }
    
    # Сохраняем кастомную конфигурацию
    import json
    with open("focused_config.json", "w", encoding="utf-8") as f:
        json.dump(custom_config, f, indent=2, ensure_ascii=False)
    
    # Создаем систему с кастомной конфигурацией
    system = LongevityResearchSystem(
        config_path="focused_config.json",
        db_path="focused_research.db",
        pdf_dir="focused_pdfs",
        email="your_email@example.com"
    )
    
    print("🔬 Запускаем целенаправленное исследование...")
    
    stats = system.run_research_session(
        max_queries=10,
        download_pdfs=True,
        target_articles_per_theme=10,
        session_name="Focused Research"
    )
    
    return stats


def example_progressive_research():
    """Пример прогрессивного исследования с несколькими сессиями"""
    print("\n⚡ ПРОГРЕССИВНОЕ ИССЛЕДОВАНИЕ")
    print("=" * 35)
    
    system = LongevityResearchSystem(
        email="your_email@example.com",
        config_path="progressive_config.json",
        db_path="progressive_research.db",
        pdf_dir="progressive_pdfs"
    )
    
    # Сессия 1: Разведывательная
    print("🕵️ Сессия 1: Разведывательное исследование")
    stats1 = system.run_research_session(
        max_queries=8,
        download_pdfs=False,  # Не скачиваем PDF на разведывательном этапе
        target_articles_per_theme=3,
        session_name="Reconnaissance"
    )
    
    time.sleep(2)  # Пауза между сессиями
    
    # Получаем рекомендации после первой сессии
    print("\n💡 Анализируем результаты и получаем рекомендации...")
    recommendations = system.coordinator.get_research_recommendations()
    
    print(f"Получено {len(recommendations)} рекомендаций:")
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"  {i}. {rec['type']}: {rec['theme']} (приоритет: {rec['priority']})")
    
    # Сессия 2: Целенаправленная на основе рекомендаций
    print(f"\n🎯 Сессия 2: Целенаправленное исследование на основе рекомендаций")
    stats2 = system.run_research_session(
        max_queries=12,
        download_pdfs=True,  # Теперь скачиваем PDF
        target_articles_per_theme=8,
        session_name="Targeted Research"
    )
    
    # Итоговая статистика
    total_queries = stats1.get('queries_processed', 0) + stats2.get('queries_processed', 0)
    total_articles = stats1.get('articles_found', 0) + stats2.get('articles_found', 0)
    total_pdfs = stats1.get('pdfs_downloaded', 0) + stats2.get('pdfs_downloaded', 0)
    
    print(f"\n🏆 ИТОГОВЫЕ РЕЗУЛЬТАТЫ ПРОГРЕССИВНОГО ИССЛЕДОВАНИЯ:")
    print(f"   Всего запросов: {total_queries}")
    print(f"   Всего статей: {total_articles}")
    print(f"   Всего PDF: {total_pdfs}")
    
    return {"stats1": stats1, "stats2": stats2}


def example_analysis_and_export():
    """Пример анализа результатов и экспорта данных"""
    print("\n📊 АНАЛИЗ И ЭКСПОРТ РЕЗУЛЬТАТОВ")
    print("=" * 35)
    
    system = LongevityResearchSystem(
        email="your_email@example.com",
        config_path="analysis_config.json",
        db_path="analysis_research.db",
        pdf_dir="analysis_pdfs"
    )
    
    # Проводим небольшое исследование
    print("🔬 Проводим исследование для анализа...")
    stats = system.run_research_session(
        max_queries=6,
        download_pdfs=True,
        target_articles_per_theme=4,
        session_name="Analysis Demo"
    )
    
    print("\n📈 Анализируем результаты...")
    
    # Получаем информацию о PDF файлах
    pdf_info = system.parser.get_downloaded_pdfs_info()
    if pdf_info:
        print(f"\n📁 Скачанные PDF файлы ({len(pdf_info)}):")
        
        # Группируем по темам
        themes = {}
        for info in pdf_info:
            theme = info['theme']
            if theme not in themes:
                themes[theme] = []
            themes[theme].append(info)
        
        for theme, files in themes.items():
            print(f"  📂 {theme.replace('_', ' ').title()}: {len(files)} файлов")
            total_size = sum(f['size_mb'] for f in files)
            print(f"     Общий размер: {total_size:.1f} MB")
    
    # Экспорт результатов
    print(f"\n📤 Экспортируем результаты...")
    
    # Имитация экспорта (в реальной системе вызовется интерактивное меню)
    import sqlite3
    import json
    from datetime import datetime
    
    try:
        with sqlite3.connect(system.coordinator.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.pmid, a.title, a.authors, a.journal, a.publication_date,
                       a.doi, a.abstract, q.theme
                FROM articles a
                JOIN queries q ON a.query_id = q.id
                ORDER BY a.timestamp DESC
            ''')
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'pmid': row[0],
                    'title': row[1],
                    'authors': json.loads(row[2]) if row[2] else [],
                    'journal': row[3],
                    'publication_date': row[4],
                    'doi': row[5],
                    'abstract': row[6],
                    'theme': row[7]
                })
        
        # Сохраняем экспорт
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = f"longevity_analysis_{timestamp}.json"
        
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Результаты экспортированы в {export_file}")
        print(f"📊 Экспортировано {len(articles)} статей")
        
        # Краткая аналитика
        if articles:
            themes_count = {}
            journals_count = {}
            
            for article in articles:
                theme = article['theme']
                journal = article['journal']
                
                themes_count[theme] = themes_count.get(theme, 0) + 1
                if journal:
                    journals_count[journal] = journals_count.get(journal, 0) + 1
            
            print(f"\n📈 Краткая аналитика:")
            print(f"   Самая популярная тема: {max(themes_count, key=themes_count.get)} ({max(themes_count.values())} статей)")
            if journals_count:
                print(f"   Топ журнал: {max(journals_count, key=journals_count.get)} ({max(journals_count.values())} статей)")
    
    except Exception as e:
        print(f"❌ Ошибка экспорта: {e}")
    
    return stats


def example_cleanup_and_maintenance():
    """Пример обслуживания системы и очистки"""
    print("\n🧹 ОБСЛУЖИВАНИЕ СИСТЕМЫ")
    print("=" * 30)
    
    system = LongevityResearchSystem(
        email="your_email@example.com",
        config_path="maintenance_config.json", 
        db_path="maintenance_research.db",
        pdf_dir="maintenance_pdfs"
    )
    
    # Проводим небольшое исследование для создания данных
    print("🔬 Создаем данные для демонстрации обслуживания...")
    system.run_research_session(
        max_queries=3,
        download_pdfs=True,
        session_name="Maintenance Demo"
    )
    
    print(f"\n🔍 Проверяем состояние системы...")
    
    # Показываем статистику
    stats = system.coordinator.get_session_stats()
    print(f"📊 Статистика:")
    print(f"   Запросов: {stats['total_queries']}")
    print(f"   Статей: {stats['total_articles']}")
    print(f"   PDF: {stats['total_pdfs']}")
    
    # Очистка битых PDF
    print(f"\n🧹 Очистка битых PDF файлов...")
    cleaned = system.parser.cleanup_failed_downloads()
    
    # Показываем информацию о PDF
    pdf_info = system.parser.get_downloaded_pdfs_info()
    if pdf_info:
        total_size = sum(info['size_mb'] for info in pdf_info)
        print(f"📁 PDF статистика:")
        print(f"   Файлов: {len(pdf_info)}")
        print(f"   Общий размер: {total_size:.1f} MB")
        print(f"   Средний размер: {total_size/len(pdf_info):.1f} MB")
    
    # Рекомендации по дальнейшему исследованию
    recommendations = system.coordinator.get_research_recommendations()
    if recommendations:
        print(f"\n💡 Рекомендации для дальнейшего исследования:")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"   {i}. {rec['type'].replace('_', ' ').title()}")
            print(f"      Тема: {rec['theme'].replace('_', ' ').title()}")
            print(f"      Приоритет: {rec['priority'].upper()}")
    
    return stats


def main():
    """Запуск всех примеров"""
    print("🧬 ДЕМОНСТРАЦИЯ МУЛЬТИАГЕНТНОЙ СИСТЕМЫ ИССЛЕДОВАНИЯ ДОЛГОЛЕТИЯ")
    print("═" * 70)
    print()
    print("Эта демонстрация покажет различные сценарии использования системы:")
    print("1. Базовое исследование")
    print("2. Целенаправленное исследование") 
    print("3. Прогрессивное исследование")
    print("4. Анализ и экспорт")
    print("5. Обслуживание системы")
    print()
    
    try:
        # Пример 1: Базовое исследование
        example_basic_research_session()
        time.sleep(2)
        
        # Пример 2: Целенаправленное исследование
        example_focused_research()
        time.sleep(2)
        
        # Пример 3: Прогрессивное исследование
        example_progressive_research()
        time.sleep(2)
        
        # Пример 4: Анализ и экспорт
        example_analysis_and_export()
        time.sleep(2)
        
        # Пример 5: Обслуживание
        example_cleanup_and_maintenance()
        
        print(f"\n🎉 ВСЕ ПРИМЕРЫ ВЫПОЛНЕНЫ УСПЕШНО!")
        print("=" * 50)
        print("📁 Созданные файлы:")
        
        # Показываем созданные файлы
        created_files = [
            "example_config.json", "example_research.db", "example_pdfs/",
            "focused_config.json", "focused_research.db", "focused_pdfs/",
            "progressive_config.json", "progressive_research.db", "progressive_pdfs/",
            "analysis_config.json", "analysis_research.db", "analysis_pdfs/",
            "maintenance_config.json", "maintenance_research.db", "maintenance_pdfs/"
        ]
        
        for file_path in created_files:
            if Path(file_path).exists():
                if file_path.endswith('/'):
                    pdf_count = len(list(Path(file_path).glob("**/*.pdf")))
                    print(f"   📂 {file_path} ({pdf_count} PDF файлов)")
                else:
                    size = Path(file_path).stat().st_size
                    print(f"   📄 {file_path} ({size} байт)")
        
        print(f"\n💡 Для интерактивного использования запустите:")
        print("   python longevity_research_system.py --interactive")
        
    except KeyboardInterrupt:
        print("\n⛔ Демонстрация прервана пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка демонстрации: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 
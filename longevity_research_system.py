#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главный модуль мультиагентной системы для сбора информации о продлении жизни
Объединяет координатора и парсера в единую управляемую систему
"""

import argparse
import json
import sys
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from agent_coordinator import AgentCoordinator
from agent_parser import AgentParser


class LongevityResearchSystem:
    """Главная система управления мультиагентным парсингом PubMed"""
    
    def __init__(self, config_path: str = "longevity_config.json",
                 db_path: str = "longevity_research.db",
                 pdf_dir: str = "longevity_pdfs",
                 email: str = None,
                 api_key: str = None):
        """
        Инициализация системы
        
        Args:
            config_path: Путь к файлу конфигурации
            db_path: Путь к базе данных
            pdf_dir: Директория для PDF файлов
            email: Email для PubMed API
            api_key: API ключ PubMed
        """
        self.config_path = config_path
        self.db_path = db_path
        self.pdf_dir = pdf_dir
        self.email = email
        self.api_key = api_key
        
        # Инициализируем компоненты системы
        print("🧬 Инициализация мультиагентной системы исследования долголетия...")
        
        self.coordinator = AgentCoordinator(db_path=db_path, config_path=config_path)
        self.parser = AgentParser(
            coordinator=self.coordinator,
            email=email,
            api_key=api_key,
            pdf_dir=pdf_dir
        )
        
        # Обработчик сигналов для graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.running = True
        
        print("✅ Система инициализирована успешно!")
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        print(f"\n🛑 Получен сигнал {signum}. Завершение работы...")
        self.running = False
    
    def run_research_session(self, 
                           max_queries: int = 50,
                           download_pdfs: bool = True,
                           target_articles_per_theme: int = None,
                           session_name: str = None) -> Dict:
        """
        Запуск исследовательской сессии
        
        Args:
            max_queries: Максимальное количество запросов
            download_pdfs: Скачивать ли PDF файлы
            target_articles_per_theme: Целевое количество статей на тему
            session_name: Имя сессии для логирования
            
        Returns:
            Статистика сессии
        """
        if session_name:
            print(f"🎯 Запуск сессии: {session_name}")
        
        # Обновляем настройки если указаны
        if target_articles_per_theme:
            self.coordinator.config["search_settings"]["min_articles_per_theme"] = target_articles_per_theme
        
        print(f"📋 Параметры сессии:")
        print(f"   Максимум запросов: {max_queries}")
        print(f"   Загрузка PDF: {'ВКЛ' if download_pdfs else 'ВЫКЛ'}")
        print(f"   Цель статей на тему: {target_articles_per_theme or 'по умолчанию'}")
        
        # Показываем текущий прогресс по темам
        self._show_themes_progress()
        
        # Запускаем автономную сессию парсера
        try:
            stats = self.parser.run_autonomous_session(
                max_queries=max_queries,
                download_pdfs=download_pdfs
            )
            
            # Показываем итоговую статистику
            self._show_session_summary(stats)
            
            return stats
            
        except Exception as e:
            print(f"❌ Критическая ошибка сессии: {e}")
            return {'error': str(e)}
        
        finally:
            self.coordinator.close_session()
    
    def run_interactive_mode(self):
        """Интерактивный режим управления системой"""
        print("\n🎮 ИНТЕРАКТИВНЫЙ РЕЖИМ УПРАВЛЕНИЯ")
        print("=" * 50)
        print("Доступные команды:")
        print("  1. start - Запуск исследовательской сессии")
        print("  2. status - Показать статус системы")
        print("  3. themes - Показать прогресс по темам")
        print("  4. recommendations - Показать рекомендации")
        print("  5. pdfs - Информация о скачанных PDF")
        print("  6. config - Показать конфигурацию")
        print("  7. export - Экспорт результатов")
        print("  8. cleanup - Очистка битых PDF")
        print("  9. help - Показать справку")
        print("  0. exit - Выход")
        
        while self.running:
            try:
                command = input("\n🤖 Введите команду: ").strip().lower()
                
                if command in ['0', 'exit', 'quit']:
                    break
                elif command in ['1', 'start']:
                    self._interactive_start_session()
                elif command in ['2', 'status']:
                    self._show_system_status()
                elif command in ['3', 'themes']:
                    self._show_themes_progress()
                elif command in ['4', 'recommendations']:
                    self._show_recommendations()
                elif command in ['5', 'pdfs']:
                    self._show_pdfs_info()
                elif command in ['6', 'config']:
                    self._show_config()
                elif command in ['7', 'export']:
                    self._export_results()
                elif command in ['8', 'cleanup']:
                    self._cleanup_pdfs()
                elif command in ['9', 'help']:
                    self._show_help()
                else:
                    print("❓ Неизвестная команда. Введите 'help' для справки.")
                    
            except KeyboardInterrupt:
                print("\n👋 Выход из интерактивного режима")
                break
            except EOFError:
                break
        
        print("🏁 Завершение работы системы...")
        self.coordinator.close_session()
    
    def _interactive_start_session(self):
        """Интерактивный запуск сессии"""
        try:
            max_queries = int(input("Максимум запросов (по умолчанию 20): ") or "20")
            download_pdfs = input("Скачивать PDF? (y/n, по умолчанию y): ").lower() != 'n'
            target_articles = input("Целевое количество статей на тему (по умолчанию 20): ")
            target_articles = int(target_articles) if target_articles else None
            session_name = input("Имя сессии (необязательно): ") or None
            
            self.run_research_session(
                max_queries=max_queries,
                download_pdfs=download_pdfs,
                target_articles_per_theme=target_articles,
                session_name=session_name
            )
        except ValueError:
            print("❌ Некорректное значение. Попробуйте снова.")
        except Exception as e:
            print(f"❌ Ошибка запуска сессии: {e}")
    
    def _show_system_status(self):
        """Показать статус системы"""
        print("\n📊 СТАТУС СИСТЕМЫ")
        print("=" * 30)
        
        stats = self.coordinator.get_session_stats()
        print(f"ID сессии: {stats['session_id']}")
        print(f"Время работы: {stats['runtime']}")
        print(f"Всего запросов: {stats['total_queries']}")
        print(f"Найдено статей: {stats['total_articles']}")
        print(f"Скачано PDF: {stats['total_pdfs']}")
        print(f"Успешных запросов: {stats['completed_queries']}")
        print(f"Неудачных запросов: {stats['failed_queries']}")
        
        # Статистика по темам
        if stats['themes']:
            print("\n📚 По темам:")
            for theme, theme_stats in stats['themes'].items():
                print(f"  {theme}: {theme_stats['queries']} запросов, {theme_stats['articles']} статей")
    
    def _show_themes_progress(self):
        """Показать прогресс по темам исследования"""
        print("\n🔬 ПРОГРЕСС ПО ТЕМАМ ИССЛЕДОВАНИЯ")
        print("=" * 40)
        
        # Получаем прогресс от координатора
        themes_progress = self.coordinator._get_themes_progress()
        target = self.coordinator.config["search_settings"]["min_articles_per_theme"]
        
        for theme, progress in themes_progress.items():
            articles = progress['total_articles']
            completion = min(100, (articles / target) * 100) if target > 0 else 0
            status = "✅" if articles >= target else "🔄"
            
            print(f"{status} {theme.replace('_', ' ').title()}")
            print(f"   Статей: {articles}/{target} ({completion:.1f}% завершено)")
            
            # Прогресс-бар
            bar_length = 20
            filled = int((completion / 100) * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"   [{bar}] {completion:.1f}%")
            print()
    
    def _show_recommendations(self):
        """Показать рекомендации системы"""
        print("\n💡 РЕКОМЕНДАЦИИ СИСТЕМЫ")
        print("=" * 30)
        
        recommendations = self.coordinator.get_research_recommendations()
        
        if not recommendations:
            print("🎉 Все текущие цели достигнуты! Система работает оптимально.")
            return
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec['type'].replace('_', ' ').title()}")
            print(f"   Тема: {rec['theme'].replace('_', ' ').title()}")
            print(f"   Приоритет: {rec['priority'].upper()}")
            
            if rec['type'] == 'underresearched_theme':
                print(f"   Текущее состояние: {rec['current_articles']}/{rec['target_articles']} статей")
            elif rec['type'] == 'expand_productive_theme':
                print(f"   Средняя продуктивность: {rec['avg_articles_per_query']:.1f} статей на запрос")
            print()
    
    def _show_pdfs_info(self):
        """Показать информацию о скачанных PDF"""
        print("\n📁 ИНФОРМАЦИЯ О СКАЧАННЫХ PDF")
        print("=" * 35)
        
        pdf_info = self.parser.get_downloaded_pdfs_info()
        
        if not pdf_info:
            print("📭 PDF файлы не найдены")
            return
        
        # Группируем по темам
        themes = {}
        total_size = 0
        
        for info in pdf_info:
            theme = info['theme']
            if theme not in themes:
                themes[theme] = {'count': 0, 'size': 0, 'files': []}
            themes[theme]['count'] += 1
            themes[theme]['size'] += info['size_mb']
            themes[theme]['files'].append(info)
            total_size += info['size_mb']
        
        print(f"📊 Всего PDF: {len(pdf_info)} файлов, {total_size:.1f} MB")
        print()
        
        for theme, data in themes.items():
            print(f"📂 {theme.replace('_', ' ').title()}")
            print(f"   Файлов: {data['count']}, Размер: {data['size']:.1f} MB")
            
            # Показываем последние 3 файла
            for file_info in data['files'][:3]:
                filename = file_info['filename'][:60] + "..." if len(file_info['filename']) > 60 else file_info['filename']
                print(f"   - {filename} ({file_info['size_mb']:.1f} MB)")
            
            if len(data['files']) > 3:
                print(f"   ... и еще {len(data['files']) - 3} файлов")
            print()
    
    def _show_config(self):
        """Показать конфигурацию системы"""
        print("\n⚙️ КОНФИГУРАЦИЯ СИСТЕМЫ")
        print("=" * 30)
        
        config = self.coordinator.config
        
        print(f"📋 Общие настройки:")
        print(f"   Максимум результатов на запрос: {config['search_settings']['max_results_per_query']}")
        print(f"   Диапазон дат: {config['search_settings']['date_range_years']} лет")
        print(f"   Минимум статей на тему: {config['search_settings']['min_articles_per_theme']}")
        print(f"   Максимум запросов на сессию: {config['search_settings']['max_queries_per_session']}")
        
        print(f"\n🎯 Приоритеты:")
        for priority, value in config['priorities'].items():
            print(f"   {priority.replace('_', ' ').title()}: {value}")
        
        print(f"\n🔬 Темы исследования ({len(config['research_themes'])}):")
        for theme in config['research_themes']:
            queries_count = len(config['query_templates'].get(theme, []))
            print(f"   - {theme.replace('_', ' ').title()} ({queries_count} шаблонов запросов)")
    
    def _export_results(self):
        """Экспорт результатов исследования"""
        print("\n📤 ЭКСПОРТ РЕЗУЛЬТАТОВ")
        print("=" * 25)
        
        try:
            format_choice = input("Формат экспорта (json/csv/both, по умолчанию both): ").lower() or "both"
            filename_base = input("Базовое имя файла (по умолчанию longevity_export): ") or "longevity_export"
            
            # Получаем данные из базы
            import sqlite3
            
            with sqlite3.connect(self.coordinator.db_path) as conn:
                cursor = conn.cursor()
                
                # Экспортируем статьи
                cursor.execute('''
                    SELECT a.pmid, a.title, a.authors, a.journal, a.publication_date,
                           a.doi, a.abstract, a.keywords, q.theme, q.query_text
                    FROM articles a
                    JOIN queries q ON a.query_id = q.id
                    ORDER BY a.timestamp DESC
                ''')
                
                articles_data = []
                for row in cursor.fetchall():
                    articles_data.append({
                        'pmid': row[0],
                        'title': row[1],
                        'authors': json.loads(row[2]) if row[2] else [],
                        'journal': row[3],
                        'publication_date': row[4],
                        'doi': row[5],
                        'abstract': row[6],
                        'keywords': json.loads(row[7]) if row[7] else [],
                        'theme': row[8],
                        'query': row[9]
                    })
            
            # Сохраняем в выбранных форматах
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format_choice in ['json', 'both']:
                json_file = f"{filename_base}_{timestamp}.json"
                json_file = f"output/{json_file}"  # Ensure JSON files are saved in the 'output' directory
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(articles_data, f, ensure_ascii=False, indent=2)
                print(f"✅ JSON экспорт сохранен: {json_file}")
            
            if format_choice in ['csv', 'both']:
                csv_file = f"{filename_base}_{timestamp}.csv"
                csv_file = f"output/{csv_file}"  # Ensure CSV files are saved in the 'output' directory
                import csv
                
                if articles_data:
                    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=articles_data[0].keys())
                        writer.writeheader()
                        
                        for article in articles_data:
                            # Преобразуем списки в строки для CSV
                            csv_article = article.copy()
                            csv_article['authors'] = '; '.join(article['authors'])
                            csv_article['keywords'] = '; '.join(article['keywords'])
                            writer.writerow(csv_article)
                    
                    print(f"✅ CSV экспорт сохранен: {csv_file}")
            
            print(f"📊 Экспортировано {len(articles_data)} статей")
            
        except Exception as e:
            print(f"❌ Ошибка экспорта: {e}")
    
    def _cleanup_pdfs(self):
        """Очистка битых PDF файлов"""
        print("\n🧹 ОЧИСТКА PDF ФАЙЛОВ")
        print("=" * 25)
        
        cleaned = self.parser.cleanup_failed_downloads()
        if cleaned == 0:
            print("✨ Все PDF файлы в хорошем состоянии")
        else:
            print(f"🗑️ Удалено {cleaned} битых PDF файлов")
    
    def _show_help(self):
        """Показать справку по командам"""
        print("\n❓ СПРАВКА ПО КОМАНДАМ")
        print("=" * 25)
        
        commands = {
            'start': 'Запуск новой исследовательской сессии',
            'status': 'Показать текущий статус системы',
            'themes': 'Прогресс исследования по темам',
            'recommendations': 'Рекомендации для улучшения',
            'pdfs': 'Информация о скачанных PDF файлах',
            'config': 'Показать конфигурацию системы',
            'export': 'Экспорт результатов в JSON/CSV',
            'cleanup': 'Очистка битых PDF файлов',
            'exit': 'Выход из программы'
        }
        
        for cmd, desc in commands.items():
            print(f"  {cmd:<15} - {desc}")


def main():
    """Главная функция запуска системы"""
    parser = argparse.ArgumentParser(
        description="Мультиагентная система исследования долголетия на основе PubMed",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python longevity_research_system.py --interactive
  python longevity_research_system.py --queries 50 --pdf
  python longevity_research_system.py --email your@email.com --api-key YOUR_KEY
        """
    )
    
    parser.add_argument('--email', help='Email для PubMed API')
    parser.add_argument('--api-key', help='API ключ для PubMed')
    parser.add_argument('--interactive', action='store_true', help='Интерактивный режим')
    parser.add_argument('--queries', type=int, default=20, help='Максимум запросов (по умолчанию 20)')
    parser.add_argument('--no-pdf', action='store_true', help='Не скачивать PDF файлы')
    parser.add_argument('--target-articles', type=int, help='Целевое количество статей на тему')
    parser.add_argument('--session-name', help='Имя сессии')
    parser.add_argument('--config', default='longevity_config.json', help='Путь к файлу конфигурации')
    parser.add_argument('--db', default='longevity_research.db', help='Путь к базе данных')
    parser.add_argument('--pdf-dir', default='longevity_pdfs', help='Директория для PDF файлов')
    
    args = parser.parse_args()
    
    try:
        # Создаем систему
        system = LongevityResearchSystem(
            config_path=args.config,
            db_path=args.db,
            pdf_dir=args.pdf_dir,
            email=args.email,
            api_key=args.api_key
        )
        
        if args.interactive:
            # Интерактивный режим
            system.run_interactive_mode()
        else:
            # Режим командной строки
            system.run_research_session(
                max_queries=args.queries,
                download_pdfs=not args.no_pdf,
                target_articles_per_theme=args.target_articles,
                session_name=args.session_name
            )
    
    except KeyboardInterrupt:
        print("\n👋 Программа завершена пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
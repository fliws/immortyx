# PubMed Парсер 🧬

Полнофункциональный парсер для работы с базой данных PubMed через официальный API E-utilities. Позволяет искать научные статьи, получать детальную информацию и сохранять результаты в различных форматах.

## 🚀 Возможности

- ✅ **Поиск статей** по ключевым словам
- ✅ **Фильтрация по дате** публикации
- ✅ **Получение детальной информации** о статьях
- ✅ **Работа с PMID** (PubMed ID)
- ✅ **Экспорт результатов** в JSON и CSV
- ✅ **Соблюдение лимитов API** NCBI
- ✅ **Анализ и статистика** найденных статей

## 📦 Установка

1. Клонируйте репозиторий или скачайте файлы
2. Установите зависимости:
```bash
pip install -r requirements.txt
```

## 🔧 Быстрый старт

### Базовое использование

```python
from pubmed_parser import PubMedParser

# Создаем экземпляр парсера
parser = PubMedParser(email="your_email@example.com")  # Email рекомендуется

# Поиск статей
articles = parser.search_and_fetch("COVID-19 vaccine", max_results=10)

# Вывод информации о первой статье
if articles:
    article = articles[0]
    print(f"Заголовок: {article['title']}")
    print(f"Авторы: {', '.join(article['authors'])}")
    print(f"Журнал: {article['journal']}")
    print(f"Дата: {article['publication_date']}")
    print(f"PMID: {article['pmid']}")
    print(f"DOI: {article['doi']}")
```

### Поиск с фильтром по дате

```python
# Поиск статей за определенный период
articles = parser.search_and_fetch(
    query="machine learning healthcare",
    max_results=20,
    date_from="2023/01/01",
    date_to="2024/12/31"
)
```

### Получение статей по PMID

```python
# Если у вас есть конкретные PMID
pmids = ["38704809", "38704550", "38704392"]
articles = parser.get_article_details(pmids)
```

### Сохранение результатов

```python
# Сохранение в JSON
parser.save_to_json(articles, "research_results.json")

# Сохранение в CSV
parser.save_to_csv(articles, "research_results.csv")
```

## 📚 Подробная документация

### Класс PubMedParser

#### Инициализация

```python
PubMedParser(email=None, api_key=None)
```

**Параметры:**
- `email` (str, optional): Ваш email для идентификации при работе с API NCBI
- `api_key` (str, optional): API ключ для увеличения лимитов запросов

#### Основные методы

##### search_articles()
Поиск статей по ключевым словам.

```python
search_articles(query, max_results=100, date_from=None, date_to=None)
```

**Параметры:**
- `query` (str): Поисковый запрос
- `max_results` (int): Максимальное количество результатов (по умолчанию 100)
- `date_from` (str): Дата начала поиска в формате "YYYY/MM/DD"
- `date_to` (str): Дата окончания поиска в формате "YYYY/MM/DD"

**Возвращает:** Список PMID найденных статей

##### get_article_details()
Получение детальной информации о статьях.

```python
get_article_details(pmids)
```

**Параметры:**
- `pmids` (str или List[str]): PMID статьи или список PMID

**Возвращает:** Список словарей с информацией о статьях

##### search_and_fetch()
Комбинированный метод: поиск и получение детальной информации.

```python
search_and_fetch(query, max_results=100, date_from=None, date_to=None)
```

## 📊 Структура данных статьи

Каждая статья представлена словарем со следующими полями:

```python
{
    'pmid': '12345678',                    # PubMed ID
    'title': 'Название статьи',            # Заголовок
    'authors': ['Иванов И.И.', 'Петров П.П.'], # Список авторов
    'journal': 'Nature Medicine',          # Название журнала
    'publication_date': '2024-03-15',      # Дата публикации
    'abstract': 'Текст аннотации...',      # Аннотация
    'doi': '10.1038/s41591-024-...',      # DOI
    'keywords': ['медицина', 'AI'],        # Ключевые слова
    'pubmed_url': 'https://pubmed.ncbi...' # Ссылка на PubMed
}
```

## 🔍 Примеры поисковых запросов

### Простые запросы
```python
"COVID-19"
"machine learning"
"cancer treatment"
"diabetes type 2"
```

### Комплексные запросы
```python
"machine learning AND medical imaging"
"COVID-19 OR SARS-CoV-2"
"cancer AND immunotherapy AND clinical trial"
"deep learning AND diagnosis NOT review"
```

### Поиск по полям
```python
"Smith J[Author]"           # По автору
"Nature[Journal]"           # По журналу
"2024[Publication Date]"    # По году
"10.1038[DOI]"             # По DOI
```

## 🏃‍♂️ Запуск примеров

В проекте включен файл с примерами использования:

```bash
python example_usage.py
```

Этот скрипт демонстрирует:
- Базовый поиск статей
- Поиск с фильтром по дате
- Получение статей по PMID
- Сохранение результатов
- Продвинутый поиск
- Анализ найденных статей

## ⚙️ Настройки API

### Лимиты запросов
- **Без API ключа**: 3 запроса в секунду
- **С API ключом**: 10 запросов в секунду
- Парсер автоматически соблюдает эти лимиты

### Получение API ключа
1. Зарегистрируйтесь на [NCBI](https://www.ncbi.nlm.nih.gov/account/)
2. Перейдите в [настройки API](https://www.ncbi.nlm.nih.gov/account/settings/)
3. Создайте API ключ
4. Используйте его при инициализации парсера:

```python
parser = PubMedParser(
    email="your_email@example.com",
    api_key="your_api_key_here"
)
```

## 📁 Структура проекта

```
pubmed_parser/
├── pubmed_parser.py    # Основной модуль парсера
├── example_usage.py    # Примеры использования
├── requirements.txt    # Зависимости
└── README.md          # Документация
```

## 🛠️ Обработка ошибок

Парсер корректно обрабатывает следующие ситуации:
- Сетевые ошибки
- Ошибки парсинга XML
- Превышение лимитов API
- Пустые результаты поиска

Все ошибки логируются в консоль с понятными сообщениями.

## 🎯 Лучшие практики

1. **Всегда указывайте email** при инициализации парсера
2. **Используйте разумные лимиты** на количество результатов
3. **Добавляйте паузы** между большими запросами
4. **Сохраняйте результаты** для повторного использования
5. **Используйте фильтры по дате** для актуальных исследований

## 🚨 Важные замечания

- Парсер использует официальный API E-utilities NCBI
- Соблюдайте [правила использования](https://www.ncbi.nlm.nih.gov/books/NBK25497/) API NCBI
- Для коммерческого использования требуется API ключ
- Не злоупотребляйте частотой запросов

## 🤝 Содействие

Если вы нашли баг или хотите предложить улучшение:
1. Создайте Issue с описанием проблемы
2. Предложите Pull Request с исправлением
3. Добавьте тесты для новой функциональности

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл LICENSE для подробностей.

## 🆘 Поддержка

Если у вас возникли вопросы или проблемы:
1. Проверьте документацию выше
2. Посмотрите примеры в `example_usage.py`
3. Создайте Issue с подробным описанием проблемы

---

**Удачного парсинга! 🧬📊** 
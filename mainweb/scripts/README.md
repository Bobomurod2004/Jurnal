# Translation Management Scripts

Набор скриптов для автоматизации работы с переводами в системе.

## Скрипты

### 1. extract_missing_translations.py
Извлекает из базы данных все алиасы, у которых отсутствуют переводы на русский и/или узбекский языки.

**Использование:**
```bash
python scripts/extract_missing_translations.py
```

**Результат:**
- Создает файл `missing_translations.json` с полным списком недостающих переводов
- Выводит статистику по количеству недостающих переводов

### 2. find_translations_usage.py
Анализирует использование алиасов переводов в коде и шаблонах для лучшего понимания контекста.

**Использование:**
```bash
python scripts/find_translations_usage.py
```

**Требования:**
- Наличие файла `missing_translations.json` (создается первым скриптом)

**Результат:**
- Создает файл `translation_usage_analysis.json` с информацией о том, где используется каждый алиас
- Помогает понять контекст использования для качественного перевода

### 3. update_translations.py
Обновляет переводы в базе данных на основе JSON файла с переводами.

**Использование:**
```bash
python scripts/update_translations.py
```

**Требования:**
- Наличие файла `translations_to_add.json` с переводами в формате:
```json
{
  "translations": {
    "alias_name": {
      "ru": "Русский перевод",
      "uz": "O'zbek tarjimasi"
    }
  }
}
```

**Результат:**
- Обновляет переводы в базе данных
- Очищает кеш переводов
- Выводит статистику обновлений

### 4. translation_report.py
Генерирует отчет о текущем состоянии всех переводов в системе.

**Использование:**
```bash
python scripts/translation_report.py
```

**Результат:**
- Создает файл `translation_status_report.json` с полным отчетом
- Выводит статистику по завершенности переводов
- Показывает процент готовности переводов

### 5. scholar_readiness_audit.py
Проверяет, насколько опубликованные статьи готовы к индексации в Google Scholar
(ключевые поля метаданных, авторы, том/номер, дата публикации, PDF для открытого доступа).

**Использование:**
```bash
python mainweb/scripts/scholar_readiness_audit.py
python mainweb/scripts/scholar_readiness_audit.py --limit 200 --json-out scholar_report.json
```

**Результат:**
- Печатает сводку готовности в консоль
- Показывает топ блокирующих проблем (`missing_title`, `missing_author`, и т.д.)
- Опционально сохраняет полный JSON-отчет для массовой правки

## Полный рабочий процесс

1. **Извлечение недостающих переводов:**
   ```bash
   python scripts/extract_missing_translations.py
   ```

2. **Анализ использования (опционально):**
   ```bash
   python scripts/find_translations_usage.py
   ```

3. **Создание файла с переводами:**
   - Вручную создать `translations_to_add.json` на основе `missing_translations.json`
   - Или использовать готовый файл `translations_to_add.json`

4. **Обновление переводов в БД:**
   ```bash
   python scripts/update_translations.py
   ```

5. **Проверка результатов:**
   ```bash
   python scripts/translation_report.py
   ```

## Файлы результатов

- `missing_translations.json` - Список недостающих переводов
- `translation_usage_analysis.json` - Анализ использования алиасов в коде
- `translations_to_add.json` - Файл с переводами для добавления (создается вручную)
- `translation_status_report.json` - Отчет о состоянии переводов

## Примечания

- Все скрипты используют коннектор из `modules/connector.py`
- Настройки подключения к БД берутся из `config.py`
- Скрипты безопасны для повторного запуска
- Автоматическое очищение кеша переводов после обновления

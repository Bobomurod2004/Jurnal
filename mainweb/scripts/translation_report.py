#!/usr/bin/env python3
"""
Скрипт для генерации отчета о состоянии переводов
"""

import sys
import os
import json
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.connector import PostgreSQLConnector
from config import *

def main():
    """Основная функция для генерации отчета"""
    
    # Подключаемся к базе данных
    dbc = PostgreSQLConnector(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    
    print("Generating translation status report...")
    
    # Получаем все переводы из БД
    translations = dbc.translations.all().exec()
    
    # Анализируем состояние переводов
    total_count = len(translations)
    complete_count = 0
    missing_ru_count = 0
    missing_uz_count = 0
    missing_both_count = 0
    
    complete_translations = []
    missing_translations = []
    
    for trans in translations:
        alias = trans['alias']
        content = trans.get('content', '')
        content_ru = trans.get('content_ru', '') or ''
        content_uz = trans.get('content_uz', '') or ''
        
        has_ru = bool(content_ru.strip())
        has_uz = bool(content_uz.strip())
        
        if has_ru and has_uz:
            complete_count += 1
            complete_translations.append({
                'alias': alias,
                'content_en': content,
                'content_ru': content_ru,
                'content_uz': content_uz
            })
        else:
            missing_translations.append({
                'alias': alias,
                'content_en': content,
                'content_ru': content_ru,
                'content_uz': content_uz,
                'missing_ru': not has_ru,
                'missing_uz': not has_uz
            })
            
            if not has_ru:
                missing_ru_count += 1
            if not has_uz:
                missing_uz_count += 1
            if not has_ru and not has_uz:
                missing_both_count += 1
    
    # Создаем отчет
    report = {
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_translations': total_count,
            'complete_translations': complete_count,
            'missing_ru_translations': missing_ru_count,
            'missing_uz_translations': missing_uz_count,
            'missing_both_translations': missing_both_count,
            'completion_percentage': round((complete_count / total_count * 100), 2) if total_count > 0 else 0
        },
        'complete_translations': complete_translations,
        'missing_translations': sorted(missing_translations, key=lambda x: x['alias'])
    }
    
    # Сохраняем отчет
    report_file = 'translation_status_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # Выводим краткий отчет
    print(f"\nTranslation Status Report")
    print(f"========================")
    print(f"Total translations: {total_count}")
    print(f"Complete translations (RU + UZ): {complete_count}")
    print(f"Missing Russian translations: {missing_ru_count}")
    print(f"Missing Uzbek translations: {missing_uz_count}")
    print(f"Missing both translations: {missing_both_count}")
    print(f"Completion percentage: {report['summary']['completion_percentage']}%")
    print(f"\nDetailed report saved to: {report_file}")
    
    # Показываем примеры недостающих переводов
    if missing_translations:
        print(f"\nStill missing translations:")
        for i, trans in enumerate(missing_translations[:10]):
            status = []
            if trans['missing_ru']:
                status.append('RU')
            if trans['missing_uz']:
                status.append('UZ')
            print(f"  {i+1}. {trans['alias']} (missing: {', '.join(status)})")
        
        if len(missing_translations) > 10:
            print(f"  ... and {len(missing_translations) - 10} more")
    else:
        print(f"\nAll translations are complete!")

if __name__ == "__main__":
    main()
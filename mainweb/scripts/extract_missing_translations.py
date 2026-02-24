#!/usr/bin/env python3
"""
Скрипт для извлечения алиасов переводов без русского и узбекского переводов
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
    """Основная функция для извлечения недостающих переводов"""
    
    # Подключаемся к базе данных
    dbc = PostgreSQLConnector(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    
    print("Searching for aliases without translations...")
    
    # Get all translations from DB
    translations = dbc.translations.all().exec()
    
    missing_translations = []
    
    for trans in translations:
        alias = trans['alias']
        content = trans.get('content', '')
        content_ru = trans.get('content_ru', '') or ''
        content_uz = trans.get('content_uz', '') or ''
        
        # Check for empty translations
        missing_ru = not content_ru.strip()
        missing_uz = not content_uz.strip()
        
        if missing_ru or missing_uz:
            missing_translations.append({
                'alias': alias,
                'content_en': content,
                'missing_ru': missing_ru,
                'missing_uz': missing_uz,
                'content_ru': content_ru,
                'content_uz': content_uz
            })
    
    # Sort by alias for convenience
    missing_translations.sort(key=lambda x: x['alias'])
    
    # Create report
    report = {
        'extracted_at': datetime.now().isoformat(),
        'total_missing': len(missing_translations),
        'missing_ru_count': sum(1 for t in missing_translations if t['missing_ru']),
        'missing_uz_count': sum(1 for t in missing_translations if t['missing_uz']),
        'translations': missing_translations
    }
    
    # Write to file
    output_file = 'missing_translations.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"Found {len(missing_translations)} aliases with missing translations")
    print(f"Statistics:")
    print(f"   - Missing Russian translations: {report['missing_ru_count']}")
    print(f"   - Missing Uzbek translations: {report['missing_uz_count']}")
    print(f"Result saved to: {output_file}")
    
    # Show first 10 for preview
    print(f"\nExamples of missing translations:")
    for i, trans in enumerate(missing_translations[:10]):
        print(f"   {i+1}. {trans['alias']} (EN: '{trans['content_en']}')")
        if trans['missing_ru']:
            print(f"      Missing Russian translation")
        if trans['missing_uz']:
            print(f"      Missing Uzbek translation")
    
    if len(missing_translations) > 10:
        print(f"   ... and {len(missing_translations) - 10} more aliases")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Скрипт для обновления переводов в базе данных из JSON файла
"""

import sys
import os
import json
import time

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.connector import PostgreSQLConnector
from config import *

def main():
    """Основная функция для обновления переводов"""
    
    # Проверяем наличие файла с переводами
    translations_file = 'translations_to_add.json'
    if not os.path.exists(translations_file):
        print(f"Error: {translations_file} not found.")
        print("Please create the translations file first.")
        return
    
    # Читаем переводы из файла
    with open(translations_file, 'r', encoding='utf-8') as f:
        translations_data = json.load(f)
    
    # Подключаемся к базе данных
    dbc = PostgreSQLConnector(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    
    print("Starting translations update...")
    
    translations = translations_data.get('translations', {})
    updated_count = 0
    errors_count = 0
    
    for alias, trans_data in translations.items():
        try:
            print(f"Updating {alias}...")
            
            # Получаем текущую запись из БД
            existing = dbc.translations.get().equal(alias=alias).exec()
            
            if not existing:
                print(f"  Warning: Translation '{alias}' not found in database, skipping...")
                continue
            
            # Подготавливаем данные для обновления
            update_data = {}
            
            if 'ru' in trans_data and trans_data['ru']:
                update_data['content_ru'] = trans_data['ru']
            
            if 'uz' in trans_data and trans_data['uz']:
                update_data['content_uz'] = trans_data['uz']
            
            if not update_data:
                print(f"  Warning: No translations to update for '{alias}', skipping...")
                continue
            
            # Обновляем запись
            dbc.translations.get().equal(alias=alias).update(**update_data).exec()
            
            updated_count += 1
            print(f"  Successfully updated {alias}")
            
            # Показываем что обновилось
            if 'ru' in update_data:
                print(f"    RU: {update_data['content_ru']}")
            if 'uz' in update_data:
                print(f"    UZ: {update_data['content_uz']}")
            
        except Exception as e:
            errors_count += 1
            print(f"  Error updating {alias}: {e}")
    
    print(f"\nTranslations update completed!")
    print(f"Successfully updated: {updated_count}")
    print(f"Errors: {errors_count}")
    print(f"Total processed: {len(translations)}")
    
    # Очищаем кеш переводов
    try:
        from modules.translate import clear_translations_cache
        clear_translations_cache()
        print("Translation cache cleared successfully.")
    except Exception as e:
        print(f"Warning: Could not clear translation cache: {e}")

if __name__ == "__main__":
    main()
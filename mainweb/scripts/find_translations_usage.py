#!/usr/bin/env python3
"""
Скрипт для поиска использования переводов в шаблонах и коде
"""

import os
import re
import json
from pathlib import Path

def find_translation_usage(alias, search_dirs):
    """Находит использование алиаса перевода в файлах"""
    usage_locations = []
    
    # Patterns to search for
    patterns = [
        rf'{{{{ t\([\'"]({re.escape(alias)})[\'"][^}}]*\}}}}',  # Jinja2 {{ t('alias') }}
        rf't\([\'"]({re.escape(alias)})[\'"][^)]*\)',  # Python t('alias')
        rf'{{{{ t\([\'"]({re.escape(alias)})[\'"]\) \}}}}',  # Alternative Jinja2
    ]
    
    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
            
        for root, dirs, files in os.walk(search_dir):
            for file in files:
                if file.endswith(('.html', '.py', '.js')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        for pattern in patterns:
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            for match in matches:
                                # Find line number
                                line_num = content[:match.start()].count('\n') + 1
                                line_content = content.split('\n')[line_num - 1].strip()
                                
                                usage_locations.append({
                                    'file': os.path.relpath(file_path),
                                    'line': line_num,
                                    'context': line_content,
                                    'match': match.group(0)
                                })
                    except (UnicodeDecodeError, PermissionError):
                        continue
    
    return usage_locations

def main():
    """Основная функция"""
    
    # Читаем файл с недостающими переводами
    if not os.path.exists('missing_translations.json'):
        print("Error: missing_translations.json not found. Run extract_missing_translations.py first.")
        return
    
    with open('missing_translations.json', 'r', encoding='utf-8') as f:
        missing_data = json.load(f)
    
    print("Searching for translation usage in code...")
    
    # Директории для поиска
    search_dirs = ['templates', 'run.py', 'modules']
    
    # Результаты анализа
    usage_analysis = {
        'analyzed_at': missing_data['extracted_at'],
        'total_aliases': len(missing_data['translations']),
        'aliases_with_usage': [],
        'aliases_without_usage': []
    }
    
    for i, trans in enumerate(missing_data['translations']):
        alias = trans['alias']
        print(f"Analyzing {i+1}/{len(missing_data['translations'])}: {alias}")
        
        usage_locations = find_translation_usage(alias, search_dirs)
        
        if usage_locations:
            usage_analysis['aliases_with_usage'].append({
                'alias': alias,
                'content_en': trans['content_en'],
                'missing_ru': trans['missing_ru'],
                'missing_uz': trans['missing_uz'],
                'usage_count': len(usage_locations),
                'locations': usage_locations
            })
        else:
            usage_analysis['aliases_without_usage'].append({
                'alias': alias,
                'content_en': trans['content_en'],
                'missing_ru': trans['missing_ru'],
                'missing_uz': trans['missing_uz']
            })
    
    # Сохраняем результаты
    output_file = 'translation_usage_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(usage_analysis, f, ensure_ascii=False, indent=2)
    
    print(f"\nAnalysis completed!")
    print(f"Total aliases analyzed: {usage_analysis['total_aliases']}")
    print(f"Aliases with usage found: {len(usage_analysis['aliases_with_usage'])}")
    print(f"Aliases without usage: {len(usage_analysis['aliases_without_usage'])}")
    print(f"Detailed analysis saved to: {output_file}")
    
    # Показываем примеры
    print(f"\nExamples of aliases with usage:")
    for i, alias_data in enumerate(usage_analysis['aliases_with_usage'][:5]):
        print(f"  {i+1}. {alias_data['alias']} - used {alias_data['usage_count']} times")
        for loc in alias_data['locations'][:2]:
            print(f"     {loc['file']}:{loc['line']}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import sys
import os
import time

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.connector import PostgreSQLConnector
from config import *

def add_test_tariffs():
    # Initialize database connection
    dbc = PostgreSQLConnector(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    
    # Test tariffs data
    tariffs = [
        {
            'name': 'Monthly Access',
            'name_uz': 'Oylik kirish',
            'name_ru': 'Месячный доступ',
            'description': 'Perfect for short-term access to all articles',
            'description_uz': 'Barcha maqolalarga qisqa muddatli kirish uchun ideal',
            'description_ru': 'Идеально для краткосрочного доступа ко всем статьям',
            'price_usd': 10.00,
            'price_uzs': 120000,
            'price_rub': 900,
            'user_limit': 30,
            'is_default': False,
            'created_at': int(time.time()),
            'updated_at': int(time.time())
        },
        {
            'name': 'Annual Access',
            'name_uz': 'Yillik kirish',
            'name_ru': 'Годовой доступ',
            'description': 'Best value for regular readers - save 17%',
            'description_uz': 'Doimiy o\'quvchilar uchun eng yaxshi narx - 17% tejang',
            'description_ru': 'Лучшая цена для постоянных читателей - экономия 17%',
            'price_usd': 100.00,
            'price_uzs': 1200000,
            'price_rub': 9000,
            'user_limit': 365,
            'is_default': True,
            'created_at': int(time.time()),
            'updated_at': int(time.time())
        },
        {
            'name': 'Student Plan',
            'name_uz': 'Talaba rejasi',
            'name_ru': 'Студенческий план',
            'description': 'Special pricing for students and researchers',
            'description_uz': 'Talabalar va tadqiqotchilar uchun maxsus narx',
            'description_ru': 'Специальная цена для студентов и исследователей',
            'price_usd': 5.00,
            'price_uzs': 60000,
            'price_rub': 450,
            'user_limit': 30,
            'is_default': False,
            'created_at': int(time.time()),
            'updated_at': int(time.time())
        },
        {
            'name': 'Premium Access',
            'name_uz': 'Premium kirish',
            'name_ru': 'Премиум доступ',
            'description': 'Unlimited access with priority support',
            'description_uz': 'Ustuvor yordam bilan cheksiz kirish',
            'description_ru': 'Безлимитный доступ с приоритетной поддержкой',
            'price_usd': 200.00,
            'price_uzs': 2400000,
            'price_rub': 18000,
            'user_limit': 365,
            'is_default': False,
            'created_at': int(time.time()),
            'updated_at': int(time.time())
        }
    ]
    
    # Clear existing tariffs (optional)
    print("Clearing existing tariffs...")
    try:
        dbc.tariffs.get().delete().exec()
        print("Existing tariffs cleared.")
    except Exception as e:
        print(f"Note: Could not clear existing tariffs: {e}")
    
    # Add new tariffs
    print("Adding test tariffs...")
    for tariff_data in tariffs:
        try:
            result = dbc.tariffs.add(**tariff_data).exec()
            if result:
                print(f"✓ Added tariff: {tariff_data['name']}")
            else:
                print(f"✗ Failed to add tariff: {tariff_data['name']}")
        except Exception as e:
            print(f"✗ Error adding tariff {tariff_data['name']}: {e}")
    
    print("\nTest tariffs added successfully!")
    print("You can now test the subscription system with different currencies.")

if __name__ == "__main__":
    add_test_tariffs() 
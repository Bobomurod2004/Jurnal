import sys
import os
import time
from datetime import datetime, timedelta
import random

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.connector import PostgreSQLConnector

def add_test_issues():
    # Initialize database connection
    dbc = PostgreSQLConnector(host='127.0.0.1', port=5432, user='postgres', password='1', database='journal')
    
    # Sample titles and descriptions
    titles = [
        "Advances in Modern Linguistics",
        "Contemporary Language Studies",
        "Theoretical and Applied Linguistics",
        "Language and Society",
        "Cognitive Linguistics Research"
    ]
    
    shortinfos = [
        "Special focus on computational linguistics and natural language processing",
        "Research in sociolinguistics and language variation",
        "Studies in phonology, morphology, and syntax",
        "Exploring the intersection of language and culture",
        "Investigating language acquisition and learning"
    ]
    
    # Generate issues for years 2022-2024
    for year in range(2022, 2025):
        # Each year has 4 issues
        for issue_no in range(1, 5):
            # Calculate creation timestamp
            issue_date = datetime(year, issue_no * 3, 1)  # Issues every 3 months
            created_at = int(issue_date.timestamp())
            
            # Randomly select title and info
            title_index = random.randint(0, len(titles) - 1)
            
            issue_data = {
                'title': f"{titles[title_index]} - {year}",
                'title_uz': f"{titles[title_index]} (UZ) - {year}",
                'title_ru': f"{titles[title_index]} (RU) - {year}",
                'vol_no': str(year - 2021),  # Volume numbers start from 1
                'issue_no': str(issue_no),
                'year': year,
                'category': 'regular',
                'shortinfo': shortinfos[title_index],
                'shortinfo_uz': f"{shortinfos[title_index]} (UZ)",
                'shortinfo_ru': f"{shortinfos[title_index]} (RU)",
                'price': 29.99 if year == 2024 else 19.99,  # Newer issues cost more
                'price_uz': 350000 if year == 2024 else 250000,
                'price_ru': 2900 if year == 2024 else 1900,
                'subscription_enable': year == 2024,  # Only current year issues require subscription
                'is_paid': True,  # All issues are paid content
                'cover_image': f"/static/uploads/covers/issue_{year}_{issue_no}.jpg",
                'created_at': created_at
            }
            
            # Add the issue to database
            result = dbc.issues.add(**issue_data).exec()
            
            if result:
                print(f"Added issue: Volume {issue_data['vol_no']}, Issue {issue_data['issue_no']}, Year {year}")
            else:
                print(f"Failed to add issue for year {year}, issue {issue_no}")

if __name__ == '__main__':
    add_test_issues() 
import sys
import os
import time

# Add parent directory to path to import connector
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.connector import PostgreSQLConnector

# Initialize database connection
dbc = PostgreSQLConnector(host='127.0.0.1', port=5432, user='postgres', password='1', database='journal')

# Test authors data
authors = [
    {
        'user_id': 1,  # Main user
        'name': 'John Smith',
        'organization': 'University of Linguistics',
        'position': 'Associate Professor',
        'email': 'john.smith@uling.edu',
        'phone': '+1 234 567 8901',
        'orcid': '0000-0001-2345-6789',
        'address_street': '123 University Ave',
        'address_city': 'Linguiston',
        'address_country': 'United States',
        'address_zip': '12345',
        'created_at': int(time.time()) - 86400 * 90
    },
    {
        'user_id': None,  # Co-author
        'name': 'Maria Garcia',
        'organization': 'Institute of Language Studies',
        'position': 'Senior Researcher',
        'email': 'maria.garcia@ils.edu',
        'phone': '+34 612 345 678',
        'orcid': '0000-0002-3456-7890',
        'address_street': 'Calle de la Lengua 45',
        'address_city': 'Madrid',
        'address_country': 'Spain',
        'address_zip': '28001',
        'created_at': int(time.time()) - 86400 * 85
    },
    {
        'user_id': None,  # Co-author
        'name': 'Akmal Karimov',
        'organization': 'Tashkent State University',
        'position': 'Professor',
        'email': 'a.karimov@tashsu.uz',
        'phone': '+998 90 123 4567',
        'orcid': '0000-0003-4567-8901',
        'address_street': '100 University Street',
        'address_city': 'Tashkent',
        'address_country': 'Uzbekistan',
        'address_zip': '100174',
        'created_at': int(time.time()) - 86400 * 80
    },
    {
        'user_id': None,  # Co-author
        'name': 'Sarah Johnson',
        'organization': 'Digital Linguistics Institute',
        'position': 'Research Fellow',
        'email': 's.johnson@dli.org',
        'phone': '+44 20 7123 4567',
        'orcid': '0000-0004-5678-9012',
        'address_street': '45 Tech Road',
        'address_city': 'London',
        'address_country': 'United Kingdom',
        'address_zip': 'EC1A 1BB',
        'created_at': int(time.time()) - 86400 * 75
    }
]

def add_authors():
    """Add authors and return a dictionary mapping their names to their IDs"""
    author_ids = {}
    
    # First, clear existing author profiles except for those connected to users
    print("Clearing existing test author profiles...")
    dbc.author_profile.get().equal(user_id=None).delete().exec()
    
    # Add or update each author
    print("Adding test authors...")
    for author in authors:
        if author['user_id']:
            # Update existing profile for user
            existing = dbc.author_profile.get(user_id=author['user_id']).exec()
            if existing:
                dbc.author_profile.get(user_id=author['user_id']).update(**author).exec()
                author_ids[author['name']] = existing[0]['id']
            else:
                result = dbc.author_profile.add(**author).exec()
                author_ids[author['name']] = result[0]['id']
        else:
            # Add new profile for co-author
            result = dbc.author_profile.add(**author).exec()
            author_ids[author['name']] = result[0]['id']
    
    return author_ids

# Test submissions data with author names (to be replaced with IDs)
submissions_template = [
    {
        'user_id': 1,
        'status': 'draft',
        'title': 'Linguistic Analysis of Modern Poetry',
        'abstract': 'This study explores the linguistic patterns in modern poetry...',
        'is_special': False,
        'is_dataset': False,
        'check_copyright': True,
        'keywords': ['linguistics', 'poetry', 'modern literature'],
        'classifications': ['linguistics', 'literature'],
        'check_ethical': True,
        'check_consent': True,
        'check_acknowledgements': True,
        'is_used_previous': False,
        'word_count': 4500,
        'is_corresponding_author': True,
        'main_author': 'John Smith',
        'sub_authors': ['Maria Garcia', 'Akmal Karimov'],
        'is_competing_interests': False,
        'notes': None,
        'file_authors': 'linguistic_analysis_authors.pdf',
        'file_anonymized': 'linguistic_analysis_anonymous.pdf',
        'created_date': int(time.time()) - 86400 * 5,  # 5 days ago
        'updated_at': int(time.time()) - 86400 * 4,
    },
    {
        'user_id': 1,
        'status': 'in_process',
        'title': 'Comparative Study of English and Uzbek Idioms',
        'abstract': 'This research compares and contrasts idiomatic expressions...',
        'is_special': False,
        'is_dataset': True,
        'check_copyright': True,
        'keywords': ['idioms', 'comparative linguistics', 'English', 'Uzbek'],
        'classifications': ['linguistics', 'comparative studies'],
        'check_ethical': True,
        'check_consent': True,
        'check_acknowledgements': True,
        'is_used_previous': False,
        'word_count': 5200,
        'is_corresponding_author': True,
        'main_author': 'John Smith',
        'sub_authors': ['Maria Garcia'],
        'is_competing_interests': False,
        'notes': None,
        'file_authors': 'idioms_study_authors.pdf',
        'file_anonymized': 'idioms_study_anonymous.pdf',
        'created_date': int(time.time()) - 86400 * 15,  # 15 days ago
        'updated_at': int(time.time()) - 86400 * 10,
    },
    {
        'user_id': 1,
        'status': 'rejected',
        'title': 'Evolution of Syntax in Central Asian Languages',
        'abstract': 'An analysis of syntactic changes in Central Asian languages...',
        'is_special': True,
        'is_dataset': False,
        'check_copyright': True,
        'keywords': ['syntax', 'Central Asian languages', 'language evolution'],
        'classifications': ['linguistics', 'syntax', 'historical linguistics'],
        'check_ethical': True,
        'check_consent': True,
        'check_acknowledgements': True,
        'is_used_previous': False,
        'word_count': 6300,
        'is_corresponding_author': True,
        'main_author': 'John Smith',
        'sub_authors': [],
        'is_competing_interests': False,
        'notes': 'The scope of the research is too broad. Please narrow down the focus to specific languages or time periods. The methodology needs more rigorous definition.',
        'file_authors': 'syntax_evolution_authors.pdf',
        'file_anonymized': 'syntax_evolution_anonymous.pdf',
        'created_date': int(time.time()) - 86400 * 30,  # 30 days ago
        'updated_at': int(time.time()) - 86400 * 25,
    },
    {
        'user_id': 1,
        'status': 'published',
        'title': 'Phonological Features of Modern Uzbek Dialects',
        'abstract': 'This paper examines the distinctive phonological features...',
        'is_special': False,
        'is_dataset': True,
        'check_copyright': True,
        'keywords': ['phonology', 'Uzbek', 'dialects', 'linguistics'],
        'classifications': ['linguistics', 'phonology', 'dialectology'],
        'check_ethical': True,
        'check_consent': True,
        'check_acknowledgements': True,
        'is_used_previous': False,
        'word_count': 4800,
        'is_corresponding_author': True,
        'main_author': 'John Smith',
        'sub_authors': ['Akmal Karimov', 'Sarah Johnson', 'Maria Garcia'],
        'is_competing_interests': False,
        'notes': None,
        'file_authors': 'uzbek_phonology_authors.pdf',
        'file_anonymized': 'uzbek_phonology_anonymous.pdf',
        'created_date': int(time.time()) - 86400 * 60,  # 60 days ago
        'updated_at': int(time.time()) - 86400 * 45,
    },
]

def main():
    try:
        # First add authors and get their IDs
        author_ids = add_authors()
        print("Authors added successfully!")
        
        # Clear existing test submissions for user_id 1
        print("Clearing existing test submissions...")
        dbc.submissions.get(user_id=1).delete().exec()
        
        # Add each submission with proper author IDs
        print("Adding test submissions...")
        for submission in submissions_template:
            # Convert author names to IDs
            submission_data = submission.copy()
            submission_data['main_author_id'] = author_ids[submission_data.pop('main_author')]
            submission_data['sub_author_ids'] = [author_ids[name] for name in submission_data.pop('sub_authors')]
            
            # Add submission
            dbc.submissions.add(**submission_data).exec()
        
        # Verify the count
        count = dbc.submissions.get(user_id=1).count().exec()
        print(f"Added {count} test submissions successfully!")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
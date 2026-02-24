import sys
import os
import time
from datetime import datetime, timedelta
import random

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.connector import PostgreSQLConnector

def add_test_publications():
    # Initialize database connection
    dbc = PostgreSQLConnector(host='127.0.0.1', port=5432, user='postgres', password='1', database='journal')
    
    # Get all issues ordered by year and issue number
    issues = dbc.issues.get().exec()
    if not issues:
        print("No issues found in the database")
        return

    # Get author profiles
    author_profiles = dbc.author_profile.get().exec()
    if not author_profiles:
        print("No author profiles found in the database")
        return

    print(f"Found {len(issues)} issues and {len(author_profiles)} author profiles")

    # Sample publication data
    titles = [
        "A Comparative Analysis of Morphological Features in Modern English and Uzbek Languages",
        "The Role of Cognitive Linguistics in Second Language Acquisition",
        "Semantic Evolution of Technical Terms in Contemporary Scientific Literature",
        "Cross-Cultural Pragmatics: A Study of Speech Acts in Academic Discourse",
        "Digital Humanities and Corpus Linguistics: New Methods in Philological Research",
        "The Impact of Social Media on Language Change and Evolution",
        "Translation Challenges in Literary Texts: A Case Study of Modern Poetry",
        "Phonological Adaptation of Loanwords in Central Asian Languages",
        "Discourse Analysis of Political Speeches: A Linguistic Perspective",
        "Teaching Methods in Modern Language Education: An Evidence-Based Approach"
    ]
    
    abstracts = [
        "This study examines the morphological features and their comparative aspects in modern English and Uzbek languages. Through detailed analysis of word formation patterns, inflectional morphology, and derivational processes, we identify key similarities and differences between these typologically distinct languages.",
        "Our research investigates the role of cognitive linguistics in second language acquisition, focusing on how mental processes influence language learning. The findings suggest that cognitive approaches significantly enhance vocabulary retention and grammatical understanding.",
        "This paper analyzes the semantic evolution of technical terminology in contemporary scientific literature, tracking changes in meaning and usage over time. We present a diachronic study of selected terms from multiple scientific disciplines.",
        "A comprehensive examination of speech acts in academic discourse across different cultural contexts. This research highlights the importance of pragmatic competence in academic communication and identifies culture-specific patterns in scholarly discourse.",
        "This article explores the intersection of digital humanities and corpus linguistics, presenting new methodological approaches to philological research. We demonstrate how computational tools enhance traditional philological analysis methods."
    ]
    
    keywords_list = [
        ["morphology", "comparative linguistics", "English", "Uzbek", "word formation"],
        ["cognitive linguistics", "SLA", "language learning", "mental processes"],
        ["semantics", "terminology", "diachronic linguistics", "scientific language"],
        ["pragmatics", "speech acts", "academic discourse", "cross-cultural communication"],
        ["digital humanities", "corpus linguistics", "computational methods", "philology"],
        ["sociolinguistics", "language change", "social media", "digital communication"],
        ["translation studies", "literary translation", "poetry", "equivalence"],
        ["phonology", "loanwords", "language contact", "Central Asian languages"],
        ["discourse analysis", "political linguistics", "rhetoric", "public speaking"],
        ["language pedagogy", "teaching methodology", "educational linguistics"]
    ]

    # Add publications for each issue
    for issue in issues:
        # Number of publications per issue (random between 8 and 12)
        num_publications = random.randint(8, 12)
        
        for i in range(num_publications):
            # Select random title and its corresponding data
            title_index = random.randint(0, len(titles) - 1)
            
            # Calculate dates
            issue_date = datetime.fromtimestamp(issue['created_at'])
            date_sent = issue_date - timedelta(days=random.randint(90, 180))
            date_accept = date_sent + timedelta(days=random.randint(30, 60))
            date_publish = issue_date
            
            # Generate DOI and DOI link
            doi = f"10.{random.randint(1000,9999)}/philology.{issue['year']}.{issue['issue_no']}.{i+1}"
            doi_link = f"https://doi.org/{doi}"
            
            # Select random authors
            main_author = random.choice(author_profiles)
            co_authors = random.sample([a for a in author_profiles if a['id'] != main_author['id']], 
                                     k=random.randint(0, 2))
            co_author_ids = [a['id'] for a in co_authors]
            
            # Create a dummy PDF file for this publication
            file_id = None
            try:
                file_data = {
                    'name': f"publication_{issue['year']}_{issue['issue_no']}_{i+1}.pdf",  # Changed from filename to name
                    'original_name': 'sample_publication.pdf',
                    'type': 'application/pdf',  # Changed from mime_type to type
                    'created_at': int(time.time())
                }
                file_result = dbc.files.add(**file_data).exec()
                if file_result:
                    file_id = file_result[0]['id']
            except Exception as e:
                print(f"Failed to create file record: {e}")
            
            # Prepare publication data according to the exact schema
            publication_data = {
                'title': titles[title_index],
                'title_uz': None,  # Added as per schema
                'title_ru': None,  # Added as per schema
                'abstract': abstracts[random.randint(0, len(abstracts) - 1)],
                'abstract_uz': None,  # Added as per schema
                'abstract_ru': None,  # Added as per schema
                'keywords': keywords_list[title_index],
                'issue_id': issue['id'],
                'main_author_id': main_author['id'],
                'subauthor_ids': co_author_ids,
                'doi': doi,
                'doi_link': doi_link,  # Added as per schema
                'additional': None,  # Added as per schema
                'stat_views': random.randint(50, 500),
                'stat_alt': random.randint(10, 100),  # Changed from stat_downloads
                'stat_crossref': random.randint(0, 50),  # Added as per schema
                'stat_wos': random.randint(0, 30),  # Added as per schema
                'stat_scopus': random.randint(0, 20),  # Added as per schema
                'date_sent': int(date_sent.timestamp()),
                'date_accept': int(date_accept.timestamp()),
                'date_publish': int(date_publish.timestamp()),
                'stage': 'published',  # Added as per schema
                'comments': None,  # Added as per schema
                'is_paid': issue['is_paid'],
                'subscription_enable': issue['subscription_enable'],
                'price': float(issue['price']) if issue['price'] is not None else 0.0,
                'price_uz': float(issue['price_uz']) if issue.get('price_uz') is not None else 0.0,  # Added as per schema
                'price_ru': float(issue['price_ru']) if issue.get('price_ru') is not None else 0.0,  # Added as per schema
                'file_ids': [file_id] if file_id else [],
                'created_at': int(time.time())
            }
            
            try:
                # Add the publication to database
                result = dbc.publications.add(**publication_data).exec()
                
                if result:
                    print(f"Added publication: {publication_data['title']} to Issue {issue['issue_no']}, Year {issue['year']}")
                else:
                    print(f"Failed to add publication to Issue {issue['issue_no']}, Year {issue['year']}")
            except Exception as e:
                print(f"Error adding publication: {e}")
                print(f"Publication data: {publication_data}")

if __name__ == '__main__':
    add_test_publications() 
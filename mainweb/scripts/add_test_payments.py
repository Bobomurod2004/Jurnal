import sys
import os
import time

# Add parent directory to path to import connector
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.connector import PostgreSQLConnector

# Initialize database connection
dbc = PostgreSQLConnector(host='127.0.0.1', port=5432, user='postgres', password='1', database='journal')

def add_test_payments():
    # Current timestamp for created_at
    current_time = int(time.time())
    
    # Example payment data
    payments = [
        {
            'user_id': 1,  # Assuming user with ID 1 exists
            'status': 'declined',
            'currency': 'usd',
            'payment_type': 'subscription',
            'payment_date': current_time - (60 * 60 * 24),  # 1 day ago
            'amount': 29.99,
            'ids': None,  # No article IDs for subscription
            'proof': None,
            'note': 'Subscription for 1 month - Payment declined',
            'created_at': current_time - (60 * 60 * 24 * 2)  # 2 days ago
        },
        {
            'user_id': 1,
            'status': 'unpaid',
            'currency': 'usd',
            'payment_type': 'subscription',
            'payment_date': None,
            'amount': 29.99,
            'ids': None,
            'proof': None,
            'note': 'Subscription for 1 month - Waiting for payment',
            'created_at': current_time - (60 * 60 * 12)  # 12 hours ago
        },
        {
            'user_id': 1,
            'status': 'paid',
            'currency': 'usd',
            'payment_type': 'article',
            'payment_date': current_time - (60 * 60 * 48),  # 2 days ago
            'amount': 49.99,
            'ids': [1, 2, 3],  # Example article IDs
            'proof': 'payment_proof_123.pdf',
            'note': 'Article purchase - 3 articles',
            'created_at': current_time - (60 * 60 * 72)  # 3 days ago
        },
        {
            'user_id': 2,  # Different user
            'status': 'paid',
            'currency': 'usd',
            'payment_type': 'subscription',
            'payment_date': current_time - (60 * 60 * 24 * 15),  # 15 days ago
            'amount': 29.99,
            'ids': None,
            'proof': 'payment_proof_456.pdf',
            'note': 'Subscription for 1 month - Active',
            'created_at': current_time - (60 * 60 * 24 * 16)  # 16 days ago
        }
    ]

    # Add payments to database
    for payment in payments:
        result = dbc.payments.add(**payment).exec()
        if result:
            print(f"Added payment: {payment['payment_type']} - {payment['status']} - ${payment['amount']}")
        else:
            print(f"Failed to add payment: {payment['payment_type']} - {payment['status']}")

if __name__ == '__main__':
    print("Adding test payments to database...")
    add_test_payments()
    print("Done!") 
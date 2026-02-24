import sys
import os
import time
from datetime import datetime

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.connector import PostgreSQLConnector

def add_test_subscription():
    # Initialize database connection
    dbc = PostgreSQLConnector(host='127.0.0.1', port=5432, user='postgres', password='1', database='journal')
    
    # Calculate timestamps
    current_time = int(time.time())
    end_of_2025 = int(datetime(2025, 12, 31, 23, 59, 59).timestamp())
    
    # Create a paid subscription payment
    payment_data = {
        'user_id': 1,
        'status': 'paid',
        'currency': 'usd',
        'payment_type': 'subscription',
        'payment_date': current_time,
        'amount': 100.00,  # Annual subscription amount
        'created_at': current_time,
        'note': '12'  # Indicates 12 months subscription
    }
    
    # Add the payment record
    payment_result = dbc.payments.add(**payment_data).exec()
    
    if not payment_result:
        print("Failed to create payment record")
        return
    
    # Update user's subscription end date
    user_update = dbc.users.get(id=1).update(
        subscription_end_date=end_of_2025
    ).exec()
    
    if not user_update:
        print("Failed to update user's subscription end date")
        return
    
    print(f"Successfully added subscription for user 1")
    print(f"Subscription will end on: {datetime.fromtimestamp(end_of_2025).strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    add_test_subscription() 
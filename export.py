# export.py
import csv
import os
from datetime import datetime
import pandas as pd
from database import get_all_clients

def export_to_csv(filename=None):
    """Export all client data to a CSV file"""
    if filename is None:
        filename = f"netflix_clients_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    clients = get_all_clients()
    
    # Create directory if it doesn't exist
    os.makedirs('exports', exist_ok=True)
    filepath = os.path.join('exports', filename)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Token', 'Name', 'Email', 'Profile', 'Start Date', 'End Date', 'Status'])
        for client in clients:
            writer.writerow(client)
    
    return filepath

def export_to_excel(filename=None):
    """Export all client data to an Excel file"""
    if filename is None:
        filename = f"netflix_clients_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    clients = get_all_clients()
    
    # Create directory if it doesn't exist
    os.makedirs('exports', exist_ok=True)
    filepath = os.path.join('exports', filename)
    
    # Convert to pandas DataFrame
    df = pd.DataFrame(clients, columns=['Token', 'Name', 'Email', 'Profile', 'Start Date', 'End Date', 'Status'])
    
    # Export to Excel
    df.to_excel(filepath, index=False)
    
    return filepath

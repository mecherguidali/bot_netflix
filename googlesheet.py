# googlesheet.py
import os
import gspread
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import json
import sys

# Google Sheets configuration
SPREADSHEET_NAME = "Netflix Clients DB"
# Si vous avez déjà un spreadsheet, utilisez son ID ici
# Laissez vide pour utiliser le nom à la place (mais cela nécessite plus d'espace de stockage)


#id hetha houaa taa3 sheet 
SPREADSHEET_ID = "1a5Pls1g1D_dJ4LGH1uAepUyfZBrZ3yNEtcXs_GCfDsg"  # ID de votre spreadsheet
CLIENTS_SHEET = "clients"
BURNED_SHEET = "burned_tokens"
OPERATIONS_SHEET = "operations_log"

# Define the service account file
SERVICE_ACCOUNT_FILE = 'bot-netflix.json'

# Global variables for connection
_client = None
_spreadsheet = None

def _connect():
    """Connect to Google Sheets API"""
    global _client, _spreadsheet
    
    if _client is not None:
        return _client
    
    try:
        print("Attempting to authenticate with Google Sheets using service account...")
        
        # Use service account authentication - much simpler and more reliable
        try:
            # Check if service account file exists
            if os.path.exists(SERVICE_ACCOUNT_FILE):
                # Use the service account file directly
                _client = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
                print(f"Authentication successful using service account: {SERVICE_ACCOUNT_FILE}")
            else:
                print(f"Service account file {SERVICE_ACCOUNT_FILE} not found.")
                raise Exception("Service account file not found")
        except Exception as e:
            print(f"Service account authentication error: {e}")
            print("\nPlease make sure:")
            print("1. The service account file exists and is valid")
            print("2. Google Sheets API and Google Drive API are enabled in your Google Cloud Console")
            print("3. The spreadsheet is shared with the service account email:")
            print("   db-netflix@bot-netflix-473417-473511.iam.gserviceaccount.com\n")
            
            # Exit with error instead of falling back to local database
            print("\nERROR: Cannot continue without Google Sheets authentication.")
            print("Please fix the authentication issues and try again.\n")
            
            # Raise the exception to stop execution
            raise
        
        # Try to open existing spreadsheet by ID or name, or create a new one
        try:
            if SPREADSHEET_ID:
                # Ouvrir par ID (plus fiable)
                _spreadsheet = _client.open_by_key(SPREADSHEET_ID)
                print(f"Connected to existing spreadsheet by ID: {SPREADSHEET_ID}")
            else:
                # Ouvrir par nom
                _spreadsheet = _client.open(SPREADSHEET_NAME)
                print(f"Connected to existing spreadsheet by name: {SPREADSHEET_NAME}")
        except (gspread.SpreadsheetNotFound, gspread.exceptions.APIError):
            # Si le quota est dépassé, nous ne pouvons pas créer de nouveau spreadsheet
            # Demandons à l'utilisateur de créer un spreadsheet manuellement
            print("\nERROR: Could not find the spreadsheet and cannot create a new one due to storage quota limits.")
            print("Please create a spreadsheet manually in Google Sheets and share it with:")
            print("db-netflix@bot-netflix-473417-473511.iam.gserviceaccount.com")
            print("Then update the SPREADSHEET_ID variable in googlesheet.py with the spreadsheet ID.")
            print("The spreadsheet ID is the long string in the URL of your spreadsheet:")
            print("https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit")
            raise Exception("Spreadsheet not found and cannot create a new one due to quota limits")
            
        return _client
    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        raise

def _get_sheet(sheet_name):
    """Get a worksheet by name, creating it if it doesn't exist"""
    if _spreadsheet is None:
        _connect()
    
    try:
        # Try to get the existing sheet
        worksheet = _spreadsheet.worksheet(sheet_name)
        return worksheet
    except gspread.WorksheetNotFound:
        # Sheet doesn't exist, create it based on the sheet name
        if sheet_name == CLIENTS_SHEET:
            print(f"Creating sheet {CLIENTS_SHEET}...")
            worksheet = _spreadsheet.add_worksheet(title=CLIENTS_SHEET, rows=100, cols=12)
            headers = ["id", "token", "name", "email", "profile", "start_date", "end_date", "status", "payment_amount", "is_burned", "burn_reason", "burn_date"]
            worksheet.append_row(headers)
            print(f"Sheet {CLIENTS_SHEET} created successfully.")
        elif sheet_name == BURNED_SHEET:
            print(f"Creating sheet {BURNED_SHEET}...")
            worksheet = _spreadsheet.add_worksheet(title=BURNED_SHEET, rows=100, cols=5)
            headers = ["id", "token", "burn_reason", "burn_date", "client_id"]
            worksheet.append_row(headers)
            print(f"Sheet {BURNED_SHEET} created successfully.")
        elif sheet_name == OPERATIONS_SHEET:
            print(f"Creating sheet {OPERATIONS_SHEET}...")
            worksheet = _spreadsheet.add_worksheet(title=OPERATIONS_SHEET, rows=1000, cols=10)
            headers = ["id", "timestamp", "operation_type", "token", "details", "amount", "client_id"]
            worksheet.append_row(headers)
            print(f"Sheet {OPERATIONS_SHEET} created successfully.")
        else:
            # Generic sheet creation
            worksheet = _spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=10)
            print(f"Generic sheet {sheet_name} created.")
        
        return worksheet

def _get_clients_sheet():
    """Get or create the clients worksheet"""
    clients_sheet = _get_sheet(CLIENTS_SHEET)
    
    # Verify headers
    headers = clients_sheet.row_values(1)
    if not headers or len(headers) < 3:  # Check that there are at least some headers
        print(f"Sheet {CLIENTS_SHEET} exists but has no headers. Adding headers...")
        headers = ["id", "token", "name", "email", "profile", "start_date", "end_date", "status", "payment_amount", "is_burned", "burn_reason", "burn_date"]
        clients_sheet.clear()
        clients_sheet.append_row(headers)
        print("Headers added successfully.")
    
    return clients_sheet

def _get_burned_sheet():
    """Get or create the burned tokens worksheet"""
    burned_sheet = _get_sheet(BURNED_SHEET)
    
    # Verify headers
    headers = burned_sheet.row_values(1)
    if not headers or len(headers) < 3:  # Check that there are at least some headers
        print(f"Sheet {BURNED_SHEET} exists but has no headers. Adding headers...")
        headers = ["id", "token", "burn_reason", "burn_date", "client_id"]
        burned_sheet.clear()
        burned_sheet.append_row(headers)
        print("Headers added successfully.")
    
    return burned_sheet

def init_db():
    """Initialize the database (create spreadsheet and worksheets if needed)"""
    try:
        _connect()
        _get_clients_sheet()
        _get_burned_sheet()
        _get_operations_sheet()  # Initialize operations log sheet
        print("Google Sheets database initialized")
    except Exception as e:
        print(f"Error initializing database: {e}")
        print("\nERROR: Cannot initialize Google Sheets database.")
        print("Please make sure:")
        print("1. The service account file exists and is valid")
        print("2. Google Sheets API and Google Drive API are enabled in your Google Cloud Console")
        print("3. The spreadsheet is shared with the service account email:")
        print("   db-netflix@bot-netflix-473417-473511.iam.gserviceaccount.com\n")
        raise

def _find_row_by_token(token):
    """Find a row by token and return row number and data"""
    sheet = _get_clients_sheet()
    all_values = sheet.get_all_values()
    headers = all_values[0]
    
    # Find token column index
    token_idx = headers.index("token")
    
    for i, row in enumerate(all_values[1:], start=2):  # Start from 2 to account for header row
        if row[token_idx] == token:
            return i, row
    
    return None, None

def token_exists(token):
    """Check if a token already exists"""
    row_num, _ = _find_row_by_token(token)
    return row_num is not None

def add_client(token, name, email, profile, duration):
    """Add a new client to the sheet"""
    sheet = _get_clients_sheet()
    
    # Calculate dates
    start_date = datetime.now()
    start_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
    
    # Parse duration
    if duration.endswith("m"):
        delta = timedelta(minutes=int(duration[:-1]))
    elif duration.endswith("h"):
        delta = timedelta(hours=int(duration[:-1]))
    elif duration.endswith("d"):
        delta = timedelta(days=int(duration[:-1]))
    else:
        delta = timedelta(days=int(duration))
    
    end_date = start_date + delta
    end_str = end_date.strftime("%Y-%m-%d %H:%M:%S")
    
    # Get next ID
    all_values = sheet.get_all_values()
    next_id = len(all_values)  # Simple auto-increment
    
    # Prepare row
    new_row = [
        str(next_id),
        token,
        name,
        email,
        profile,
        start_str,
        end_str,
        "Unpaid",
        "0.0",  # payment_amount
        "0",    # is_burned
        "",     # burn_reason
        ""      # burn_date
    ]
    
    # Append to sheet
    sheet.append_row(new_row)
    
    # Log the NEW operation
    details = f"Profile: {profile}, Duration: {duration}"
    _log_operation("NEW", token, details, 0, str(next_id))
    
    return start_date, end_date

def get_client_by_token(token):
    """Get client details by token"""
    row_num, row_data = _find_row_by_token(token)
    if row_num is None:
        return None
    
    sheet = _get_clients_sheet()
    headers = sheet.row_values(1)
    
    # Convert payment_amount to float
    payment_idx = headers.index("payment_amount") if "payment_amount" in headers else -1
    if payment_idx >= 0 and payment_idx < len(row_data) and row_data[payment_idx]:
        row_data[payment_idx] = float(row_data[payment_idx])
    
    # Return as tuple to match database.py behavior
    return tuple(row_data)

def update_status(token, new_status, payment_amount=None):
    """Update client status and optionally payment amount"""
    row_num, row_data = _find_row_by_token(token)
    if row_num is None:
        return
    
    sheet = _get_clients_sheet()
    headers = sheet.row_values(1)
    
    # Update status
    status_idx = headers.index("status") + 1  # +1 because gspread is 1-indexed
    sheet.update_cell(row_num, status_idx, new_status)
    
    # Update payment amount if provided
    if payment_amount is not None:
        payment_idx = headers.index("payment_amount") + 1
        sheet.update_cell(row_num, payment_idx, str(payment_amount))
        
        # Log PAID operation when status is changed to Paid
        if new_status == "Paid":
            client_id = row_data[0] if row_data and len(row_data) > 0 else ""
            details = f"Status changed to Paid"
            _log_operation("PAID", token, details, payment_amount, client_id)

def extend_subscription(token, extra_days):
    """Extend subscription by adding days to end_date"""
    row_num, row_data = _find_row_by_token(token)
    if row_num is None:
        return None
    
    sheet = _get_clients_sheet()
    headers = sheet.row_values(1)
    
    # Get end date
    end_idx = headers.index("end_date")
    end_str = row_data[end_idx]
    
    # Parse date
    try:
        end_date = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            end_date = datetime.strptime(end_str, "%Y-%m-%d")
        except ValueError:
            print(f"Error parsing date: {end_str}")
            return None
    
    # Calculate new end date
    new_end = end_date + timedelta(days=extra_days)
    new_end_str = new_end.strftime("%Y-%m-%d %H:%M:%S")
    
    # Update in sheet
    sheet.update_cell(row_num, end_idx + 1, new_end_str)
    
    # Log EXT operation
    client_id = row_data[0] if row_data and len(row_data) > 0 else ""
    details = f"(+{extra_days} days)"
    _log_operation("EXT", token, details, 0, client_id)
    
    return new_end

def get_unpaid_clients():
    """Get list of unpaid clients"""
    sheet = _get_clients_sheet()
    all_values = sheet.get_all_values()
    headers = all_values[0]
    
    # Find column indices
    token_idx = headers.index("token")
    name_idx = headers.index("name")
    profile_idx = headers.index("profile")
    start_idx = headers.index("start_date")
    end_idx = headers.index("end_date")
    status_idx = headers.index("status")
    
    # Filter unpaid clients
    unpaid = []
    for row in all_values[1:]:  # Skip header
        if row[status_idx] == "Unpaid":
            unpaid.append((
                row[token_idx],
                row[name_idx],
                row[profile_idx],
                row[start_idx],
                row[end_idx]
            ))
    
    return unpaid

def get_all_clients():
    """Get all clients"""
    sheet = _get_clients_sheet()
    all_values = sheet.get_all_values()
    headers = all_values[0]
    
    # Find column indices
    token_idx = headers.index("token")
    name_idx = headers.index("name")
    email_idx = headers.index("email")
    profile_idx = headers.index("profile")
    start_idx = headers.index("start_date")
    end_idx = headers.index("end_date")
    status_idx = headers.index("status")
    
    # Extract client data
    clients = []
    for row in all_values[1:]:  # Skip header
        clients.append((
            row[token_idx],
            row[name_idx],
            row[email_idx],
            row[profile_idx],
            row[start_idx],
            row[end_idx],
            row[status_idx]
        ))
    
    return clients

def burn_token(token, reason):
    """Mark a token as burned"""
    row_num, row_data = _find_row_by_token(token)
    if row_num is None:
        return False, "Token not found"
    
    sheet = _get_clients_sheet()
    headers = sheet.row_values(1)
    
    # Check if already burned
    is_burned_idx = headers.index("is_burned")
    if row_data[is_burned_idx] == "1":
        return False, "Token is already burned"
    
    # Current time
    burn_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Update client record
    sheet.update_cell(row_num, is_burned_idx + 1, "1")
    sheet.update_cell(row_num, headers.index("burn_reason") + 1, reason)
    sheet.update_cell(row_num, headers.index("burn_date") + 1, burn_date)
    
    # Add to burned tokens sheet
    burned_sheet = _get_burned_sheet()
    burned_values = burned_sheet.get_all_values()
    next_id = len(burned_values)
    
    burned_sheet.append_row([
        str(next_id),
        token,
        reason,
        burn_date,
        row_data[0]  # client_id
    ])
    
    # Log operation
    _log_operation("BURN", token, reason, 0, row_data[0])
    
    return True, f"Token {token} has been burned successfully"

def _get_burned_sheet():
    """Get the burned tokens sheet"""
    return _get_sheet(BURNED_SHEET)

def _get_operations_sheet():
    """Get the operations log sheet"""
    operations_sheet = _get_sheet(OPERATIONS_SHEET)
    
    # Verify headers
    headers = operations_sheet.row_values(1)
    if not headers or len(headers) < 3:  # Check that there are at least some headers
        print(f"Sheet {OPERATIONS_SHEET} exists but has no headers. Adding headers...")
        headers = ["id", "timestamp", "operation_type", "token", "details", "amount", "client_id"]
        operations_sheet.clear()
        operations_sheet.append_row(headers)
        print("Headers added successfully.")
    
    return operations_sheet

def _log_operation(op_type, token, details, amount=0, client_id=""):
    """Log an operation to the operations log sheet"""
    try:
        operations_sheet = _get_operations_sheet()
        operations = operations_sheet.get_all_values()
        next_id = len(operations)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        operations_sheet.append_row([
            str(next_id),
            timestamp,
            op_type,
            token,
            details,
            str(amount),
            client_id
        ])
        return True
    except Exception as e:
        print(f"Error logging operation: {e}")
        return False

def get_burned_tokens():
    """Get all burned tokens"""
    burned_sheet = _get_burned_sheet()
    clients_sheet = _get_clients_sheet()
    
    burned_values = burned_sheet.get_all_values()
    client_values = clients_sheet.get_all_values()
    
    # Skip if no data
    if len(burned_values) <= 1:  # Only header
        return []
    
    # Create client lookup by ID
    client_headers = client_values[0]
    id_idx = client_headers.index("id")
    name_idx = client_headers.index("name")
    email_idx = client_headers.index("email")
    profile_idx = client_headers.index("profile")
    
    clients_by_id = {}
    for row in client_values[1:]:
        clients_by_id[row[id_idx]] = {
            "name": row[name_idx],
            "email": row[email_idx],
            "profile": row[profile_idx]
        }
    
    # Process burned tokens
    burned_headers = burned_values[0]
    token_idx = burned_headers.index("token")
    reason_idx = burned_headers.index("burn_reason")
    date_idx = burned_headers.index("burn_date")
    client_id_idx = burned_headers.index("client_id")
    
    result = []
    for row in burned_values[1:]:
        client_id = row[client_id_idx]
        client = clients_by_id.get(client_id, {"name": "", "email": "", "profile": ""})
        
        result.append((
            row[token_idx],
            row[reason_idx],
            row[date_idx],
            client["name"],
            client["email"],
            client["profile"]
        ))
    
    # Sort by date, newest first
    result.sort(key=lambda x: x[2], reverse=True)
    return result

def get_stats():
    """Get subscription statistics"""
    sheet = _get_clients_sheet()
    all_values = sheet.get_all_values()
    
    if len(all_values) <= 1:  # Only header or empty
        return 0, 0, 0, 0, 0
    
    headers = all_values[0]
    status_idx = headers.index("status")
    end_idx = headers.index("end_date")
    is_burned_idx = headers.index("is_burned")
    
    total = len(all_values) - 1  # Exclude header
    paid = sum(1 for row in all_values[1:] if row[status_idx] == "Paid")
    unpaid = sum(1 for row in all_values[1:] if row[status_idx] == "Unpaid")
    
    # Count expired
    now = datetime.now()
    expired = 0
    for row in all_values[1:]:
        try:
            end_date = datetime.strptime(row[end_idx], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                end_date = datetime.strptime(row[end_idx], "%Y-%m-%d")
            except ValueError:
                continue
        
        if end_date < now:
            expired += 1
    
    # Count burned
    burned = sum(1 for row in all_values[1:] if row[is_burned_idx] == "1")
    
    return total, paid, unpaid, expired, burned

def get_expiring_clients(days):
    """Get clients expiring within specified days"""
    sheet = _get_clients_sheet()
    all_values = sheet.get_all_values()
    headers = all_values[0]
    
    # Find column indices
    token_idx = headers.index("token")
    name_idx = headers.index("name")
    profile_idx = headers.index("profile")
    end_idx = headers.index("end_date")
    status_idx = headers.index("status")
    payment_idx = headers.index("payment_amount") if "payment_amount" in headers else -1
    
    # Calculate limit date
    now = datetime.now()
    limit = now + timedelta(days=days)
    
    # Filter expiring clients
    expiring = []
    for row in all_values[1:]:
        try:
            end_date = datetime.strptime(row[end_idx], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                end_date = datetime.strptime(row[end_idx], "%Y-%m-%d")
            except ValueError:
                continue
        
        if now <= end_date <= limit:
            # Get payment amount if available
            payment_amount = 0.0
            if payment_idx >= 0 and payment_idx < len(row) and row[payment_idx]:
                try:
                    payment_amount = float(row[payment_idx])
                except (ValueError, TypeError):
                    payment_amount = 0.0
                    
            expiring.append((
                row[token_idx],
                row[name_idx],
                row[profile_idx],
                row[end_idx],
                row[status_idx],
                payment_amount
            ))
    
    return expiring

def search_clients(query):
    """Search for clients by name, email, profile, or token"""
    sheet = _get_clients_sheet()
    all_values = sheet.get_all_values()
    headers = all_values[0]
    
    # Find column indices
    token_idx = headers.index("token")
    name_idx = headers.index("name")
    email_idx = headers.index("email")
    profile_idx = headers.index("profile")
    start_idx = headers.index("start_date")
    end_idx = headers.index("end_date")
    status_idx = headers.index("status")
    
    # Search
    query = query.lower()
    results = []
    
    for row in all_values[1:]:
        if (query in row[token_idx].lower() or
            query in row[name_idx].lower() or
            query in row[email_idx].lower() or
            query in row[profile_idx].lower()):
            
            results.append((
                row[token_idx],
                row[name_idx],
                row[email_idx],
                row[profile_idx],
                row[start_idx],
                row[end_idx],
                row[status_idx]
            ))
    
    return results

def get_recent_operations(limit=10):
    """Get recent operations from the operations log"""
    try:
        # Get operations from the dedicated operations log
        operations_sheet = _get_operations_sheet()
        all_operations = operations_sheet.get_all_values()
        
        if len(all_operations) <= 1:  # Only header or empty
            return []
            
        headers = all_operations[0]
        
        # Find column indices
        timestamp_idx = headers.index("timestamp")
        op_type_idx = headers.index("operation_type")
        token_idx = headers.index("token")
        details_idx = headers.index("details")
        amount_idx = headers.index("amount")
        client_id_idx = headers.index("client_id")
        
        # Get client info for better display
        clients_sheet = _get_clients_sheet()
        client_values = clients_sheet.get_all_values()
        client_headers = client_values[0]
        client_id_idx_client = client_headers.index("id")
        client_name_idx = client_headers.index("name")
        
        # Create client lookup by ID
        clients_by_id = {}
        for row in client_values[1:]:
            if len(row) > client_name_idx:
                clients_by_id[row[client_id_idx_client]] = row[client_name_idx]
        
        # Process operations
        operations = []
        for row in all_operations[1:]:  # Skip header
            try:
                # Parse timestamp
                timestamp_str = row[timestamp_idx]
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    timestamp = datetime.now()  # Fallback
                
                # Get amount
                amount = 0
                if amount_idx < len(row) and row[amount_idx]:
                    try:
                        amount = float(row[amount_idx])
                    except (ValueError, TypeError):
                        amount = 0
                
                # Get client name if available
                client_id = row[client_id_idx] if client_id_idx < len(row) else ""
                client_name = clients_by_id.get(client_id, "")
                
                # Fix duplicated names like "hamidihamidi"
                if client_name and len(client_name) % 2 == 0:
                    half_len = len(client_name) // 2
                    first_half = client_name[:half_len]
                    second_half = client_name[half_len:]
                    if first_half == second_half:
                        client_name = first_half  # Use just one half if duplicated
                
                # Add operation
                operations.append({
                    "type": row[op_type_idx],
                    "date": timestamp,
                    "token": row[token_idx],
                    "details": row[details_idx],
                    "amount": amount,
                    "client_name": client_name
                })
            except Exception as e:
                print(f"Error processing operation: {e}")
                continue
        
        # Sort operations by date (newest first)
        operations.sort(key=lambda x: x["date"], reverse=True)
        
        # Return limited number of operations
        return operations[:limit]
    except Exception as e:
        print(f"Error getting operations: {e}")
        return []

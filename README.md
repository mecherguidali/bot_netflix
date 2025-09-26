# Netflix Subscription Manager Bot

A Telegram bot for managing Netflix subscription clients with automatic reminders and comprehensive client management features. **This bot is restricted to administrators only.**

## Features

### Core Features
- **Client Registration**: Register new clients with `/new` command
- **Automatic Reminders**: Send reminders for unpaid accounts and expiring subscriptions
- **Client Queries**: Look up client details with their token
- **Trial Support**: Support for minute/hour-based trials (e.g., 2m = 2 minutes, 1h = 1 hour)
- **Enhanced Token Security**: Complex token generation with uniqueness validation
- **Token Burning**: Ability to permanently disable tokens with recorded reasons

### Management Commands
- `/pay TOKEN_ID [AMOUNT]` - Mark a subscription as paid with optional payment amount
- `/extend TOKEN_ID X` - Extend subscription by X days
- `/delete TOKEN_ID` - Delete a client
- `/unpaid` - List all unpaid clients
- `/expiring X` - List clients whose subscription ends within X days
- `/stats` - Show statistics (total clients, paid, unpaid, expiring soon)
- `/search QUERY` - Search for clients by name, email, token, or profile
- `/export [csv|excel]` - Export client data to CSV or Excel

### Token Management
- `/burn TOKEN_ID REASON` - Mark a token as burned (permanently disabled) with a reason
- `/burned` - List all burned tokens with their reasons and dates

### Help & Support
- `/help` - Show general help information
- `/help COMMAND` - Show detailed help for a specific command
- `/admin` - Check if you have admin privileges

### Access Control

This bot is configured with strict access control that allows **only administrators** to use it. Users who are not listed in the `ADMIN_IDS` environment variable will be denied access to all commands except:

- `/admin` - Check admin status and get User ID

Even the `/start` command is restricted to administrators only. Non-admin users who attempt to use the bot will receive an access denied message with instructions on how to request access.

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Telegram Bot Token (get from [@BotFather](https://t.me/BotFather))

### Installation

1. Clone this repository:
```
git clone https://github.com/yourusername/netflix-subscription-bot.git
cd netflix-subscription-bot
```

2. Create a virtual environment:
```
python -m venv env
```

3. Activate the virtual environment:
- Windows: `env\Scripts\activate`
- Linux/Mac: `source env/bin/activate`

4. Install dependencies:
```
pip install -r requirements.txt
```

5. Configure the bot:
- Create a `.env` file based on the provided `.env.example`
- Set `BOT_TOKEN` to your Telegram bot token (get from [@BotFather](https://t.me/BotFather))
- Set `CHAT_ID` to your Telegram chat ID or group ID for notifications
- Set `ADMIN_IDS` to a comma-separated list of Telegram user IDs who should have admin privileges
  (You can get your user ID by sending a message to [@userinfobot](https://t.me/userinfobot) on Telegram)

6. Run the bot:
```
python bot.py
```

## Admin Configuration

### Setting Up Admin Access

1. **Get Your Telegram User ID**:
   - Send a message to [@userinfobot](https://t.me/userinfobot) on Telegram
   - The bot will reply with your user ID (a number like `123456789`)

2. **Configure Admin IDs**:
   - Open your `.env` file
   - Add your Telegram user ID to the `ADMIN_IDS` variable
   - For multiple admins, separate IDs with commas: `ADMIN_IDS=123456789,987654321`

3. **Verify Admin Access**:
   - After starting the bot, send the `/admin` command
   - If configured correctly, you'll see a confirmation message with your admin status

### Security Considerations

- **Strict Access Control**: Only users with their IDs in the `ADMIN_IDS` list can access the bot's functionality
- **Complete Lockdown**: Even the `/start` command is restricted to administrators only
- **Access Logging**: All access attempts by non-admin users are logged with user ID and username
- **User Identification**: The `/admin` command is accessible to all users but only provides information about their status
- **Secure Configuration**: Admin IDs are stored securely in the `.env` file, which should not be committed to version control
- **Telegram Security**: Authentication is based on Telegram user IDs, which cannot be spoofed

## Usage

1. Start the bot by sending `/start` to get a list of available commands
2. Register a new client:
   ```
   /new John Smith john@example.com Profile1 30
   ```
   This registers John Smith for 30 days.

3. For trial periods, use:
   ```
   /new John Smith john@example.com Profile1 2h
   ```
   This registers John Smith for a 2-hour trial.

4. To mark a subscription as paid with an amount:
   ```
   /pay NFX-ABC1234-Profile1 50.5
   ```
   This marks the subscription as paid with an amount of 50.5.

5. To burn a token (permanently disable it):
   ```
   /burn NFX-ABC1234-Profile1 Account sharing detected
   ```
   This marks the token as burned with the specified reason.

6. To view all burned tokens:
   ```
   /burned
   ```
   This shows a list of all burned tokens with their reasons and dates.

## Database

The bot uses SQLite for data storage. The database file `clients.db` will be created automatically when you first run the bot.

### Database Schema

#### Clients Table
- `id`: Primary key
- `token`: Unique token for the client
- `name`: Client's name
- `email`: Client's email
- `profile`: Netflix profile name
- `start_date`: Subscription start date
- `end_date`: Subscription end date
- `status`: Payment status (Paid/Unpaid)
- `payment_amount`: Amount paid (if any)
- `is_burned`: Whether the token is burned (1) or active (0)
- `burn_reason`: Reason for burning the token
- `burn_date`: Date when the token was burned

#### Burned Tokens Table
- `id`: Primary key
- `token`: Burned token
- `burn_reason`: Reason for burning
- `burn_date`: Date when burned
- `client_id`: Foreign key to clients table

## Scheduled Tasks

The bot uses APScheduler to run the following scheduled tasks:
- Daily check for unpaid clients (24 hours after registration)
- Reminder for subscriptions expiring in 3 days
- Notification on subscription expiration day

## Export Data

Use the `/export` command to export all client data:
- `/export csv` - Export to CSV format
- `/export excel` - Export to Excel format

Exported files will be saved in the `exports` directory.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

# botnetflix.py
import logging
import random
import os
from datetime import datetime
from dotenv import load_dotenv
from datetime import timedelta
import re  # For token validation
# Load environment variables
load_dotenv()
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Create scheduler at the top level
scheduler = AsyncIOScheduler()

from googlesheet import (
    init_db, add_client, get_client_by_token, update_status, token_exists,
    extend_subscription, get_unpaid_clients, get_all_clients, get_stats, get_expiring_clients,
    search_clients, burn_token, get_burned_tokens, get_recent_operations
)
from auth import admin_required, load_admin_users, register_admin_check

# Get configuration from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
YOUR_CHAT_ID = int(os.getenv("CHAT_ID", 0))  # Default to 0 if not set
ADMIN_IDS = os.getenv("ADMIN_IDS", "")  # Admin user IDs

# Validate configuration
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set. Please set it in the .env file.")

if not YOUR_CHAT_ID:
    logging.warning("CHAT_ID environment variable is not set or invalid. Reminders will not be sent.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load admin users from environment variable
load_admin_users(ADMIN_IDS)

# Initialize database
init_db()

def parse_duration(duration_str: str) -> timedelta:
    duration_str = str(duration_str).lower()
    if duration_str.endswith("m"):
        return timedelta(minutes=int(duration_str[:-1]))
    elif duration_str.endswith("h"):
        return timedelta(hours=int(duration_str[:-1]))
    elif duration_str.endswith("d"):
        return timedelta(days=int(duration_str[:-1]))
    else:
        return timedelta(days=int(duration_str))  # default days

async def notify_expiration(app, chat_id, token, name, email, profile, end):
    try:
        await app.bot.send_message(
            chat_id=chat_id,
            text=(
                f"❌ *Subscription Expired*\n\n"
                f"🔑 Token: `{token}`\n"
                f"👤 {name} ({email}) – {profile}\n"
                f"📅 End: {end}"
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        # Fallback if Markdown parsing fails
        logger.error(f"Error sending formatted expiration message: {e}")
        await app.bot.send_message(
            chat_id=chat_id,
            text=(
                f"❌ Subscription Expired\n\n"
                f"🔑 Token: {token}\n"
                f"👤 {name} ({email}) – {profile}\n"
                f"📅 End: {end}"
            )
        )

# توليد Token - Generate more complex and unique tokens
def generate_token(profile):
    # Create a unique identifier with timestamp and random elements
    timestamp = datetime.now().strftime("%y%m%d%H%M")
    rand_id = random.randint(1000, 9999)
    
    # Create a unique hash based on profile name and timestamp
    profile_hash = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=4))
    
    # Format the token with prefix, timestamp hash, random ID, and profile
    token = f"NFX-{profile_hash}{rand_id}-{profile}"
    
    # Check if token already exists and regenerate if needed
    while token_exists(token):
        rand_id = random.randint(1000, 9999)
        profile_hash = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=4))
        token = f"NFX-{profile_hash}{rand_id}-{profile}"
    
    return token

# Helper function for command descriptions
def get_help_text():
    return (
        "👋 Welcome to Netflix Subscription Manager (Google Sheets)!\n\n"
        "⚠️ NOTE: This bot is restricted to administrators only.\n\n"
        "This bot helps you manage Netflix subscriptions for your clients.\n\n"
        "📝 Available Commands:\n\n"
        "Client Registration:\n"
        "👉 /new FullName Email Profile Duration - Register new client\n"
        "   Duration can be days (30), minutes (2m), or hours (1h)\n\n"
        "Client Management:\n"
        "👉 /token TOKEN_ID - View client details\n"
        "👉 /pay TOKEN_ID [AMOUNT] - Mark subscription as paid\n"
        "👉 /extend TOKEN_ID DAYS - Extend subscription\n\n"
        "Reports & Lists:\n"
        "👉 /unpaid - List all unpaid clients\n"
        "👉 /expiring DAYS - List clients expiring within DAYS\n"
        "👉 /stats - View subscription statistics\n"
        "👉 /search QUERY - Search for clients\n"
        "👉 /export [csv|excel] - Export client data\n\n"
        "Token Management:\n"
        "👉 /burn TOKEN_ID REASON - Mark a token as burned\n"
        "👉 /burned - List all burned tokens\n\n"
        "Help & Support:\n"
        "👉 /help - Show this help message\n"
        "👉 /help COMMAND - Show detailed help for a specific command\n"
        "👉 /admin - Check your admin status\n\n"
        "Examples:\n"
        "/new John Smith john@example.com Profile1 30\n"
        "/help new - Get detailed help for the new command\n"
    )

# /help command
@admin_required
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # If no arguments, show general help
    if not context.args:
        help_text = get_help_text()
        await update.message.reply_text(help_text)
        return
        
    # If command specified, show detailed help for that command
    command = context.args[0].lower().strip('/')
    
    command_help = {
        "new": (
            "📝 *Command: /new*\n\n"
            "*Usage:* /new FullName Email Profile Duration\n\n"
            "*Description:* Register a new Netflix client\n\n"
            "*Parameters:*\n"
            "- FullName: Client's full name\n"
            "- Email: Client's email address (for Netflix account)\n"
            "- Profile: Netflix profile name\n"
            "- Duration: Subscription duration\n  • Regular days: 30, 15, etc.\n  • Minutes: 2m, 30m, etc.\n  • Hours: 1h, 24h, etc.\n\n"
            "*Examples:*\n"
            "/new John Smith john@example.com Profile1 30\n"
            "/new Jane Doe jane@example.com Profile2 2h"
        ),
        "token": (
            "🔍 *Command: /token*\n\n"
            "*Usage:* /token TOKEN_ID\n\n"
            "*Description:* Look up client details using their token\n\n"
            "*Example:*\n"
            "/token NFX-123-Profile1"
        ),
        "pay": (
            "💰 *Command: /pay*\n\n"
            "*Usage:* /pay TOKEN_ID [AMOUNT]\n\n"
            "*Description:* Mark a client's subscription as paid with an optional payment amount\n\n"
            "*Parameters:*\n"
            "- TOKEN_ID: Client's token\n"
            "- AMOUNT: (Optional) Payment amount\n\n"
            "*Examples:*\n"
            "/pay NFX-123-Profile1\n"
            "/pay NFX-123-Profile1 50.5"
        ),
        "extend": (
            "⏳ *Command: /extend*\n\n"
            "*Usage:* /extend TOKEN_ID DAYS\n\n"
            "*Description:* Extend a client's subscription by specified days\n\n"
            "*Parameters:*\n"
            "- TOKEN_ID: Client's token\n"
            "- DAYS: Number of days to extend\n\n"
            "*Example:*\n"
            "/extend NFX-123-Profile1 30"
        ),
        "unpaid": (
            "⚠️ *Command: /unpaid*\n\n"
            "*Usage:* /unpaid\n\n"
            "*Description:* List all clients with unpaid status\n\n"
            "Displays each unpaid client with their name, profile, end date, and token.\n"
            "Tokens are formatted in code blocks for easy visibility and copying."
        ),
        "expiring": (
            "⏰ *Command: /expiring*\n\n"
            "*Usage:* /expiring DAYS\n\n"
            "*Description:* List all clients whose subscriptions expire within the specified days\n\n"
            "Displays each expiring client with their name, profile, end date, status, remaining time, and token.\n"
            "The remaining time shows exactly how many days or hours are left before expiration.\n"
            "Tokens are formatted in code blocks for easy visibility and copying.\n\n"
            "*Example:*\n"
            "/expiring 7"
        ),
        "stats": (
            "📊 *Command: /stats*\n\n"
            "*Usage:* /stats\n\n"
            "*Description:* Show subscription statistics including total clients, paid, unpaid, expired, and burned tokens"
        ),
        "search": (
            "🔎 *Command: /search*\n\n"
            "*Usage:* /search QUERY\n\n"
            "*Description:* Search for clients by name, email, profile, or token\n\n"
            "*Example:*\n"
            "/search john"
        ),
        "export": (
            "📁 *Command: /export*\n\n"
            "*Usage:* /export [csv|excel]\n\n"
            "*Description:* Export all client data to CSV or Excel format\n\n"
            "*Examples:*\n"
            "/export csv\n"
            "/export excel"
        ),
        "help": (
            "ℹ️ *Command: /help*\n\n"
            "*Usage:* /help [command]\n\n"
            "*Description:* Show general help or detailed help for a specific command\n\n"
            "*Examples:*\n"
            "/help\n"
            "/help new"
        ),
        "admin": (
            "🔑 *Command: /admin*\n\n"
            "*Usage:* /admin\n\n"
            "*Description:* Check if you have admin privileges\n\n"
            "Admin privileges are required for the following commands:\n"
            "- /pay - Mark subscription as paid\n"
            "- /extend - Extend subscription\n"
            "- /export - Export client data"
        ),
        "burn": (
            "🔥 *Command: /burn*\n\n"
            "*Usage:* /burn TOKEN_ID REASON\n\n"
            "*Description:* Mark a token as burned (permanently disabled) with a reason\n\n"
            "*Parameters:*\n"
            "- TOKEN_ID: The token to burn\n"
            "- REASON: The reason for burning the token\n\n"
            "*Example:*\n"
            "/burn NFX-ABC1234-Profile1 Account sharing detected"
        ),
        "burned": (
            "📊 *Command: /burned*\n\n"
            "*Usage:* /burned\n\n"
            "*Description:* List all burned tokens with their reasons and dates\n\n"
            "Shows the most recent burned tokens first, limited to 10 entries per page."
        ),
        "last10": (
            "📃 *Command: /last10*\n\n"
            "*Usage:* /last10\n\n"
            "*Description:* آخر 10 عمليات - Show the last 10 operations\n\n"
            "Displays a simple log of recent operations with icons:\n"
            "🆕 NEW - New client registration\n"
            "💳 PAID - Payment received\n"
            "⏳ EXT - Subscription extended\n"
            "🔥 BURN - Token burned\n\n"
            "Each entry shows all information in a single line for easy reading:\n"
            "- Operation type with icon\n"
            "- Token in a code block for easy copying\n"
            "- Date and time\n"
            "- Client name (when available)\n"
            "- Payment amount and other details\n\n"
            "Format example:\n"
            "1) 🆕 NEW `NFX-MYP7K29WQ-Profile1` 13-09-2025 10:12 - John Smith\n\n"
            "2) 💳 PAID `NFX-MYP7K29WQ-Profile1` 13-09-2025 12:35 - John Smith (10 TND)\n\n"
            "3) ⏳ EXT `NFX-MYP7K29WQ-Profile1` 20-09-2025 09:10 - John Smith (+30 days)"
        )
    }
    
    if command in command_help:
        try:
            await update.message.reply_text(command_help[command], parse_mode="Markdown")
        except Exception as e:
            # Fallback if Markdown parsing fails
            await update.message.reply_text(command_help[command])
    else:
        await update.message.reply_text(f"❌ Unknown command: {command}\n\nUse /help to see all available commands.")


# /new
@admin_required
async def new_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) != 4:
            await update.message.reply_text(
                "❌ Usage: /new FullName Email Profile Duration\n\n"
                "Duration examples:\n- 30 (days)\n- 2m (minutes)\n- 1h (hours)\n- 1d (1 day)"
            )
            return

        name, email, profile, duration_str = context.args
        token = generate_token(profile)

        # parse duration
        delta = parse_duration(duration_str)
        start_date = datetime.now()
        end_date = start_date + delta

        # save in DB
        add_client(token, name, email, profile, duration_str)

        # format display
        reply = (
            f"✅ *Registration successful!*\n\n"
            f"👤 {name}\n"
            f"📧 {email}\n"
            f"📺 {profile}\n"
            f"📅 Start: {start_date.strftime('%d-%m-%Y %H:%M')}\n"
            f"📅 End: {end_date.strftime('%d-%m-%Y %H:%M')}\n"
            f"⏱ Duration: {duration_str}\n"
            f"💰 Status: Unpaid\n\n"
            f"🔑 *Token:* `{token}`"
        )
        
        try:
            await update.message.reply_text(reply, parse_mode="Markdown")
        except Exception as e:
            # Fallback if Markdown parsing fails
            logger.error(f"Error sending formatted message: {e}")
            # Send without formatting
            simple_reply = (
                f"✅ Registration successful!\n\n"
                f"👤 {name}\n"
                f"📧 {email}\n"
                f"📺 {profile}\n"
                f"📅 Start: {start_date.strftime('%d-%m-%Y %H:%M')}\n"
                f"📅 End: {end_date.strftime('%d-%m-%Y %H:%M')}\n"
                f"⏱ Duration: {duration_str}\n"
                f"💰 Status: Unpaid\n\n"
                f"🔑 TOKEN: {token}\n"
                f"---------------------------"
            )
            await update.message.reply_text(simple_reply)

        # 🕒 جدولة إشعار عند الانتهاء
        scheduler.add_job(
            notify_expiration,
            "date",
            run_date=end_date,
            args=[context.application, YOUR_CHAT_ID, token, name, email, profile, end_date.strftime('%d-%m-%Y %H:%M')]
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        logger.error(f"Error in new_client: {e}", exc_info=True)

# /token
@admin_required
async def token_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /token TOKEN_ID")
        return

    token = context.args[0]
    client = get_client_by_token(token)
    if client:
        # Check if the client tuple has payment_amount (for backward compatibility)
        if len(client) >= 9:
            _, _, name, email, profile, start, end, status, payment_amount = client
        else:
            _, _, name, email, profile, start, end, status = client
            payment_amount = 0.0
        
        # Try to parse with time component first, then fall back to just date
        try:
            end_date = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                end_date = datetime.strptime(end, "%Y-%m-%d")
            except ValueError:
                logger.error(f"Could not parse end date: {end} for token {token}")
                end_date = datetime.now()  # Fallback
                
        days_left = (end_date - datetime.now()).days
        
        # Prepare payment info
        payment_info = ""
        if payment_amount and payment_amount > 0:
            payment_info = f"💵 Payment: {payment_amount}\n"
        
        reply = (
            f"🔎 *Client Details:*\n\n"
            f"🔑 Token: `{token}`\n"
            f"👤 Name: {name}\n"
            f"📧 Email: {email}\n"
            f"📺 Profile: {profile}\n"
            f"📅 Start: {start}\n"
            f"📅 End: {end}\n"
            f"💰 Status: {status}\n"
            f"{payment_info}"
            f"⏳ Days Left: {days_left}"
        )
    else:
        reply = "❌ Token not found."
    
    try:
        await update.message.reply_text(reply, parse_mode="Markdown")
    except Exception as e:
        # Fallback if Markdown parsing fails
        logger.error(f"Error sending formatted message: {e}")
        await update.message.reply_text(reply)

# /admin - Check if user is an admin
async def admin_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    first_name = update.effective_user.first_name or "User"
    from auth import is_admin, ADMIN_USERS
    
    if is_admin(user_id):
        await update.message.reply_text(
            f"✅ *Admin Access Granted*\n\n"
            f"Hello, {first_name}!\n\n"
            f"User ID: `{user_id}`\n"
            f"Username: @{username}\n\n"
            f"You have full administrative access to this bot.\n\n"
            f"Current admin IDs: `{', '.join(map(str, ADMIN_USERS))}`",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"❌ *Access Denied*\n\n"
            f"Hello, {first_name}!\n\n"
            f"User ID: `{user_id}`\n"
            f"Username: @{username}\n\n"
            f"This bot is restricted to administrators only.\n\n"
            f"To request access, please contact the bot owner with your User ID shown above.",
            parse_mode="Markdown"
        )

# /pay
@admin_required
async def pay_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /pay TOKEN_ID [AMOUNT]")
        return
    
    token = context.args[0]
    
    # Check if client exists
    client = get_client_by_token(token)
    if not client:
        await update.message.reply_text(f"❌ Token {token} not found.")
        return
    
    # Check if payment amount is provided
    payment_amount = None
    if len(context.args) > 1:
        try:
            payment_amount = float(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Payment amount must be a number.")
            return
    
    # Update status and payment amount
    update_status(token, "Paid", payment_amount)
    
    # Prepare response message
    if payment_amount is not None:
        await update.message.reply_text(
            f"💰 Token {token} updated → Paid ✅\n"
            f"Payment amount: {payment_amount}"
        )
    else:
        await update.message.reply_text(f"💰 Token {token} updated → Paid ✅")

# /extend
@admin_required
async def extend_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /extend TOKEN_ID DAYS")
        return
    
    token = context.args[0]
    
    # Validate days parameter
    try:
        days = int(context.args[1])
        if days <= 0:
            await update.message.reply_text("❌ Days must be a positive number")
            return
    except ValueError:
        await update.message.reply_text("❌ Days must be a valid number")
        return
    
    # Get client info before extending
    client = get_client_by_token(token)
    if not client:
        await update.message.reply_text("❌ Token not found.")
        return
    
    # Extend subscription
    new_end = extend_subscription(token, days)
    if new_end:
        # Format the message as requested
        reply = (
            f"➕ *Abonnement prolongé*\n\n"
            f"🔑 Token: `{token}`\n"
            f"+{days} jours → Nouvelle fin: {new_end.strftime('%d-%m-%Y')}"
        )
        
        try:
            await update.message.reply_text(reply, parse_mode="Markdown")
        except Exception as e:
            # Fallback if Markdown parsing fails
            logger.error(f"Error sending formatted message: {e}")
            # Send without formatting
            simple_reply = (
                f"➕ Abonnement prolongé\n\n"
                f"🔑 {token}\n"
                f"+{days} jours → Nouvelle fin: {new_end.strftime('%d-%m-%Y')}"
            )
            await update.message.reply_text(simple_reply)
    else:
        await update.message.reply_text("❌ Une erreur s'est produite lors de la prolongation.")


# /unpaid
@admin_required
async def unpaid_clients(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clients = get_unpaid_clients()
    if not clients:
        await update.message.reply_text("🎉 No unpaid clients!")
        return
    
    reply = "⚠️ *Unpaid Clients*\n\n"
    
    for i, (token, name, profile, start, end) in enumerate(clients):
        # Format end date for display
        try:
            end_date = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
            formatted_end = end_date.strftime("%d-%m-%Y")
        except ValueError:
            try:
                end_date = datetime.strptime(end, "%Y-%m-%d")
                formatted_end = end_date.strftime("%d-%m-%Y")
            except ValueError:
                formatted_end = end
        
        # Add client info with token in a code block for easy copying
        reply += f"👤 *{name}* - {profile}\n"
        reply += f"📅 Ends: {formatted_end}\n"
        reply += f"🔑 Token: `{token}`\n\n"
    
    try:
        await update.message.reply_text(reply, parse_mode="Markdown")
    except Exception as e:
        # Fallback if Markdown parsing fails
        logger.error(f"Error sending formatted message: {e}")
        
        # Simplified fallback message
        simple_reply = "⚠️ Unpaid Clients:\n\n"
        for token, name, profile, start, end in clients:
            simple_reply += f"🔑 {token} – {name} – {profile} (Ends: {end})\n\n"
        await update.message.reply_text(simple_reply)

# /stats
@admin_required 
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total, paid, unpaid, expired, burned = get_stats()
    reply = (
        f"📊 Subscription Stats:\n"
        f"👥 Total Clients: {total}\n"
        f"💰 Paid: {paid}\n"
        f"⚠️ Unpaid: {unpaid}\n"
        f"⏳ Expired: {expired}\n"
        f"🔥 Burned: {burned}"
    )
    await update.message.reply_text(reply)

# /expiring X
@admin_required
async def expiring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /expiring DAYS")
        return
    
    try:
        days = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ DAYS must be a number.")
        return

    clients = get_expiring_clients(days)
    if not clients:
        await update.message.reply_text(f"🎉 No clients expiring within {days} days.")
        return
    
    reply = f"⏳ *Clients expiring in {days} days:*\n\n"
    
    for token, name, profile, end, status, payment_amount in clients:
        # Format end date for display and calculate days remaining
        try:
            end_date = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
            formatted_end = end_date.strftime("%d-%m-%Y")
            days_remaining = (end_date - datetime.now()).days
            hours_remaining = int((end_date - datetime.now()).seconds / 3600)
        except ValueError:
            try:
                end_date = datetime.strptime(end, "%Y-%m-%d")
                formatted_end = end_date.strftime("%d-%m-%Y")
                days_remaining = (end_date - datetime.now()).days
                hours_remaining = int((end_date - datetime.now()).seconds / 3600)
            except ValueError:
                formatted_end = end
                days_remaining = 0
                hours_remaining = 0
        
        # Prepare remaining time text
        if days_remaining > 0:
            remaining_text = f"{days_remaining} days"
        elif hours_remaining > 0:
            remaining_text = f"{hours_remaining} hours"
        else:
            remaining_text = "less than 1 hour"
        
        # Add client info with token in a code block for easy copying
        reply += f"👤 *{name}* - {profile}\n"
        reply += f"📅 Ends: {formatted_end} - Status: *{status}*\n"
        reply += f"⏳ Remaining: {remaining_text}\n"
        
        # Add payment amount if available
        if payment_amount and payment_amount > 0:
            reply += f"💵 Payment: {payment_amount}\n"
            
        reply += f"🔑 Token: `{token}`\n\n"
    
    try:
        await update.message.reply_text(reply, parse_mode="Markdown")
    except Exception as e:
        # Fallback if Markdown parsing fails
        logger.error(f"Error sending formatted message: {e}")
        
        # Simplified fallback message
        simple_reply = f"⏳ Clients expiring in {days} days:\n\n"
        for token, name, profile, end, status, payment_amount in clients:
            # Calculate remaining time for fallback message
            try:
                end_date = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
                days_remaining = (end_date - datetime.now()).days
                hours_remaining = int((end_date - datetime.now()).seconds / 3600)
                
                if days_remaining > 0:
                    remaining = f"{days_remaining} days"
                elif hours_remaining > 0:
                    remaining = f"{hours_remaining} hours"
                else:
                    remaining = "<1 hour"
            except ValueError:
                try:
                    end_date = datetime.strptime(end, "%Y-%m-%d")
                    days_remaining = (end_date - datetime.now()).days
                    remaining = f"{days_remaining} days"
                except ValueError:
                    remaining = "unknown"
            
            payment_info = f", Payment: {payment_amount}" if payment_amount and payment_amount > 0 else ""
            simple_reply += f"🔑 {token} – {name} – {profile} (Ends: {end}, Remaining: {remaining}, Status: {status}{payment_info})\n\n"
        await update.message.reply_text(simple_reply)

# /search command
@admin_required
async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /search QUERY")
        return
    
    query = context.args[0]
    clients = search_clients(query)
    
    if not clients:
        await update.message.reply_text(f"🔎 No clients found matching '{query}'")
        return
    
    reply = f"🔎 *Search results for '{query}':*\n\n"
    for token, name, email, profile, start, end, status in clients:
        reply += f"👤 {name} ({profile}) - {status}\n"
        reply += f"🔑 Token: `{token}`\n\n"
    
    try:
        await update.message.reply_text(reply, parse_mode="Markdown")
    except Exception as e:
        # Fallback if Markdown parsing fails
        logger.error(f"Error sending formatted message: {e}")
        
        # Simplified fallback message
        simple_reply = f"🔎 Search results for '{query}':\n\n"
        for token, name, email, profile, start, end, status in clients:
            simple_reply += f"🔑 {token} - {name} ({profile}) - {status}\n\n"
        await update.message.reply_text(simple_reply)

# /last10 command to show recent operations in a concise format
@admin_required
async def last10_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get last 10 operations
    operations = get_recent_operations(10)

    if not operations:
        await update.message.reply_text("🔎 لا توجد أي عمليات حديثة.")
        return

    # Header
    reply = f"📃 *آخر {len(operations)} عمليات:*\n\n"

    # Icons for operation types
    op_icons = {
        "NEW": "🆕",
        "PAID": "💳",
        "EXT": "⏳",
        "BURN": "🔥"
    }

    for i, op in enumerate(operations, 1):
        # Format date
        formatted_date = op["date"].strftime("%d-%m-%Y %H:%M")

        # Operation type + icon
        op_type = op["type"]
        op_icon = op_icons.get(op_type, "💾")

        # Token (in code block for easy copy)
        token = f"`{op['token']}`"

        # Client name (normalize: replace "_" with space, title case)
        client_name = ""
        if op.get("client_name"):
            name = op["client_name"].replace("_", " ").title()
            client_name = f"- {name}"

        # Amount & details
        amount = f"({op['amount']} TND)" if op.get("amount", 0) > 0 else ""
        details = op.get("details", "")

        # Combine
        extra_info = " ".join([amount, details]).strip()

        # Final line
        reply += f"{i}) {op_icon} {op_type} {token} {formatted_date} {client_name} {extra_info}\n\n"

    # Send message
    try:
        await update.message.reply_text(reply, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Markdown error: {e}")
        await update.message.reply_text(reply.replace("`", ""))  # fallback without code blocks

# /burned command to list all burned tokens
@admin_required
async def list_burned_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    burned_tokens = get_burned_tokens()
    
    if not burned_tokens:
        await update.message.reply_text("🔎 No burned tokens found.")
        return
    
    reply = f"🔥 *Burned Tokens ({len(burned_tokens)}):*\n\n"
    
    for token, reason, date, name, email, profile in burned_tokens[:10]:  # Limit to 10 to avoid message too long
        reply += f"👤 {name}\n"
        reply += f"🔑 Token: `{token}`\n"
        reply += f"📅 {date}\n"
        reply += f"📜 {reason}\n\n"
    
    if len(burned_tokens) > 10:
        reply += f"\n...and {len(burned_tokens) - 10} more.\n"
    
    try:
        await update.message.reply_text(reply, parse_mode="Markdown")
    except Exception as e:
        # Fallback if Markdown parsing fails
        logger.error(f"Error sending formatted message: {e}")
        
        # Simplified fallback message
        simple_reply = f"🔥 Burned Tokens ({len(burned_tokens)}):\n\n"
        for token, reason, date, name, email, profile in burned_tokens[:10]:
            simple_reply += f"🔑 {token} - {name}\n"
            simple_reply += f"   📅 {date}\n"
            simple_reply += f"   📜 {reason}\n\n"
        
        if len(burned_tokens) > 10:
            simple_reply += f"\n...and {len(burned_tokens) - 10} more.\n"
            
        await update.message.reply_text(simple_reply)

# /burn command to mark tokens as burned
@admin_required
async def burn_token_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /burn TOKEN_ID REASON")
        return
    
    token = context.args[0]
    reason = ' '.join(context.args[1:])  # Combine all remaining args as the reason
    
    # Validate token format
    if not re.match(r'^NFX-[A-Z0-9]+-\w+$', token):
        await update.message.reply_text("❌ Invalid token format. Token should be in format NFX-XXXX-Profile")
        return
    
    # Get client info before burning
    client = get_client_by_token(token)
    if not client:
        await update.message.reply_text(f"❌ Token {token} not found.")
        return
    
    # Extract client info for the response
    _, _, name, email, profile, _, _, status = client[:8]  # First 8 fields
    
    # Burn the token
    success, message = burn_token(token, reason)
    
    if success:
        # Format the success message
        reply = (
            f"🔥 *Token Burned Successfully*\n\n"
            f"🔑 Token: `{token}`\n"
            f"👤 {name} ({email})\n"
            f"📺 Profile: {profile}\n"
            f"📜 Reason: {reason}\n"
            f"📅 Date: {datetime.now().strftime('%d-%m-%Y %H:%M')}"
        )
        
        try:
            await update.message.reply_text(reply, parse_mode="Markdown")
        except Exception as e:
            # Fallback if Markdown parsing fails
            logger.error(f"Error sending formatted message: {e}")
            # Send without formatting
            simple_reply = (
                f"🔥 Token Burned Successfully\n\n"
                f"🔑 {token}\n"
                f"👤 {name} ({email})\n"
                f"📺 Profile: {profile}\n"
                f"📜 Reason: {reason}\n"
                f"📅 Date: {datetime.now().strftime('%d-%m-%Y %H:%M')}"
            )
            await update.message.reply_text(simple_reply)
    else:
        await update.message.reply_text(f"❌ {message}")

# /export command
@admin_required
async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        format_type = "csv"  # Default format
        if context.args and context.args[0].lower() in ["csv", "excel"]:
            format_type = context.args[0].lower()
        
        await update.message.reply_text(f"⏳ Exporting client data to {format_type.upper()}...")
        
        # Get all clients from Google Sheets
        clients = get_all_clients()
        
        # Create exports directory if it doesn't exist
        os.makedirs('exports', exist_ok=True)
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format_type == "csv":
            import csv
            filepath = os.path.join('exports', f'netflix_clients_gsheet_{timestamp}.csv')
            
            with open(filepath, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['Token', 'Name', 'Email', 'Profile', 'Start Date', 'End Date', 'Status'])
                for client in clients:
                    writer.writerow(client)
                    
            await update.message.reply_document(
                document=open(filepath, 'rb'),
                filename=os.path.basename(filepath),
                caption="📊 Here's your exported client data in CSV format."
            )
        else:  # Excel
            import pandas as pd
            filepath = os.path.join('exports', f'netflix_clients_gsheet_{timestamp}.xlsx')
            
            df = pd.DataFrame(clients, columns=['Token', 'Name', 'Email', 'Profile', 'Start Date', 'End Date', 'Status'])
            df.to_excel(filepath, index=False)
            
            await update.message.reply_document(
                document=open(filepath, 'rb'),
                filename=os.path.basename(filepath),
                caption="📊 Here's your exported client data in Excel format."
            )
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error exporting data: {e}")
        logger.error(f"Error in export_data: {e}", exc_info=True)


# /start command
@admin_required
async def startapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = get_help_text()
    await update.message.reply_text(welcome_text)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    register_admin_check(app)

    # Load all existing clients and re-schedule jobs
    for token, name, email, profile, start, end, status in get_all_clients():
        try:
            end_date = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                end_date = datetime.strptime(end, "%Y-%m-%d")
            except:
                continue
        
        # إذا الاشتراك مزال ما انتهى
        if end_date > datetime.now():
            scheduler.add_job(
                notify_expiration,
                "date",
                run_date=end_date,
                args=[app, YOUR_CHAT_ID, token, name, email, profile, end]
            )

    # === Handlers
    app.add_handler(CommandHandler("start", startapp))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("new", new_client))
    app.add_handler(CommandHandler("token", token_info))
    app.add_handler(CommandHandler("admin", admin_check))
    app.add_handler(CommandHandler("pay", pay_client))
    app.add_handler(CommandHandler("extend", extend_client))
    app.add_handler(CommandHandler("unpaid", unpaid_clients))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("expiring", expiring))
    app.add_handler(CommandHandler("export", export_data))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("burn", burn_token_command))
    app.add_handler(CommandHandler("burned", list_burned_tokens))
    app.add_handler(CommandHandler("last10", last10_command))

    scheduler.start()
    app.run_polling()

if __name__ == "__main__":
    main()

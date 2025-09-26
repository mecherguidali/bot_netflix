# auth.py
import functools
import logging
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

logger = logging.getLogger(__name__)

# List of admin user IDs
ADMIN_USERS = []  # Will be populated from environment variables

def load_admin_users(admin_ids):
    """Load admin user IDs from a comma-separated string"""
    global ADMIN_USERS
    if not admin_ids:
        return
        
    try:
        # Parse comma-separated list of admin IDs
        admin_list = [int(id.strip()) for id in admin_ids.split(',') if id.strip()]
        ADMIN_USERS.extend(admin_list)
        logger.info(f"Loaded {len(admin_list)} admin users: {ADMIN_USERS}")
    except Exception as e:
        logger.error(f"Error loading admin users: {e}")

def admin_required(func):
    """Decorator to restrict commands to admin users only"""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        if not ADMIN_USERS:
            # If no admins are defined, log a warning but allow the command
            logger.warning(f"No admin users defined. User {user_id} allowed to use admin command by default.")
            return await func(update, context)
            
        if user_id in ADMIN_USERS:
            logger.info(f"Admin user {user_id} authorized to use command {func.__name__}")
            return await func(update, context)
        else:
            logger.warning(f"Unauthorized user {user_id} (@{username}) attempted to use admin command {func.__name__}")
            # No message is sent to the user, they'll just see the middleware message
            return None
            
    return wrapper

def is_admin(user_id):
    """Check if a user ID is an admin"""
    if not ADMIN_USERS:
        # If no admins are defined, consider everyone an admin
        logger.warning(f"No admin users defined. User {user_id} considered admin by default.")
        return True
        
    return user_id in ADMIN_USERS


async def admin_only_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Middleware to check if user is admin before processing any command"""
    # Skip updates that aren't messages or don't have a user
    if not update.effective_message or not update.effective_user:
        return True
        
    user_id = update.effective_user.id
    message_text = update.effective_message.text or ""
    
    # Allow only /admin command for all users to check their status
    if message_text.startswith("/admin"):
        return True
    
    # Check if user is admin
    if is_admin(user_id):
        return True
    
    # If not admin, send access denied message
    username = update.effective_user.username or "Unknown"
    logger.warning(f"Unauthorized access attempt by user {user_id} (@{username}) for command: {message_text}")
    
    # For first-time users trying to start the bot
    if message_text.startswith("/start"):
        try:
            await update.effective_message.reply_text(
                "⛔ *Access Denied*\n\n"
                f"User ID: `{user_id}` (@{username})\n\n"
                "This bot is restricted to administrators only.\n"
                "Use /admin to see your status and get your User ID.\n\n"
                "Please contact the bot owner to request access.",
                parse_mode="Markdown"
            )
        except Exception:
            # Fallback if Markdown parsing fails
            await update.effective_message.reply_text(
                "⛔ Access Denied\n\n"
                f"User ID: {user_id} (@{username})\n\n"
                "This bot is restricted to administrators only.\n"
                "Use /admin to see your status and get your User ID.\n\n"
                "Please contact the bot owner to request access."
            )
    else:
        # For other commands
        try:
            await update.effective_message.reply_text(
                "⛔ *Access Denied*\n\n"
                f"User ID: `{user_id}` (@{username})\n\n"
                "This bot is restricted to administrators only.\n"
                "Use /admin to see your status and get your User ID.",
                parse_mode="Markdown"
            )
        except Exception:
            # Fallback if Markdown parsing fails
            await update.effective_message.reply_text(
                "⛔ Access Denied\n\n"
                f"User ID: {user_id}\n\n"
                "This bot is restricted to administrators only.\n"
                "Use /admin to check your status."
            )
    
    # Return False to stop command processing
    return False


def register_admin_check(application):
    """Register the admin check middleware with the application"""
    application.add_handler(MessageHandler(filters.ALL, admin_only_middleware), group=-1)  # -1 makes it run first

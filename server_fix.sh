#!/bin/bash
# This script fixes the UnboundLocalError in bot.py

# Navigate to the bot directory
cd /root/dali/bot_netflix

# Create a backup of the original file
cp bot.py bot.py.backup

# Use sed to insert the start function before the main function
# This ensures the start function is defined before it's used
sed -i '/def main/i \
# /start command\
@admin_required\
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    welcome_text = get_help_text()\
    await update.message.reply_text(welcome_text)\
' bot.py

# Find and remove any duplicate start function definitions
# This pattern looks for the start function definition and removes it
# We're careful to only remove duplicates, not the one we just added
sed -i '0,/# \/start command/!{/# \/start command/,/await update.message.reply_text(welcome_text)/d}' bot.py

echo "Fix applied. Restart the bot with one of these commands:"
echo "python bot.py  # If running directly"
echo "sudo systemctl restart netflix-bot  # If running as a service"

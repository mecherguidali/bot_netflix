# Detailed Fix for UnboundLocalError

The error you're seeing is:
```
UnboundLocalError: cannot access local variable 'start' where it is not associated with a value
```

This occurs because the `start` function is not in scope when the `main()` function tries to use it. Here's how to fix it properly:

## Option 1: Move All Command Functions to the Top

1. Open your `bot.py` file on the server
2. Move the `start` function definition to be at the top of the file, with other command functions
3. Make sure all command functions are defined before the `main()` function

## Option 2: Fix the Specific Issue (Recommended)

1. SSH into your server:
   ```bash
   ssh username@your_server_ip
   ```

2. Navigate to your bot directory:
   ```bash
   cd /root/dali/bot_netflix
   ```

3. Open the bot.py file for editing:
   ```bash
   nano bot.py
   ```

4. Find the `main()` function (around line 621)

5. Before the `main()` function, make sure the `start` function is defined like this:
   ```python
   # /start command
   @admin_required
   async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
       welcome_text = get_help_text()
       await update.message.reply_text(welcome_text)
   ```

6. If there's another definition of the `start` function elsewhere in the file, remove it to avoid duplication

7. Save the file (in nano: Ctrl+O, then Enter, then Ctrl+X)

8. Restart the bot:
   ```bash
   # If running directly:
   python bot.py
   
   # If running as a service:
   sudo systemctl restart netflix-bot
   ```

## Option 3: Direct Fix on Server

If the above doesn't work, you can make a direct edit on the server:

```bash
# Navigate to the bot directory
cd /root/dali/bot_netflix

# Create a backup of the original file
cp bot.py bot.py.backup

# Use sed to insert the start function before the main function
sed -i '/def main/i \
# /start command\
@admin_required\
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    welcome_text = get_help_text()\
    await update.message.reply_text(welcome_text)\
' bot.py

# Remove any duplicate start function definitions if they exist
# (This is a simplified example - you might need to adjust this)
sed -i '/^# \/start command$/,/^    await update.message.reply_text(welcome_text)$/d' bot.py

# Restart the bot
sudo systemctl restart netflix-bot  # if using systemd
# or
python bot.py  # if running directly
```

## Verifying the Fix

After applying any of these fixes, you should verify that:

1. The `start` function is defined before the `main()` function
2. There are no duplicate definitions of the `start` function
3. The bot starts without errors

You can check the logs to confirm the bot is running correctly:
```bash
# If running as a service:
sudo journalctl -u netflix-bot -n 50

# If running directly:
# Check the console output
```

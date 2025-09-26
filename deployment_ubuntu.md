# Deployment Instructions for Netflix Bot on Ubuntu

This guide will help you deploy the Netflix Subscription Manager Bot on an Ubuntu server.

## Prerequisites

- Ubuntu server (18.04 LTS or newer)
- Python 3.8 or newer
- Git (to clone the repository)
- Access to the server via SSH

## Step 1: Update System Packages

```bash
sudo apt update
sudo apt upgrade -y
```

## Step 2: Install Required System Dependencies

```bash
sudo apt install -y python3-pip python3-venv git
```

## Step 3: Clone the Repository

```bash
mkdir -p ~/netflix_bot
cd ~/netflix_bot
# If you're using Git:
git clone https://your-repository-url.git .
# Or upload your files via SFTP/SCP
```

## Step 4: Set Up Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

## Step 5: Install Python Dependencies

```bash
pip install -r requirements.txt
# If requirements.txt doesn't exist, install dependencies manually:
pip install python-telegram-bot python-dotenv apscheduler
```

## Step 6: Configure Environment Variables

Create a `.env` file in the project directory:

```bash
nano .env
```

Add the following content (replace with your actual values):

```
BOT_TOKEN=your_telegram_bot_token_here
CHAT_ID=your_telegram_chat_id_here
ADMIN_IDS=123456789,987654321
```

Save and exit (Ctrl+X, then Y, then Enter).

## Step 7: Run the Bot

### Option 1: Run Directly

For testing purposes, you can run the bot directly:

```bash
python3 bot.py
```

### Option 2: Run as a Systemd Service (Recommended)

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/netflix-bot.service
```

Add the following content (adjust paths as needed):

```
[Unit]
Description=Netflix Subscription Manager Bot
After=network.target

[Service]
User=your_username
WorkingDirectory=/home/your_username/netflix_bot
ExecStart=/home/your_username/netflix_bot/venv/bin/python /home/your_username/netflix_bot/bot.py
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=netflix-bot

[Install]
WantedBy=multi-user.target
```

Save and exit.

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable netflix-bot
sudo systemctl start netflix-bot
```

Check the status:

```bash
sudo systemctl status netflix-bot
```

## Step 8: View Logs

To view the bot logs:

```bash
# For systemd service:
sudo journalctl -u netflix-bot -f

# For direct output:
tail -f netflix-bot.log  # If you've configured file logging
```

## Troubleshooting

### Common Issues

1. **Bot Not Responding**:
   - Check if the bot is running: `sudo systemctl status netflix-bot`
   - Verify your BOT_TOKEN is correct
   - Ensure the bot has been started in Telegram by messaging `/start` to it

2. **Permission Issues**:
   - Ensure the user running the bot has proper permissions to the directory and files
   - Check file permissions: `chmod 755 bot.py`

3. **Database Issues**:
   - Ensure the directory for the database file is writable
   - Check database file permissions

4. **Error: "cannot access local variable 'start' where it is not associated with a value"**:
   - This error occurs when the `start` function is not defined in the global scope
   - Make sure the `start` function is defined before it's used in the handlers

### Restarting the Bot

If you need to restart the bot after making changes:

```bash
sudo systemctl restart netflix-bot
```

## Updating the Bot

To update the bot with new code:

```bash
cd ~/netflix_bot
# Pull new code or upload new files
git pull  # If using Git

# Activate virtual environment if not already activated
source venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Restart the service
sudo systemctl restart netflix-bot
```

## Backup

Regularly backup your database file:

```bash
# Create a backup directory if it doesn't exist
mkdir -p ~/backups

# Backup the database file
cp ~/netflix_bot/clients.db ~/backups/clients_$(date +%Y%m%d).db
```

Consider setting up automatic backups using a cron job.

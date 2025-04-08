# Telegram Mandiri Finance Bot 💸🤖

A Telegram bot to parse bank statement Excel files, auto-categorize transactions, store them in MySQL, and generate spending charts.

## Features
- Upload Excel bank statements.
- Auto-categorize expenses by keywords.
- Store data in MySQL for persistence.
- Generate pie charts for expense breakdown.
- Cache chart images per user for faster access.

## Requirements
- Python 3.11 or higher
- MySQL database
- Telegram Bot API token

## Setup without Docker

### 1. Clone the Repository
```bash
git clone https://github.com/ardzz/mandiri-statement-bot.git
cd mandiri-statement-bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up MySQL Database
- Create a MySQL database and user.
- Run the alembic migrations to set up the database schema.
```bash
alembic upgrade head
```

### 4. Configure Environment Variables
- Create a `.env` file in the root directory and add your Telegram bot token and MySQL connection details.
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
MYSQL_HOST=localhost
...
```

### 5. Run the Bot
```bash
python run.py
```

## Setup with Docker
### 1. Clone the Repository
```bash
git clone https://github.com/ardzz/mandiri-statement-bot.git
cd mandiri-statement-bot
```

### 2. Build the Docker Image
```bash
docker compose build
```

### 3. Run the Docker Container
```bash
docker compose up -d
```
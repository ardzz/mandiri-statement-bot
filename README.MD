# 🏦 Mandiri Finance Telegram Bot 💸

A sophisticated Telegram bot that transforms your Mandiri bank statements into actionable financial insights. Upload encrypted Excel statements, get automatic categorization, detailed analytics, budget tracking, and beautiful visualizations.

## ✨ Key Features

### 📊 **Smart Financial Analysis**
- **Automatic Transaction Categorization** - AI-powered expense categorization with 11+ predefined categories
- **Advanced Analytics** - Comprehensive spending trends, patterns, and insights
- **Custom Time Range Reports** - Flexible date range analysis with preset options (7 days, 30 days, this month, etc.)
- **Visual Charts** - Balance trends, income vs expenses, and category breakdowns

### 💰 **Budget & Goal Management**
- **Budget Limits** - Set and track category-specific spending limits
- **Financial Goals** - Create and monitor savings targets and spending goals
- **Smart Alerts** - Get notified when approaching budget limits or unusual spending patterns

### 🔒 **Security & Privacy**
- **Encrypted Statement Processing** - Handles password-protected Mandiri e-Statements
- **Soft Delete Architecture** - Data recovery capabilities with proper deletion tracking
- **Local Processing** - Files processed locally and automatically deleted after analysis

### 🎯 **User Experience**
- **Interactive Menus** - Intuitive keyboard navigation and inline buttons
- **Flexible Date Input** - Natural language date parsing (e.g., "last month", "yesterday")
- **Real-time Processing** - Instant feedback and progress updates
- **Multi-format Support** - Text summaries and visual chart outputs

## 🚀 Quick Start

### Option 1: Docker Setup (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/ardzz/mandiri-statement-bot.git
   cd mandiri-statement-bot
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Launch with Docker**
   ```bash
   docker-compose up -d
   ```

4. **Initialize database**
   ```bash
   docker-compose exec bot python categories_seeder.py
   ```

### Option 2: Manual Setup

1. **Prerequisites**
   - Python 3.11+ 
   - MySQL 8.0+
   - Telegram Bot Token

2. **Installation**
   ```bash
   git clone https://github.com/ardzz/mandiri-statement-bot.git
   cd mandiri-statement-bot
   pip install -r requirements.txt
   ```

3. **Database Setup**
   ```bash
   # Configure your .env file first
   alembic upgrade head
   python categories_seeder.py
   ```

4. **Run the bot**
   ```bash
   python run.py
   ```

## ⚙️ Configuration

### Environment Variables (.env)
```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Database Configuration
DATABASE_URL=mysql+pymysql://user:password@host:port/database
MYSQL_ROOT_PASSWORD=your_root_password
MYSQL_DATABASE=finance_db
MYSQL_USER=finance_user  
MYSQL_PASSWORD=secure_password
MYSQL_PORT_FORWARD=3307
```

### Getting a Telegram Bot Token
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Use `/newbot` command and follow instructions
3. Copy the token to your `.env` file

## 📱 Bot Commands & Usage

### Essential Commands
- `/start` - Register and access main menu
- `/menu` - Return to main menu anytime
- `/categorize` - Auto-categorize uncategorized transactions
- `/trends` - View spending trends and category analysis
- `/recap` - Generate financial summaries

### Navigation Menu
```
📤 Upload E-statement Excel    📊 Recap
📈 Trends & Analysis          💰 Budget Management  
🎯 Financial Goals            🔔 Smart Insights
🏷️ Auto Categorize           ⚙️ Settings
📅 Update Birthdate          ❓ Help
```

## 📊 Transaction Categories

The bot automatically categorizes transactions into:

- **Food & Dining** - Restaurants, groceries, coffee shops
- **Shopping** - Online/retail stores, electronics, clothing  
- **Transportation** - Public transport, fuel, parking
- **Health & Fitness** - Medical expenses, gym, pharmacy
- **Entertainment** - Movies, games, recreation
- **Personal Care** - Grooming, beauty, wellness
- **Bills & Utilities** - Bank fees, subscriptions, insurance
- **Transfers & Banking** - ATM, deposits, investments
- **Income** - Salary, freelance, investment returns
- **Education** - Tuition, books, courses
- **Travel** - Accommodation, transportation, dining

## 🏗️ Architecture

### Tech Stack
- **Backend**: Python 3.12, SQLAlchemy ORM
- **Database**: MySQL 8.0 with Alembic migrations
- **Bot Framework**: python-telegram-bot v22
- **Charts**: Matplotlib, Seaborn, Pillow
- **File Processing**: msoffcrypto-tool, openpyxl
- **Deployment**: Docker & Docker Compose

### Project Structure
```
mandiri-statement-bot/
├── alembic/                 # Database migrations
├── bot/                     # Telegram bot handlers
│   ├── handlers/           # Command and message handlers
│   └── utils/              # Authentication and utilities
├── core/                   # Core business logic
│   ├── chart/              # Chart generation
│   ├── repository/         # Data access layer
│   ├── services/           # Business services
│   └── database.py         # Database models
├── config/                 # Configuration management
├── docker-compose.yml      # Container orchestration
└── categories_seeder.py    # Initial data setup
```

## 🔧 Development

### Running Tests
```bash
pytest
```

### Code Quality
```bash
# Linting
pylint $(find . -name "*.py" -not -path "./alembic/*")

# Type checking (if using mypy)
mypy .
```

### Database Operations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 📈 Features in Detail

### Smart Categorization
- Keyword-based transaction matching
- Learning from user corrections
- Support for custom categories
- Categorization statistics and reporting

### Advanced Analytics
- **Trend Analysis** - Spending patterns over time
- **Category Insights** - Detailed breakdowns by expense type
- **Budget Tracking** - Real-time budget vs actual comparisons
- **Goal Monitoring** - Progress tracking for financial objectives

### Flexible Reporting
- **Preset Ranges** - Quick access to common time periods
- **Custom Dates** - Natural language date input support
- **Multiple Formats** - Both visual charts and text summaries
- **Export Options** - Chart images and detailed statistics

## 🚨 Troubleshooting

### Common Issues

**Excel decryption fails**
- Ensure birth date is in DDMMYYYY format
- Verify the uploaded file is a genuine Mandiri e-Statement
- Check file isn't corrupted during upload

**Database connection errors**
- Verify DATABASE_URL format and credentials
- Ensure MySQL service is running
- Check network connectivity between bot and database

**Missing categories**
- Run `python categories_seeder.py` to initialize categories
- Verify database migrations are up to date

### Getting Help
- Check existing [Issues](https://github.com/ardzz/mandiri-statement-bot/issues)
- Create a new issue with detailed error information
- Include relevant logs and environment details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation as needed
- Ensure pylint passes without errors

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API wrapper
- [matplotlib](https://matplotlib.org/) - Chart generation
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
- [msoffcrypto-tool](https://github.com/nolze/msoffcrypto-tool) - Excel decryption

## 📊 Project Stats

![GitHub issues](https://img.shields.io/github/issues/ardzz/mandiri-statement-bot)
![GitHub forks](https://img.shields.io/github/forks/ardzz/mandiri-statement-bot)
![GitHub stars](https://img.shields.io/github/stars/ardzz/mandiri-statement-bot)
![GitHub license](https://img.shields.io/github/license/ardzz/mandiri-statement-bot)

---
Made with ❤️ by [ardzz](https://github.com/ardzz)

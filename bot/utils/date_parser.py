from datetime import datetime, date, timedelta
from typing import Optional, Tuple, List
import re
from calendar import monthrange


class DateParseError(Exception):
    """Custom exception for date parsing errors with suggestions."""

    def __init__(self, message: str, suggestions: List[str] = None):
        self.message = message
        self.suggestions = suggestions or []
        super().__init__(self.message)


def parse_flexible_date(date_str: str) -> date:
    """
    Parse various date formats and return standardized date object.

    Supported formats:
    - YYYY-MM-DD (ISO format)
    - DD/MM/YYYY, DD-MM-YYYY
    - Month DD, YYYY (e.g., "Jan 15, 2024")
    - DD Month YYYY (e.g., "15 Jan 2024")
    - Relative dates: today, yesterday, tomorrow
    - Relative periods: last week, last month, this month, etc.

    Args:
        date_str: Input date string

    Returns:
        datetime.date object

    Raises:
        DateParseError: If date cannot be parsed with helpful suggestions
    """
    if not date_str or not isinstance(date_str, str):
        raise DateParseError(
            "Please provide a valid date",
            ["2024-12-25", "25/12/2024", "Dec 25, 2024", "yesterday", "last week"]
        )

    date_str = date_str.strip().lower()
    today = date.today()

    # Handle relative dates
    if date_str in ['today']:
        return today
    elif date_str in ['yesterday']:
        return today - timedelta(days=1)
    elif date_str in ['tomorrow']:
        return today + timedelta(days=1)
    elif date_str in ['last week']:
        return today - timedelta(weeks=1)
    elif date_str in ['last month']:
        if today.month == 1:
            return today.replace(year=today.year - 1, month=12)
        else:
            # Handle month with different number of days
            try:
                return today.replace(month=today.month - 1)
            except ValueError:
                # Handle case where current day doesn't exist in previous month
                last_month = today.month - 1 if today.month > 1 else 12
                last_year = today.year if today.month > 1 else today.year - 1
                last_day = monthrange(last_year, last_month)[1]
                return date(last_year, last_month, min(today.day, last_day))
    elif date_str in ['this month']:
        return today.replace(day=1)
    elif date_str in ['last year']:
        return today.replace(year=today.year - 1)

    # Try different date formats
    formats_to_try = [
        # ISO format
        ('%Y-%m-%d', 'YYYY-MM-DD'),
        # European formats
        ('%d/%m/%Y', 'DD/MM/YYYY'),
        ('%d-%m-%Y', 'DD-MM-YYYY'),
        ('%d.%m.%Y', 'DD.MM.YYYY'),
        # American formats
        ('%m/%d/%Y', 'MM/DD/YYYY'),
        ('%m-%d-%Y', 'MM-DD-YYYY'),
        # Natural language formats
        ('%b %d, %Y', 'Month DD, YYYY'),
        ('%B %d, %Y', 'Month DD, YYYY'),
        ('%d %b %Y', 'DD Month YYYY'),
        ('%d %B %Y', 'DD Month YYYY'),
        # Short year formats
        ('%d/%m/%y', 'DD/MM/YY'),
        ('%d-%m-%y', 'DD-MM-YY'),
        ('%Y/%m/%d', 'YYYY/MM/DD'),
    ]

    # Normalize the input for better parsing
    normalized_str = date_str.replace(',', '').strip()

    for fmt, description in formats_to_try:
        try:
            parsed_date = datetime.strptime(normalized_str, fmt).date()
            # Validate reasonable date range (not too far in future/past)
            if parsed_date.year < 2000 or parsed_date.year > 2050:
                continue
            return parsed_date
        except ValueError:
            continue

    # If no format worked, provide helpful suggestions
    suggestions = [
        f"{today.strftime('%Y-%m-%d')} (today)",
        f"{today.strftime('%d/%m/%Y')} (today in DD/MM/YYYY)",
        f"{today.strftime('%b %d, %Y')} (today in natural format)",
        "yesterday",
        "last week",
        "last month"
    ]

    raise DateParseError(
        f"Could not understand date format: '{date_str}'",
        suggestions
    )


def calculate_preset_dates(preset_type: str) -> Tuple[date, date, str]:
    """
    Calculate start and end dates for preset ranges.

    Args:
        preset_type: The preset identifier (e.g., 'preset_7d', 'preset_30d')

    Returns:
        Tuple of (start_date, end_date, description)

    Raises:
        ValueError: If preset type is unknown
    """
    today = date.today()

    if preset_type == "preset_7d":
        return today - timedelta(days=7), today, "Last 7 Days"
    elif preset_type == "preset_30d":
        return today - timedelta(days=30), today, "Last 30 Days"
    elif preset_type == "preset_this_month":
        return today.replace(day=1), today, "This Month"
    elif preset_type == "preset_last_month":
        if today.month == 1:
            last_month_start = date(today.year - 1, 12, 1)
            last_month_end = date(today.year - 1, 12, 31)
        else:
            last_month_start = date(today.year, today.month - 1, 1)
            # Get last day of previous month
            last_month_end = today.replace(day=1) - timedelta(days=1)
        return last_month_start, last_month_end, "Last Month"
    elif preset_type == "preset_this_year":
        return date(today.year, 1, 1), today, "This Year"
    elif preset_type == "preset_last_year":
        return date(today.year - 1, 1, 1), date(today.year - 1, 12, 31), "Last Year"

    raise ValueError(f"Unknown preset type: {preset_type}")


def get_preset_transaction_count(preset_type: str, user_id: int) -> Optional[int]:
    """
    Get the number of transactions for a specific preset range.

    Args:
        preset_type: The preset identifier
        user_id: User's ID

    Returns:
        Number of transactions in the preset range, or None if error
    """
    try:
        from core.database import Session
        from core.repository.TransactionRepository import TransactionRepository
        from core.repository.BankAccountRepository import BankAccountRepository

        start_date, end_date, _ = calculate_preset_dates(preset_type)

        session = Session()
        bank_account_repo = BankAccountRepository(session)
        bank_account = bank_account_repo.get_by_telegram_id(str(user_id))

        if not bank_account:
            return None

        trx_repo = TransactionRepository(session)
        transactions = trx_repo.get_transactions_by_date_range(bank_account.id, start_date, end_date)

        return len(transactions) if transactions else 0

    except Exception:
        return None


def get_date_range_suggestions(user_min_date: Optional[date] = None, user_max_date: Optional[date] = None) -> List[str]:
    """
    Generate smart date range suggestions based on user's transaction history.

    Args:
        user_min_date: Earliest transaction date for the user
        user_max_date: Latest transaction date for the user

    Returns:
        List of suggested date ranges with descriptions
    """
    today = date.today()
    suggestions = []

    # Common relative periods
    suggestions.extend([
        "last 7 days → 7 days ago to today",
        "last 30 days → 30 days ago to today",
        "this month → first day of current month to today",
        "last month → entire previous month",
        "this year → January 1st to today"
    ])

    # Add user-specific suggestions if we have their data
    if user_min_date and user_max_date:
        suggestions.extend([
            f"all time → {user_min_date.strftime('%b %d, %Y')} to {user_max_date.strftime('%b %d, %Y')}",
            f"recent data → {user_max_date.strftime('%b %d, %Y')} (latest transaction)"
        ])

    return suggestions


def validate_date_range(start_date: date, end_date: date, user_min_date: Optional[date] = None,
                        user_max_date: Optional[date] = None) -> Tuple[bool, str]:
    """
    Validate a date range against user's transaction history and logical constraints.

    Args:
        start_date: Start date of the range
        end_date: End date of the range
        user_min_date: User's earliest transaction date
        user_max_date: User's latest transaction date

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Basic validation
    if start_date > end_date:
        return False, "❌ Start date cannot be after end date"

    # Check if range is too large (performance consideration)
    days_diff = (end_date - start_date).days
    if days_diff > 365 * 2:  # More than 2 years
        return False, f"⚠️ Date range is very large ({days_diff} days). This might take a while to process."

    # Validate against user's transaction history
    if user_min_date and user_max_date:
        if end_date < user_min_date:
            return False, f"❌ End date is before your first transaction ({user_min_date.strftime('%b %d, %Y')})"

        if start_date > user_max_date:
            return False, f"❌ Start date is after your last transaction ({user_max_date.strftime('%b %d, %Y')})"

        # Warn if dates are outside user's range but still allow
        warnings = []
        if start_date < user_min_date:
            warnings.append(f"⚠️ Start date is before your first transaction ({user_min_date.strftime('%b %d, %Y')})")
        if end_date > user_max_date:
            warnings.append(f"⚠️ End date is after your last transaction ({user_max_date.strftime('%b %d, %Y')})")

        if warnings:
            return True, "\n".join(warnings) + "\n\n✅ Proceeding anyway..."

    return True, "✅ Date range looks good!"


def format_date_range_display(start_date: date, end_date: date) -> str:
    """
    Format date range for user-friendly display.

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        Formatted string representation
    """
    days_diff = (end_date - start_date).days

    if days_diff == 0:
        return f"📅 {start_date.strftime('%B %d, %Y')} (single day)"
    elif days_diff <= 7:
        return f"📅 {start_date.strftime('%b %d')} → {end_date.strftime('%b %d, %Y')} ({days_diff + 1} days)"
    elif days_diff <= 31:
        return f"📅 {start_date.strftime('%b %d')} → {end_date.strftime('%b %d, %Y')} (~{days_diff + 1} days)"
    else:
        return f"📅 {start_date.strftime('%b %d, %Y')} → {end_date.strftime('%b %d, %Y')} (~{days_diff + 1} days)"


def get_user_transaction_date_bounds(user_id: int) -> Tuple[Optional[date], Optional[date]]:
    """
    Get the earliest and latest transaction dates for a user.

    Args:
        user_id: User's ID

    Returns:
        Tuple of (min_date, max_date) or (None, None) if no transactions
    """
    try:
        from core.database import Session
        from core.repository.TransactionRepository import TransactionRepository
        from core.repository.BankAccountRepository import BankAccountRepository

        session = Session()
        bank_account_repo = BankAccountRepository(session)
        bank_account = bank_account_repo.get_by_telegram_id(str(user_id))

        if not bank_account:
            return None, None

        trx_repo = TransactionRepository(session)
        min_date, max_date = trx_repo.get_user_date_bounds(bank_account.id)

        return min_date, max_date

    except Exception:
        return None, None
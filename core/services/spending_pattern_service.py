from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract

from core.database import Session as DBSession, SpendingPattern, RecurringTransaction, PatternAnomaly
from core.repository.TransactionRepository import TransactionRepository
from core.repository.BankAccountRepository import BankAccountRepository


class SpendingPatternService:
    """Service for analyzing spending patterns and detecting recurring transactions."""

    def __init__(self):
        self.session = DBSession()
        self.transaction_repo = TransactionRepository(self.session)
        self.account_repo = BankAccountRepository(self.session)

    def analyze_daily_patterns(self, user_id: int) -> Dict:
        """Analyze daily spending patterns."""
        account = self.account_repo.get_by_telegram_id(str(user_id))
        if not account:
            return {'error': 'Account not found'}

        # Get transactions from last 90 days for better pattern detection
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=90)

        transactions = self.transaction_repo.get_transactions_by_date_range(
            account.id, start_date, end_date
        )

        if not transactions:
            return {'error': 'No transactions found'}

        # Group by day of week and hour
        daily_patterns = defaultdict(lambda: {'amounts': [], 'count': 0})
        hourly_patterns = defaultdict(lambda: {'amounts': [], 'count': 0})
        detailed_transactions = []

        for t in transactions:
            if t.outgoing and t.outgoing > 0:
                # Day of week (0=Monday, 6=Sunday)
                day_name = t.date.strftime('%A')
                daily_patterns[day_name]['amounts'].append(t.outgoing)
                daily_patterns[day_name]['count'] += 1

                # Hour of day
                hour = t.date.hour
                hourly_patterns[hour]['amounts'].append(t.outgoing)
                hourly_patterns[hour]['count'] += 1

                # Collect detailed transaction info for later display
                detailed_transactions.append({
                    'amount': t.outgoing,
                    'merchant': t.description,
                    'category': self._get_transaction_category(t),
                    'time': t.date.strftime('%Y-%m-%d %H:%M')
                })

        # Calculate statistics
        daily_stats = {}
        for day, data in daily_patterns.items():
            if data['amounts']:
                daily_stats[day] = {
                    'average_amount': np.mean(data['amounts']),
                    'total_amount': sum(data['amounts']),
                    'transaction_count': data['count'],
                    'median_amount': np.median(data['amounts']),
                    'std_deviation': np.std(data['amounts'])
                }

        hourly_stats = {}
        for hour, data in hourly_patterns.items():
            if data['amounts']:
                hourly_stats[hour] = {
                    'average_amount': np.mean(data['amounts']),
                    'total_amount': sum(data['amounts']),
                    'transaction_count': data['count']
                }

        # Sort and keep top 5 transactions by amount
        top_transactions = sorted(
            detailed_transactions,
            key=lambda x: x['amount'],
            reverse=True
        )[:5]

        # Store patterns in database
        self._store_daily_patterns(account.id, daily_stats, hourly_stats)

        return {
            'daily_patterns': daily_stats,
            'hourly_patterns': hourly_stats,
            'top_transactions': top_transactions,
            'analysis_period': f"{start_date} to {end_date}",
            'total_transactions': len(transactions)
        }

    def analyze_weekly_patterns(self, user_id: int) -> Dict:
        """Analyze weekly spending patterns."""
        account = self.account_repo.get_by_telegram_id(str(user_id))
        if not account:
            return {'error': 'Account not found'}

        # Get transactions from last 12 weeks
        end_date = datetime.now().date()
        start_date = end_date - timedelta(weeks=12)

        transactions = self.transaction_repo.get_transactions_by_date_range(
            account.id, start_date, end_date
        )

        if not transactions:
            return {'error': 'No transactions found'}

        # Group by week
        weekly_spending = defaultdict(lambda: {'amounts': [], 'dates': []})

        for t in transactions:
            if t.outgoing and t.outgoing > 0:
                # Get week number
                week_key = t.date.strftime('%Y-W%U')
                weekly_spending[week_key]['amounts'].append(t.outgoing)
                weekly_spending[week_key]['dates'].append(t.date.date())

        # Calculate weekly statistics
        weekly_stats = {}
        for week, data in weekly_spending.items():
            if data['amounts']:
                weekly_stats[week] = {
                    'total_spending': sum(data['amounts']),
                    'average_transaction': np.mean(data['amounts']),
                    'transaction_count': len(data['amounts']),
                    'first_date': min(data['dates']),
                    'last_date': max(data['dates'])
                }

        # Identify trends
        weekly_totals = [stats['total_spending'] for stats in weekly_stats.values()]
        if len(weekly_totals) >= 4:
            trend = self._calculate_trend(weekly_totals)
        else:
            trend = 'insufficient_data'

        # Store patterns
        self._store_weekly_patterns(account.id, weekly_stats)

        return {
            'weekly_patterns': weekly_stats,
            'trend': trend,
            'average_weekly_spending': np.mean(weekly_totals) if weekly_totals else 0,
            'analysis_period': f"{start_date} to {end_date}"
        }

    def analyze_monthly_patterns(self, user_id: int) -> Dict:
        """Analyze monthly spending patterns."""
        account = self.account_repo.get_by_telegram_id(str(user_id))
        if not account:
            return {'error': 'Account not found'}

        # Get transactions from last 12 months
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=365)

        transactions = self.transaction_repo.get_transactions_by_date_range(
            account.id, start_date, end_date
        )

        if not transactions:
            return {'error': 'No transactions found'}

        # Group by month
        monthly_spending = defaultdict(lambda: {'amounts': [], 'categories': defaultdict(float)})

        for t in transactions:
            if t.outgoing and t.outgoing > 0:
                month_key = t.date.strftime('%Y-%m')
                monthly_spending[month_key]['amounts'].append(t.outgoing)

                # Group by category if available
                category = self._get_transaction_category(t)
                monthly_spending[month_key]['categories'][category] += t.outgoing

        # Calculate monthly statistics
        monthly_stats = {}
        for month, data in monthly_spending.items():
            if data['amounts']:
                monthly_stats[month] = {
                    'total_spending': sum(data['amounts']),
                    'average_transaction': np.mean(data['amounts']),
                    'transaction_count': len(data['amounts']),
                    'top_categories': dict(sorted(
                        data['categories'].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5])
                }

        # Identify seasonal patterns
        seasonal_analysis = self._analyze_seasonal_patterns(monthly_stats)

        # Store patterns
        self._store_monthly_patterns(account.id, monthly_stats)

        return {
            'monthly_patterns': monthly_stats,
            'seasonal_analysis': seasonal_analysis,
            'analysis_period': f"{start_date} to {end_date}"
        }

    def detect_recurring_transactions(self, user_id: int) -> List[Dict]:
        """Detect recurring transactions like subscriptions."""
        account = self.account_repo.get_by_telegram_id(str(user_id))
        if not account:
            return []

        # Get transactions from last 6 months
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=180)

        transactions = self.transaction_repo.get_transactions_by_date_range(
            account.id, start_date, end_date
        )

        if not transactions:
            return []

        # Group similar transactions
        merchant_groups = defaultdict(list)

        for t in transactions:
            if t.outgoing and t.outgoing > 0:
                # Normalize merchant name for grouping
                normalized_desc = self._normalize_description(t.description)
                merchant_groups[normalized_desc].append(t)

        recurring_transactions = []

        for merchant, merchant_transactions in merchant_groups.items():
            if len(merchant_transactions) >= 3:  # At least 3 occurrences
                pattern = self._analyze_transaction_frequency(merchant_transactions)

                if pattern['is_recurring']:
                    recurring_transactions.append({
                        'merchant': merchant,
                        'frequency': pattern['frequency'],
                        'average_amount': pattern['average_amount'],
                        'last_transaction': pattern['last_transaction'],
                        'next_expected': pattern['next_expected'],
                        'confidence': pattern['confidence'],
                        'transaction_count': len(merchant_transactions)
                    })

                    # Store in database
                    self._store_recurring_transaction(account.id, pattern, merchant)

        return recurring_transactions

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from a series of values."""
        if len(values) < 2:
            return 'insufficient_data'

        # Simple linear regression slope
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]

        if slope > np.mean(values) * 0.05:  # 5% increase
            return 'increasing'
        elif slope < -np.mean(values) * 0.05:  # 5% decrease
            return 'decreasing'
        else:
            return 'stable'

    def _get_transaction_category(self, transaction) -> str:
        """Get category name for a transaction."""
        if hasattr(transaction, 'category') and transaction.category:
            return transaction.category.name
        return 'Uncategorized'

    def _normalize_description(self, description: str) -> str:
        """Normalize transaction description for grouping."""
        # Remove common words, numbers, dates
        import re
        normalized = re.sub(r'\d+', '', description.lower())
        normalized = re.sub(r'[^\w\s]', '', normalized)
        return normalized.strip()[:50]  # Limit length

    def _analyze_transaction_frequency(self, transactions: List) -> Dict:
        """Analyze frequency pattern of similar transactions."""
        amounts = [t.outgoing for t in transactions]
        dates = [t.date.date() for t in transactions]

        # Sort by date
        sorted_transactions = sorted(zip(dates, amounts))
        dates, amounts = zip(*sorted_transactions)

        # Calculate intervals between transactions
        intervals = []
        for i in range(1, len(dates)):
            interval = (dates[i] - dates[i - 1]).days
            intervals.append(interval)

        if not intervals:
            return {'is_recurring': False}

        # Check for recurring pattern
        avg_interval = np.mean(intervals)
        std_interval = np.std(intervals)

        # Consider recurring if standard deviation is low relative to mean
        consistency = 1 - (std_interval / avg_interval) if avg_interval > 0 else 0

        is_recurring = consistency > 0.7 and len(transactions) >= 3

        # Determine frequency type
        if avg_interval <= 7:
            frequency_type = 'weekly'
        elif avg_interval <= 31:
            frequency_type = 'monthly'
        elif avg_interval <= 93:
            frequency_type = 'quarterly'
        else:
            frequency_type = 'irregular'

        # Predict next transaction
        if is_recurring:
            next_expected = dates[-1] + timedelta(days=int(avg_interval))
        else:
            next_expected = None

        return {
            'is_recurring': is_recurring,
            'frequency': frequency_type,
            'average_amount': np.mean(amounts),
            'confidence': consistency,
            'last_transaction': dates[-1],
            'next_expected': next_expected,
            'average_interval_days': avg_interval
        }

    def _store_daily_patterns(self, user_id: int, daily_stats: Dict, hourly_stats: Dict):
        """Store daily patterns in database."""
        # Clear existing patterns
        self.session.query(SpendingPattern).filter(
            SpendingPattern.user_id == user_id,
            SpendingPattern.pattern_type == 'daily'
        ).delete()

        # Store daily patterns
        for day, stats in daily_stats.items():
            pattern = SpendingPattern(
                user_id=user_id,
                pattern_type='daily',
                pattern_key=day,
                average_amount=stats['average_amount'],
                transaction_count=stats['transaction_count'],
                confidence_score=min(1.0, stats['transaction_count'] / 10),  # Higher with more data
                variance=stats['std_deviation']
            )
            self.session.add(pattern)

        self.session.commit()

    def _store_weekly_patterns(self, user_id: int, weekly_stats: Dict):
        """Store weekly patterns in database."""
        # Clear existing weekly patterns
        self.session.query(SpendingPattern).filter(
            SpendingPattern.user_id == user_id,
            SpendingPattern.pattern_type == 'weekly'
        ).delete()

        # Store weekly patterns
        for week, stats in weekly_stats.items():
            pattern = SpendingPattern(
                user_id=user_id,
                pattern_type='weekly',
                pattern_key=week,
                average_amount=stats['average_transaction'],
                transaction_count=stats['transaction_count'],
                confidence_score=min(1.0, stats['transaction_count'] / 20),  # Higher with more data
                variance=0  # Could calculate variance if needed
            )
            self.session.add(pattern)

        self.session.commit()

    def _store_monthly_patterns(self, user_id: int, monthly_stats: Dict):
        """Store monthly patterns in database."""
        # Clear existing monthly patterns
        self.session.query(SpendingPattern).filter(
            SpendingPattern.user_id == user_id,
            SpendingPattern.pattern_type == 'monthly'
        ).delete()

        # Store monthly patterns
        for month, stats in monthly_stats.items():
            pattern = SpendingPattern(
                user_id=user_id,
                pattern_type='monthly',
                pattern_key=month,
                average_amount=stats['average_transaction'],
                transaction_count=stats['transaction_count'],
                confidence_score=min(1.0, stats['transaction_count'] / 30),  # Higher with more data
                variance=0  # Could calculate variance if needed
            )
            self.session.add(pattern)

        self.session.commit()

    def _store_recurring_transaction(self, user_id: int, pattern: Dict, merchant: str):
        """Store recurring transaction pattern in database."""
        # Check if already exists
        existing = self.session.query(RecurringTransaction).filter(
            RecurringTransaction.user_id == user_id,
            RecurringTransaction.merchant_pattern == merchant
        ).first()

        if existing:
            # Update existing
            existing.average_amount = pattern['average_amount']
            existing.confidence_score = pattern['confidence']
            existing.last_transaction_date = pattern['last_transaction']
            existing.next_expected_date = pattern['next_expected']
        else:
            # Create new
            recurring = RecurringTransaction(
                user_id=user_id,
                merchant_pattern=merchant,
                frequency_type=pattern['frequency'],
                average_amount=pattern['average_amount'],
                confidence_score=pattern['confidence'],
                last_transaction_date=pattern['last_transaction'],
                next_expected_date=pattern['next_expected']
            )
            self.session.add(recurring)

        self.session.commit()

    def _analyze_seasonal_patterns(self, monthly_stats: Dict) -> Dict:
        """Analyze seasonal spending patterns."""
        # Group by month of year
        seasonal_data = defaultdict(list)

        for month_key, stats in monthly_stats.items():
            month_num = int(month_key.split('-')[1])
            seasonal_data[month_num].append(stats['total_spending'])

        # Calculate seasonal averages
        seasonal_averages = {}
        for month_num, amounts in seasonal_data.items():
            if amounts:
                seasonal_averages[month_num] = {
                    'average_spending': np.mean(amounts),
                    'data_points': len(amounts)
                }

        return seasonal_averages

    def __del__(self):
        """Close session when service is destroyed."""
        if hasattr(self, 'session'):
            self.session.close()
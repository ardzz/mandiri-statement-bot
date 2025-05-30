from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import numpy as np
from core.database import Session, SpendingAlert
from core.repository.TransactionRepository import TransactionRepository
from core.repository.BudgetRepository import BudgetRepository, GoalRepository, AlertRepository
from core.repository.BankAccountRepository import BankAccountRepository


class FinancialAnalysisService:
    """Service for advanced financial analysis and insights."""

    def __init__(self):
        self.session = Session()
        self.transaction_repo = TransactionRepository(self.session)
        self.budget_repo = BudgetRepository(self.session)
        self.goal_repo = GoalRepository(self.session)
        self.alert_repo = AlertRepository(self.session)
        self.account_repo = BankAccountRepository(self.session)

    def get_spending_trends(self, user_id: int, period: str = 'monthly') -> Dict:
        """Get spending trends for a user."""
        account = self.account_repo.get_by_telegram_id(str(user_id))
        if not account:
            return {}

        transactions = self.transaction_repo.get_all_transactions(account.id)

        if not transactions:
            return {}

        # Group by period
        period_data = defaultdict(lambda: {'spending': 0, 'income': 0, 'count': 0})

        for t in transactions:
            if period == 'daily':
                key = t.date.strftime('%Y-%m-%d')
            elif period == 'weekly':
                key = t.date.strftime('%Y-W%U')
            else:  # monthly
                key = t.date.strftime('%Y-%m')

            period_data[key]['spending'] += abs(t.outgoing or 0)
            period_data[key]['income'] += t.incoming or 0
            period_data[key]['count'] += 1

        return dict(period_data)

    def get_category_insights(self, user_id: int) -> Dict:
        """Get insights about spending by category."""
        account = self.account_repo.get_by_telegram_id(str(user_id))
        if not account:
            return {}

        # Get transactions from last 30 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)

        recent_transactions = self.transaction_repo.get_transactions_by_date_range(
            account.id, start_date, end_date
        )

        # Get transactions from previous 30 days for comparison
        prev_end_date = start_date
        prev_start_date = prev_end_date - timedelta(days=30)

        prev_transactions = self.transaction_repo.get_transactions_by_date_range(
            account.id, prev_start_date, prev_end_date
        )

        # Analyze categories
        recent_category_spending = defaultdict(float)
        prev_category_spending = defaultdict(float)

        for t in recent_transactions:
            category = self._get_transaction_category(t)
            recent_category_spending[category] += abs(t.outgoing or 0)

        for t in prev_transactions:
            category = self._get_transaction_category(t)
            prev_category_spending[category] += abs(t.outgoing or 0)

        # Calculate changes
        insights = {}
        for category in set(list(recent_category_spending.keys()) + list(prev_category_spending.keys())):
            recent = recent_category_spending[category]
            previous = prev_category_spending[category]

            change_pct = ((recent - previous) / previous * 100) if previous > 0 else 0

            insights[category] = {
                'recent_spending': recent,
                'previous_spending': previous,
                'change_percentage': change_pct,
                'trend': 'increasing' if change_pct > 10 else 'decreasing' if change_pct < -10 else 'stable'
            }

        return insights

    def check_budget_status(self, user_id: int) -> Dict:
        """Check budget status and generate alerts if needed."""
        account = self.account_repo.get_by_telegram_id(str(user_id))
        if not account:
            return {}

        budgets = self.budget_repo.get_user_budgets(account.id)
        if not budgets:
            return {}

        # Get current month spending
        current_month = datetime.now().replace(day=1).date()
        end_of_month = (current_month.replace(month=current_month.month + 1)
                        if current_month.month < 12
                        else current_month.replace(year=current_month.year + 1, month=1)) - timedelta(days=1)

        current_month_transactions = self.transaction_repo.get_transactions_by_date_range(
            account.id, current_month, end_of_month
        )

        # Calculate spending by category
        category_spending = defaultdict(float)
        for t in current_month_transactions:
            category = self._get_transaction_category(t)
            category_spending[category] += abs(t.outgoing or 0)

        budget_status = {}
        for budget in budgets:
            spent = category_spending[budget.category_name]
            limit = budget.monthly_limit
            usage_pct = (spent / limit * 100) if limit > 0 else 0

            status = 'safe'
            if usage_pct >= 100:
                status = 'exceeded'
            elif usage_pct >= 80:
                status = 'warning'

            budget_status[budget.category_name] = {
                'spent': spent,
                'limit': limit,
                'usage_percentage': usage_pct,
                'status': status,
                'remaining': max(0, limit - spent)
            }

            # Create alerts for budget issues
            if status == 'exceeded' and not self._alert_exists(account.id, 'budget_exceeded', budget.category_name):
                self.alert_repo.create_alert(
                    account.id,
                    'budget_exceeded',
                    f'Budget exceeded for {budget.category_name}! Spent {spent:,.0f} IDR (limit: {limit:,.0f} IDR)',
                    spent,
                    budget.category_name
                )
            elif status == 'warning' and not self._alert_exists(account.id, 'budget_warning', budget.category_name):
                self.alert_repo.create_alert(
                    account.id,
                    'budget_warning',
                    f'Budget warning for {budget.category_name}: {usage_pct:.1f}% used',
                    spent,
                    budget.category_name
                )

        return budget_status

    def detect_spending_anomalies(self, user_id: int) -> List[Dict]:
        """Detect unusual spending patterns."""
        account = self.account_repo.get_by_telegram_id(str(user_id))
        if not account:
            return []

        # Get last 60 days of transactions
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=60)

        transactions = self.transaction_repo.get_transactions_by_date_range(
            account.id, start_date, end_date
        )

        if len(transactions) < 10:  # Not enough data
            return []

        # Calculate daily spending
        daily_spending = defaultdict(float)
        for t in transactions:
            daily_spending[t.date.date()] += abs(t.outgoing or 0)

        spending_amounts = list(daily_spending.values())
        mean_spending = np.mean(spending_amounts)
        std_spending = np.std(spending_amounts)

        # Detect anomalies (spending > mean + 2*std)
        threshold = mean_spending + 2 * std_spending

        anomalies = []
        for date, amount in daily_spending.items():
            if amount > threshold and amount > mean_spending * 1.5:  # At least 50% above average
                anomalies.append({
                    'date': date,
                    'amount': amount,
                    'deviation': amount - mean_spending,
                    'severity': 'high' if amount > mean_spending * 2 else 'medium'
                })

        return sorted(anomalies, key=lambda x: x['date'], reverse=True)

    def calculate_financial_health_score(self, user_id: int) -> Dict:
        """Calculate a financial health score based on various factors."""
        account = self.account_repo.get_by_telegram_id(str(user_id))
        if not account:
            return {}

        score_components = {
            'budget_adherence': 0,  # 0-30 points
            'spending_consistency': 0,  # 0-25 points
            'savings_rate': 0,  # 0-25 points
            'transaction_regularity': 0,  # 0-20 points
        }

        # Check budget adherence
        budget_status = self.check_budget_status(user_id)
        if budget_status:
            within_budget_count = sum(1 for status in budget_status.values() if status['status'] == 'safe')
            total_budgets = len(budget_status)
            score_components['budget_adherence'] = (within_budget_count / total_budgets) * 30

        # Check spending consistency (lower variance = higher score)
        trends = self.get_spending_trends(user_id, 'daily')
        if trends:
            daily_amounts = [data['spending'] for data in trends.values()]
            if len(daily_amounts) > 1:
                cv = np.std(daily_amounts) / np.mean(daily_amounts) if np.mean(daily_amounts) > 0 else 1
                consistency_score = max(0, 25 - (cv * 10))  # Lower CV = higher score
                score_components['spending_consistency'] = min(25, consistency_score)

        # Calculate savings rate (last 30 days)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)

        recent_transactions = self.transaction_repo.get_transactions_by_date_range(
            account.id, start_date, end_date
        )

        total_income = sum(t.incoming or 0 for t in recent_transactions)
        total_spending = sum(abs(t.outgoing or 0) for t in recent_transactions)

        if total_income > 0:
            savings_rate = ((total_income - total_spending) / total_income) * 100
            score_components['savings_rate'] = max(0, min(25, savings_rate * 0.5))  # 50% savings = full points

        # Transaction regularity (consistent transaction patterns)
        if len(recent_transactions) >= 20:
            score_components['transaction_regularity'] = 20
        elif len(recent_transactions) >= 10:
            score_components['transaction_regularity'] = 15
        elif len(recent_transactions) >= 5:
            score_components['transaction_regularity'] = 10

        total_score = sum(score_components.values())

        # Determine grade
        if total_score >= 85:
            grade = 'A'
        elif total_score >= 70:
            grade = 'B'
        elif total_score >= 55:
            grade = 'C'
        elif total_score >= 40:
            grade = 'D'
        else:
            grade = 'F'

        return {
            'total_score': total_score,
            'grade': grade,
            'components': score_components,
            'recommendations': self._get_health_recommendations(score_components)
        }

    def _get_transaction_category(self, transaction) -> str:
        """Get category name for a transaction."""
        if hasattr(transaction, 'category') and transaction.category:
            return transaction.category.name if hasattr(transaction.category, 'name') else str(transaction.category)
        return 'Uncategorized'

    def _alert_exists(self, user_id: int, alert_type: str, category: str = None) -> bool:
        """Check if a similar alert already exists."""
        # Check for alerts created in the last 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)

        alerts = self.session.query(SpendingAlert).filter(
            SpendingAlert.user_id == user_id,
            SpendingAlert.alert_type == alert_type,
            SpendingAlert.created_at >= cutoff_time,
            SpendingAlert.deleted_at.is_(None)
        )

        if category:
            alerts = alerts.filter(SpendingAlert.category == category)

        return alerts.first() is not None

    def _get_health_recommendations(self, components: Dict) -> List[str]:
        """Generate recommendations based on health score components."""
        recommendations = []

        if components['budget_adherence'] < 20:
            recommendations.append("Set realistic budget limits and track your spending more closely")

        if components['spending_consistency'] < 15:
            recommendations.append("Try to maintain more consistent daily spending patterns")

        if components['savings_rate'] < 15:
            recommendations.append("Increase your savings rate by reducing unnecessary expenses")

        if components['transaction_regularity'] < 15:
            recommendations.append("Upload your bank statements more regularly for better tracking")

        return recommendations
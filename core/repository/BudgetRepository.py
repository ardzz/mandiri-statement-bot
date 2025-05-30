from typing import List, Optional
from sqlalchemy.orm import Session

from core.database import BudgetLimit, FinancialGoal, SpendingAlert
from core.repository.base import BaseRepository


class BudgetRepository(BaseRepository[BudgetLimit]):
    """Repository for managing budget limits."""

    def __init__(self, db: Session):
        super().__init__(db, BudgetLimit)

    def get_user_budgets(self, user_id: int) -> List[BudgetLimit]:
        """Get all budget limits for a user."""
        return self.db.query(BudgetLimit).filter(
            BudgetLimit.user_id == user_id,
            BudgetLimit.deleted_at.is_(None)
        ).all()

    def get_budget_by_category(self, user_id: int, category_name: str) -> Optional[BudgetLimit]:
        """Get budget limit for a specific category."""
        return self.db.query(BudgetLimit).filter(
            BudgetLimit.user_id == user_id,
            BudgetLimit.category_name == category_name,
            BudgetLimit.deleted_at.is_(None)
        ).first()

    def set_budget_limit(self, user_id: int, category_name: str, monthly_limit: float) -> BudgetLimit:
        """Set or update budget limit for a category."""
        existing = self.get_budget_by_category(user_id, category_name)

        if existing:
            existing.monthly_limit = monthly_limit
            self.db.commit()
            return existing
        else:
            return self.create({
                'user_id': user_id,
                'category_name': category_name,
                'monthly_limit': monthly_limit
            })


class GoalRepository(BaseRepository[FinancialGoal]):
    """Repository for managing financial goals."""

    def __init__(self, db: Session):
        super().__init__(db, FinancialGoal)

    def get_user_goals(self, user_id: int, active_only: bool = True) -> List[FinancialGoal]:
        """Get all financial goals for a user."""
        query = self.db.query(FinancialGoal).filter(
            FinancialGoal.user_id == user_id,
            FinancialGoal.deleted_at.is_(None)
        )

        if active_only:
            query = query.filter(FinancialGoal.is_active == True)

        return query.all()

    def update_goal_progress(self, goal_id: int, current_amount: float) -> Optional[FinancialGoal]:
        """Update progress on a financial goal."""
        goal = self.get(goal_id)
        if goal:
            goal.current_amount = current_amount
            self.db.commit()
            return goal
        return None


class AlertRepository(BaseRepository[SpendingAlert]):
    """Repository for managing spending alerts."""

    def __init__(self, db: Session):
        super().__init__(db, SpendingAlert)

    def get_user_alerts(self, user_id: int, unread_only: bool = False) -> List[SpendingAlert]:
        """Get spending alerts for a user."""
        query = self.db.query(SpendingAlert).filter(
            SpendingAlert.user_id == user_id,
            SpendingAlert.deleted_at.is_(None)
        )

        if unread_only:
            query = query.filter(SpendingAlert.is_read == False)

        return query.order_by(SpendingAlert.created_at.desc()).all()

    def create_alert(self, user_id: int, alert_type: str, message: str,
                     amount: float = None, category: str = None) -> SpendingAlert:
        """Create a new spending alert."""
        return self.create({
            'user_id': user_id,
            'alert_type': alert_type,
            'message': message,
            'amount': amount,
            'category': category
        })

    def mark_as_read(self, alert_id: int) -> bool:
        """Mark an alert as read."""
        alert = self.get(alert_id)
        if alert:
            alert.is_read = True
            self.db.commit()
            return True
        return False
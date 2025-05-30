import dataclasses
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint, Boolean, Text
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

from config.settings import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class SoftDeleteMixin:
    """ Mixin for soft delete functionality."""
    deleted_at = Column(DateTime, nullable=True)

    def soft_delete(self):
        """ Marks the object as deleted by setting the deleted_at timestamp."""
        self.deleted_at = datetime.now()

    def restore(self):
        """ Restores the object by clearing the deleted_at timestamp."""
        self.deleted_at = None

    @property
    def is_deleted(self):
        """ Checks if the object is marked as deleted."""
        return self.deleted_at is not None


@dataclasses.dataclass
class Category(SoftDeleteMixin, Base):
    """ Class representing a category of bank transactions."""
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(length=255), unique=True)
    subcategories = relationship("Subcategory", back_populates="category")


@dataclasses.dataclass
class Subcategory(SoftDeleteMixin, Base):
    """ Class representing a subcategory of bank transactions."""
    __tablename__ = 'subcategories'
    id = Column(Integer, primary_key=True)
    name = Column(String(length=255))
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship("Category", back_populates="subcategories")
    transactions = relationship("BankTransaction", back_populates="subcategory")


@dataclasses.dataclass
class BudgetLimit(SoftDeleteMixin, Base):
    """Budget limits for different categories."""
    __tablename__ = 'budget_limits'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('bank_accounts.id', ondelete='CASCADE'))
    category_name = Column(String(255), nullable=False)
    monthly_limit = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    account = relationship("BankAccount", back_populates="budget_limits")


@dataclasses.dataclass
class FinancialGoal(SoftDeleteMixin, Base):
    """Financial goals and targets."""
    __tablename__ = 'financial_goals'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('bank_accounts.id', ondelete='CASCADE'))
    goal_type = Column(String(50), nullable=False)  # 'savings', 'spending_limit', 'income_target'
    title = Column(String(255), nullable=False)
    description = Column(String(500))
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    target_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    account = relationship("BankAccount", back_populates="financial_goals")


@dataclasses.dataclass
class SpendingAlert(SoftDeleteMixin, Base):
    """Spending alerts and notifications."""
    __tablename__ = 'spending_alerts'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('bank_accounts.id', ondelete='CASCADE'))
    alert_type = Column(String(50), nullable=False)  # 'budget_exceeded', 'unusual_spending', 'goal_milestone'
    message = Column(String(500), nullable=False)
    amount = Column(Float)
    category = Column(String(255))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    account = relationship("BankAccount", back_populates="spending_alerts")


@dataclasses.dataclass
class BankAccount(SoftDeleteMixin, Base):
    """ Class representing a bank account."""
    __tablename__ = 'bank_accounts'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(length=255), unique=True, nullable=False)
    bank_name = Column(String(length=255), nullable=True)
    account_number = Column(String(length=255), unique=True, nullable=True)
    balance = Column(Float, nullable=True)
    birth_date = Column(DateTime)

    # Relationships
    transactions = relationship("BankTransaction", back_populates="account")
    budget_limits = relationship("BudgetLimit", back_populates="account")
    financial_goals = relationship("FinancialGoal", back_populates="account")
    spending_alerts = relationship("SpendingAlert", back_populates="account")
    spending_patterns = relationship("SpendingPattern", back_populates="account")
    recurring_transactions = relationship("RecurringTransaction", back_populates="account")
    pattern_anomalies = relationship("PatternAnomaly", back_populates="account")


@dataclasses.dataclass
class BankTransaction(SoftDeleteMixin, Base):
    """ Class representing a bank transaction."""
    __tablename__ = 'bank_transactions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('bank_accounts.id', ondelete='CASCADE', onupdate='CASCADE'))
    description = Column(String(length=255))
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    subcategory_id = Column(Integer, ForeignKey('subcategories.id'), nullable=True)
    incoming = Column(Float, nullable=True)
    outgoing = Column(Float, nullable=True)
    balance = Column(Float)
    date: datetime = Column(DateTime)

    # Relationships
    account = relationship("BankAccount", back_populates="transactions")
    subcategory = relationship("Subcategory", back_populates="transactions")

    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='uq_user_date'),
    )

@dataclasses.dataclass
class SpendingPattern(SoftDeleteMixin, Base):
    """Store detected spending patterns for users."""
    __tablename__ = 'spending_patterns'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('bank_accounts.id', ondelete='CASCADE'))
    pattern_type = Column(String(50), nullable=False)  # 'daily', 'weekly', 'monthly'
    pattern_key = Column(String(100), nullable=False)  # e.g., 'monday', 'week_1', 'january'
    average_amount = Column(Float, nullable=False)
    transaction_count = Column(Integer, default=0)
    confidence_score = Column(Float, default=0.0)  # 0.0 to 1.0
    variance = Column(Float, default=0.0)
    last_calculated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    account = relationship("BankAccount", back_populates="spending_patterns")

@dataclasses.dataclass
class RecurringTransaction(SoftDeleteMixin, Base):
    """Store detected recurring transactions."""
    __tablename__ = 'recurring_transactions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('bank_accounts.id', ondelete='CASCADE'))
    merchant_pattern = Column(String(255), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    frequency_type = Column(String(50), nullable=False)  # 'daily', 'weekly', 'monthly', 'yearly'
    frequency_value = Column(Integer, default=1)  # every N days/weeks/months
    average_amount = Column(Float, nullable=False)
    last_transaction_date = Column(DateTime)
    next_expected_date = Column(DateTime)
    confidence_score = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    account = relationship("BankAccount", back_populates="recurring_transactions")
    category = relationship("Category")


class PatternAnomaly(SoftDeleteMixin, Base):
    """Store detected spending anomalies."""
    __tablename__ = 'pattern_anomalies'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('bank_accounts.id', ondelete='CASCADE'))
    anomaly_type = Column(String(50), nullable=False)  # 'spike', 'drop', 'missing_recurring'
    detected_date = Column(DateTime, nullable=False)
    description = Column(Text)
    severity = Column(String(20), default='medium')  # 'low', 'medium', 'high'
    amount_involved = Column(Float)
    deviation_percentage = Column(Float)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    account = relationship("BankAccount", back_populates="pattern_anomalies")
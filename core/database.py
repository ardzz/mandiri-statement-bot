import dataclasses
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Mapped, mapped_column
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
class BankAccount(SoftDeleteMixin, Base):
    """ Class representing a bank account."""
    __tablename__ = 'bank_accounts'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(length=255), unique=True, nullable=False)
    bank_name = Column(String(length=255), nullable=True)
    account_number = Column(String(length=255), unique=True, nullable=True)
    balance = Column(Float, nullable=True)
    birth_date = Column(DateTime)
    transactions = relationship("BankTransaction", back_populates="account")

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
    date: Mapped[datetime] = mapped_column(DateTime, nullable=True, default=datetime.now)
    account = relationship("BankAccount", back_populates="transactions")
    subcategory = relationship("Subcategory", back_populates="transactions")

    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='uq_user_date'),
    )

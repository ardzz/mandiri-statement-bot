from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config.settings import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(length=255), unique=True)
    subcategories = relationship("Subcategory", back_populates="category")

class Subcategory(Base):
    __tablename__ = 'subcategories'
    id = Column(Integer, primary_key=True)
    name = Column(String(length=255))
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship("Category", back_populates="subcategories")
    transactions = relationship("BankTransaction", back_populates="subcategory")

class BankAccount(Base):
    __tablename__ = 'bank_accounts'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(length=255), unique=True)
    bank_name = Column(String(length=255), nullable=True)
    account_number = Column(String(length=255), unique=True, nullable=True)
    balance = Column(Float, nullable=True)
    birth_date = Column(DateTime)
    transactions = relationship("BankTransaction", back_populates="account")

class BankTransaction(Base):
    __tablename__ = 'bank_transactions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('bank_accounts.id', ondelete='CASCADE', onupdate='CASCADE'))
    date = Column(DateTime)
    description = Column(String(length=255))
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    subcategory_id = Column(Integer, ForeignKey('subcategories.id'), nullable=True)
    incoming = Column(Float, nullable=True)
    outgoing = Column(Float, nullable=True)
    balance = Column(Float)
    account = relationship("BankAccount", back_populates="transactions")
    subcategory = relationship("Subcategory", back_populates="transactions")
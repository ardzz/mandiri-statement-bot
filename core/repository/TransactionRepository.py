from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text
from sqlalchemy import and_
from datetime import date
from core.database import BankTransaction, Session, BankAccount
from core.repository.base import BaseRepository


class TransactionRepository(BaseRepository[BankTransaction]):
    """Repository for managing bank transactions."""
    def __init__(self, db: Session):
        super().__init__(db, BankTransaction)

    def insert_transaction(self, transactions, bank_account: BankAccount):
        """Insert transactions into the database."""
        for transaction in transactions:
            try:
                self.create({
                    "date": transaction["date"],
                    "description": transaction["description"].strip(),
                    "incoming": transaction["incoming"],
                    "outgoing": transaction["outgoing"],
                    "balance": transaction["balance"],
                    "user_id": bank_account.id
                })
            except IntegrityError:
                self.db.rollback()

    def get_all_transactions(self, user_id):
        """Get all transactions for a user."""
        with self.db as session:
            transactions = (
                session.query(BankTransaction)
                .filter(
                    BankTransaction.user_id == user_id,
                    BankTransaction.deleted_at == None
                )
                .order_by(BankTransaction.date.desc())
                .all()
            )
            return transactions

    def get_transaction_statistics(self, user_id):
        """Get transaction statistics for a user."""
        query = """
            SELECT
                COUNT(*)                                                   AS total_transactions,
                SUM(IF(outgoing > 0, outgoing, 0))                         AS total_outcome,
                SUM(IF(incoming > 0, incoming, 0))                         AS total_income,
                MAX(IF(outgoing > 0, outgoing, NULL))                      AS highest_outcome,
                MAX(IF(incoming > 0, incoming, NULL))                      AS highest_income,
                MIN(IF(outgoing > 0 AND outgoing < 10000, outgoing, NULL)) AS lowest_outcome,
                MIN(IF(incoming > 0, incoming, NULL))                      AS lowest_income,
                AVG(IF(outgoing > 0, outgoing, NULL))                      AS avg_outcome,
                AVG(IF(incoming > 0, incoming, NULL)) AS avg_income
            FROM bank_transactions
            WHERE user_id = :user_id AND deleted_at IS NULL
        """
        with self.db as session:
            result = session.execute(text(query), {"user_id": user_id}).fetchone()
            return result._mapping

    def get_transactions_by_date_range(self, user_id: int, start_date: date, end_date: date):
        """Get transactions within a specific date range for a user."""
        with self.db as session:
            transactions = (
                session.query(BankTransaction)
                .filter(
                    and_(
                        BankTransaction.user_id == user_id,
                        BankTransaction.date >= start_date,
                        BankTransaction.date <= end_date,
                        BankTransaction.deleted_at == None
                    )
                )
                .order_by(BankTransaction.date.desc())
                .all()
            )
            return transactions

    def get_transaction_statistics_by_date_range(self, start_date: date, end_date: date):
        """Get transaction statistics within a specific date range."""
        query = """
            SELECT
                COUNT(*)                                                   AS total_transactions,
                SUM(IF(outgoing > 0, outgoing, 0))                         AS total_outcome,
                SUM(IF(incoming > 0, incoming, 0))                         AS total_income,
                MAX(IF(outgoing > 0, outgoing, NULL))                      AS highest_outcome,
                MAX(IF(incoming > 0, incoming, NULL))                      AS highest_income,
                MIN(IF(outgoing > 0 AND outgoing < 10000, outgoing, NULL)) AS lowest_outcome,
                MIN(IF(incoming > 0, incoming, NULL))                      AS lowest_income,
                AVG(IF(outgoing > 0, outgoing, NULL))                      AS avg_outcome,
                AVG(IF(incoming > 0, incoming, NULL)) AS avg_income
            FROM bank_transactions
            WHERE date BETWEEN :start_date AND :end_date AND deleted_at IS NULL
        """
        with self.db as session:
            result = session.execute(text(query), {"start_date": start_date, "end_date": end_date}).fetchone()
            return result._mapping

    def get_user_date_bounds(self, user_id: int):
        """Get the earliest and latest transaction dates for a user."""
        with self.db as session:
            result = session.execute(
                text("""
                    SELECT 
                        MIN(DATE(date)) as min_date,
                        MAX(DATE(date)) as max_date
                    FROM bank_transactions 
                    WHERE user_id = :user_id AND deleted_at IS NULL
                """),
                {"user_id": user_id}
            ).fetchone()

            if result and result.min_date and result.max_date:
                return result.min_date, result.max_date
            return None, None
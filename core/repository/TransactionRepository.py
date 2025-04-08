from sqlalchemy.exc import IntegrityError

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
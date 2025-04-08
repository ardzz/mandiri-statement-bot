from sqlalchemy.exc import IntegrityError

from core.database import BankTransaction, Session, BankAccount
from core.repository.base import BaseRepository


class TransactionRepository(BaseRepository[BankTransaction]):
    def __init__(self, db: Session):
        super().__init__(db, BankTransaction)

    def insert_transaction(self, transactions, bank_account: BankAccount):
        """Insert transactions into the database."""
        for transaction in transactions:
            try:
                self.create({
                    "date": transaction["datetime"],
                    "description": transaction["description"],
                    "incoming": transaction["incoming"],
                    "outgoing": transaction["outgoing"],
                    "balance": transaction["balance"],
                    "user_id": bank_account.id
                })
            except IntegrityError:
                self.db.rollback()

from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from .base import BaseRepository
from ..database import BankAccount


class BankAccountRepository(BaseRepository[BankAccount]):
    """Repository for managing bank accounts."""
    def __init__(self, db: Session):
        super().__init__(db, BankAccount)

    def get_by_telegram_id(self, telegram_id: str) -> Optional[BankAccount]:
        """Fetch a bank account by its Telegram ID."""
        with self.db as session:
            stmt = select(BankAccount).where(BankAccount.telegram_id == telegram_id)
            result = session.execute(stmt).scalars().first()

            return result

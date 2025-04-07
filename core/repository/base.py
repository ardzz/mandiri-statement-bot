from datetime import datetime
from typing import Type, TypeVar, Generic, List, Optional
from sqlalchemy.orm import Session

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """Base repository class for CRUD operations."""
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model

    def get(self, id_row: int) -> Optional[T]:
        """Fetch a single object by its ID."""
        return self.db.get(self.model, id_row)

    def get_all(self) -> List[T]:
        """Fetch all objects of the model."""
        return self.db.query(self.model).all()

    def create(self, obj_in: dict) -> T:
        """Create a new object."""
        obj = self.model(**obj_in)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, db_obj: T, obj_in: dict) -> T:
        """Update an existing object."""
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id_row: int) -> None:
        """Delete an object by its ID."""
        obj = self.get(id_row)
        if not obj:
            return
        if self._has_deleted_at(): # type: ignore[attr-defined]
            setattr(obj, 'deleted_at', datetime.now())
        else:
            self.db.delete(obj)
        self.db.commit()

# app/repositories/admin_repo.py — Admin data access

from typing import Optional

from sqlalchemy.orm import Session

from app.models.admin import Admin
from app.repositories.base import BaseRepository


class AdminRepository(BaseRepository[Admin]):

    def __init__(self, db: Session):
        super().__init__(Admin, db)

    def get_by_username(self, username: str) -> Optional[Admin]:
        return self.db.query(Admin).filter(Admin.username == username).first()

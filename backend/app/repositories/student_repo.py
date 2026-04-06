# app/repositories/student_repo.py — Student data access

from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.student import Student
from app.repositories.base import BaseRepository


class StudentRepository(BaseRepository[Student]):

    def __init__(self, db: Session):
        super().__init__(Student, db)

    def get_by_username(self, username: str) -> Optional[Student]:
        return self.db.query(Student).filter(Student.username == username).first()

    def get_by_registration_no(self, reg_no: str) -> Optional[Student]:
        return self.db.query(Student).filter(Student.registration_no == reg_no).first()

    def search(self, query: str, skip: int = 0, limit: int = 100) -> List[Student]:
        pattern = f"%{query}%"
        return (
            self.db.query(Student)
            .filter(
                or_(
                    Student.name.ilike(pattern),
                    Student.username.ilike(pattern),
                    Student.email.ilike(pattern),
                    Student.registration_no.ilike(pattern),
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_count(self, query: str) -> int:
        pattern = f"%{query}%"
        return (
            self.db.query(Student)
            .filter(
                or_(
                    Student.name.ilike(pattern),
                    Student.username.ilike(pattern),
                    Student.email.ilike(pattern),
                    Student.registration_no.ilike(pattern),
                )
            )
            .count()
        )

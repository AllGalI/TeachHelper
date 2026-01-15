from typing import Sequence, Optional
import uuid
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_users import  Users


class RepoUser:
    def __init__(self, session: AsyncSession):
        self.session = session
  
    async def email_exists(self, email):
        stmt = select(Users).where(Users.email == email)
        response = await self.session.execute(stmt)
        result = response.scalar_one_or_none()
        return result is not None
        

    async def create(self, user: Users) -> Users:
        self.session.add(user)
        return user

    async def get(self, user_id: uuid.UUID) -> Optional[Users]:
        res = await self.session.execute(select(Users).where(Users.id == user_id))
        return res.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[Users]:
        res = await self.session.execute(select(Users).where(Users.email == email))
        return res.scalar_one_or_none()

    async def list(self, limit: int = 100, offset: int = 0) -> Sequence[Users]:
        res = await self.session.execute(select(Users).offset(offset).limit(limit))
        return res.scalars().all()

    async def update(self, user_id: uuid.UUID, fields: dict) -> Optional[Users]:
        await self.session.execute(update(Users).where(Users.id == user_id).values(**fields))

    async def delete(self, user_id: uuid.UUID) -> bool:
        await self.session.execute(delete(Users).where(Users.id == user_id))
        return True



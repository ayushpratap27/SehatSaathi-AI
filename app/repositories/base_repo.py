"""
Generic async repository base — typed CRUD operations for all models.
"""

from __future__ import annotations

from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Provides standard async CRUD operations for a SQLAlchemy ORM model.

    Subclasses only need to pass the model class:
        class UserRepository(BaseRepository[User]):
            model = User
    """

    model: Type[ModelT]

    async def get_by_id(
        self, db: AsyncSession, id: str
    ) -> Optional[ModelT]:
        return await db.get(self.model, id)

    async def get_all(
        self, db: AsyncSession, limit: int = 100, offset: int = 0
    ) -> List[ModelT]:
        result = await db.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, **kwargs) -> ModelT:
        instance = self.model(**kwargs)
        db.add(instance)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def update(
        self, db: AsyncSession, id: str, **kwargs
    ) -> Optional[ModelT]:
        instance = await self.get_by_id(db, id)
        if instance is None:
            return None
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await db.flush()
        await db.refresh(instance)
        return instance

    async def delete(self, db: AsyncSession, id: str) -> bool:
        instance = await self.get_by_id(db, id)
        if instance is None:
            return False
        await db.delete(instance)
        return True

    async def count(self, db: AsyncSession) -> int:
        from sqlalchemy import func  # noqa: PLC0415
        result = await db.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()

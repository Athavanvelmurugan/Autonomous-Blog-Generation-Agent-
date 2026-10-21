import hashlib
import secrets
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.db.models import User, ApiKey

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_user(self, email: str, role: str = "user") -> User:
        """
        Gets an existing user by email or creates a new one.
        """
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            return user

        user = User(email=email, role=role, is_active=True)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    @staticmethod
    def hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    async def create_api_key(self, user_id: int, name: str = "default") -> Tuple[ApiKey, str]:
        """
        Generates a secure API key, stores its SHA-256 hash, and returns the raw key once.
        """
        raw_key = f"agy_{secrets.token_urlsafe(32)}"
        key_hash = self.hash_key(raw_key)

        api_key = ApiKey(
            user_id=user_id,
            key_hash=key_hash,
            name=name,
            revoked=False,
        )
        self.session.add(api_key)
        await self.session.commit()
        await self.session.refresh(api_key)
        return api_key, raw_key

    async def validate_api_key(self, raw_key: str) -> Optional[User]:
        """
        Authenticates a user via API key.
        """
        key_hash = self.hash_key(raw_key)
        stmt = (
            select(User)
            .join(ApiKey, ApiKey.user_id == User.id)
            .where(
                ApiKey.key_hash == key_hash,
                ApiKey.revoked == False,
                User.is_active == True,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

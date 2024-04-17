import unittest
from unittest.mock import MagicMock, AsyncMock, Mock

from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.schema.user import UserSchema
from src.repository.users import get_user_by_email, create_user, update_token, confirmed_email, update_avatar_url


class TestAsyncUser(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.user = User(id=1, username='test_user', password="qwerty", confirmed=True)
        self.session = AsyncMock(spec=AsyncSession)

    async def test_get_user_by_email(self):
        email = "test@example.com"
        user = User(id=1, username="test_user", email=email)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user

        self.session.execute.return_value = mock_result

        result = await get_user_by_email(email, self.session)
        self.assertEqual(result, user)
        self.session.execute.assert_called_once()

    async def test_create_user(self):
        user_data = UserSchema(username="new_user", email="new@example.com", password="pass1234")
        new_user = User(**user_data.dict(), avatar="avatar_url")

        self.session.add = Mock()
        self.session.commit = AsyncMock()
        self.session.refresh = AsyncMock()

        result = await create_user(user_data, self.session)
        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once()

        self.assertEqual(result.username, new_user.username)
        self.assertEqual(result.email, new_user.email)

    async def test_update_token(self):
        user = User(id=1, username="test_user", email="test@example.com")
        token = "new_refresh_token"

        self.session.commit = AsyncMock()

        await update_token(user, token, self.session)
        self.assertEqual(user.refresh_token, token)
        self.session.commit.assert_called_once()

    async def test_confirmed_email(self):
        email = "test@example.com"
        user = User(id=1, username="test_user", email=email, confirmed=False)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        self.session.execute.return_value = mock_result
        self.session.commit = AsyncMock()

        await confirmed_email(email, self.session)
        self.assertTrue(user.confirmed)
        self.session.commit.assert_called_once()

    async def test_update_avatar_url(self):
        email = "test@example.com"
        url = "new_avatar_url"
        user = User(id=1, username="test_user", email=email, avatar="old_avatar_url")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        self.session.execute.return_value = mock_result
        self.session.commit = AsyncMock()
        self.session.refresh = AsyncMock()

        result = await update_avatar_url(email, url, self.session)
        self.assertEqual(result.avatar, url)
        self.session.commit.assert_called_once()
        self.session.refresh.assert_called_once_with(user)

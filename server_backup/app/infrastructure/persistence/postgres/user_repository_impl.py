from app.domain.repositories.user_repository import UserRepository
from app.domain.entities.user import User

class PostgresUserRepository(UserRepository):

    def __init__(self):
        self._db = {}

    def save(self, user: User) -> None:
        self._db[user.id] = user

    def get_by_id(self, user_id: str):
        return self._db.get(user_id)
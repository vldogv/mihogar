import uuid
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository

class CreateUser:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    def execute(self, email: str) -> User:
        user = User(id=str(uuid.uuid4()), email=email)
        self.repository.save(user)
        return user
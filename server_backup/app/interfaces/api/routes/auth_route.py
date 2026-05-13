from fastapi import APIRouter
from app.application.use_cases.create_user import CreateUser
from app.infrastructure.persistence.postgres.user_repository_impl import PostgresUserRepository
from app.interfaces.schemas.user_dto import CreateUserRequest, UserResponse

router = APIRouter()

@router.post("/users", response_model=UserResponse)
def create_user(request: CreateUserRequest):

    repository = PostgresUserRepository()
    use_case = CreateUser(repository)

    user = use_case.execute(request.email)

    return UserResponse(id=user.id, email=user.email)
from fastapi import FastAPI
from app.interfaces.api.routes import auth_route

app = FastAPI()

app.include_router(auth_route.router)
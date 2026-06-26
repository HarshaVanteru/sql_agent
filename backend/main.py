from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.auth.signin import router as signin_router
from backend.auth.signout import router as signout_router
from backend.auth.signup import router as signup_router
from backend.database.router import router as database_router
from backend.query.router import router as query_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(signin_router)
app.include_router(signout_router)
app.include_router(signup_router)
app.include_router(database_router)
app.include_router(query_router)
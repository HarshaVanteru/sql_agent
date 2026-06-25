from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.signin import router as signin_router
from backend.signout import router as signout_router
from backend.signup import router as signup_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(signin_router)
app.include_router(signout_router)
app.include_router(signup_router)
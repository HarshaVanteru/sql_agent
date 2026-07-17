from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.auth.router import router as auth_router
from backend.database.router import router as database_router
from backend.query.router import router as query_router
from backend.core.logging_config import setup_logging
from backend.core.tracing import log_tracing_status

# Initialize logging
setup_logging()
log_tracing_status()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth_router)
app.include_router(database_router)
app.include_router(query_router)
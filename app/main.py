from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import Base, engine
from app.routes import transactions, users, analytics
from app.seed import seed_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_data()
    yield


app = FastAPI(
    title="Finance Tracker API",
    description="A backend system to manage and analyze personal financial records.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Finance Tracker API is running",
        "docs": "/docs",
        "version": "1.0.0",
    }

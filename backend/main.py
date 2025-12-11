"""FastAPI application entrypoint for SmartReco."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import analysis, recommendations, rules, upload

app = FastAPI(title="SmartReco", version="1.0.0")

# Basic CORS to simplify local dev and docker usage
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(upload.router)
app.include_router(analysis.router)
app.include_router(rules.router)
app.include_router(recommendations.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Health probe used by Docker."""
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    """Small welcome message."""
    return {"message": "SmartReco backend is running"}



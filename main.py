"""Creates the standalone FastAPI application without MongoDB or patient dependencies."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.dashboard import router as dashboard_router
from app.monitor.middleware import capture_trace

app = FastAPI(
    title="HealthStack Guidelines API",
    version="0.1.0",
    description=(
        "Clinical guideline and PubMed evidence retrieval. PubMed data is "
        "provided by NLM without warranty; abstracts may be copyrighted by "
        "publishers or authors."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(capture_trace)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(router, prefix="/api/v1")
app.include_router(dashboard_router)

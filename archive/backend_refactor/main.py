from fastapi import FastAPI
from backend.api.scheme_routes import router as scheme_router

app = FastAPI(
    title="Scheme Intelligence API",
    version="1.0"
)

# include routes
app.include_router(scheme_router)


@app.get("/")
def root():
    return {
        "status": "Backend Running",
        "service": "Scheme Intelligence Engine"
    }
from app import catalog
from app.reommender import recommend_movies
from app.routers import movies, recommendations
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI(title="Movie Recommendation API")

# Needed only if the Flutter app runs on web. Mobile apps ignore CORS.
# Restrict allow_origins before deploying publicly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- one error shape for every failure: {"error": {"code": ..., "message": ...}} ----
def _error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(_: Request, exc: StarletteHTTPException):
    code = {404: "not_found", 422: "validation_error"}.get(exc.status_code, "http_error")
    return _error(exc.status_code, code, str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError):
    first = exc.errors()[0]
    location = ".".join(str(part) for part in first["loc"] if part != "body")
    message = f"{location}: {first['msg']}" if location else first["msg"]
    return _error(422, "validation_error", message)


@app.exception_handler(Exception)
async def unexpected_error_handler(_: Request, exc: Exception):
    return _error(500, "internal_error", "Internal server error")


app.include_router(movies.router)
app.include_router(recommendations.router)


@app.get("/")
def root():
    return {"message": "Movie Recommendation API is running"}


@app.get("/health")
def health():
    return {"status": "ok", "movies": catalog.movie_count()}


@app.post("/recommend")
def recommend(selected_movies: list[str]):
    """Legacy title-based endpoint, kept so existing clients keep working."""
    recommendations_df = recommend_movies(selected_movies)

    # recommend_movies() returns [] when no title matches; a list has no .to_dict()
    if len(recommendations_df) == 0:
        return {"recommendations": []}

    # Missing values (possible for movies synced from TMDB) become null, never NaN.
    cleaned = recommendations_df.astype(object).where(recommendations_df.notna(), None)
    return {"recommendations": cleaned.to_dict(orient="records")}

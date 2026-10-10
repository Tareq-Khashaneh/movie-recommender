from fastapi import APIRouter, HTTPException

from app import catalog
from app.reommender import recommend_by_ids
from app.schemas import RecommendationRequest, RecommendationResponse, RecommendedMovie

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("", response_model=RecommendationResponse)
def create_recommendations(request: RecommendationRequest):
    unknown = [i for i in request.movie_ids if catalog.get_summary(i) is None]
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown movie ids: {unknown}")

    ranked = recommend_by_ids(request.movie_ids, n=request.limit)

    items = []
    for row in ranked.itertuples() if len(ranked) else []:
        summary = catalog.get_summary(int(row.movie_id))
        if summary is None:
            continue
        items.append(
            RecommendedMovie(
                **summary.model_dump(),
                similarity=round(float(row.Similarity), 4),
                score=round(float(row.Final_Score), 4),
            )
        )
    return RecommendationResponse(items=items)

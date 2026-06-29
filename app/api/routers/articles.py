"""Article API routes."""

from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.schemas import ArticleResponse
from app.database.repositories.article_repository import ArticleRepository
from app.api.dependencies import get_article_repository

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=List[ArticleResponse], summary="List latest articles", description="Return the newest articles from the repository.")
def list_articles(
    limit: int = Query(default=10, ge=1, le=100),
    repository: ArticleRepository = Depends(get_article_repository),
) -> List[ArticleResponse]:
    """Return the latest articles."""
    return [ArticleResponse.model_validate(article.model_dump()) for article in repository.get_latest_articles(limit)]


@router.get("/{article_id}", response_model=ArticleResponse, summary="Get one article", description="Return a single article by identifier.")
def get_article(
    article_id: UUID,
    repository: ArticleRepository = Depends(get_article_repository),
) -> ArticleResponse:
    """Return one article or raise 404."""
    article = repository.get_article(article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="article not found")
    return ArticleResponse.model_validate(article.model_dump())


@router.get("/search", response_model=List[ArticleResponse], summary="Search articles", description="Search articles by title or content.")
def search_articles(
    q: str = Query(..., min_length=1),
    repository: ArticleRepository = Depends(get_article_repository),
) -> List[ArticleResponse]:
    """Search articles by the provided query."""
    return [ArticleResponse.model_validate(article.model_dump()) for article in repository.search_articles(q)]

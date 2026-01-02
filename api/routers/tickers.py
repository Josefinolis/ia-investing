"""Tickers API router."""

import time
import threading
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from api.schemas import (
    TickerCreate,
    TickerResponse,
    TickerListResponse,
    TickerSentimentResponse,
    NewsListResponse,
    NewsItemResponse,
    NewsStatus
)
from services.watchlist_service import (
    get_all_tickers,
    get_ticker,
    add_ticker,
    remove_ticker
)
from services.news_service import get_news_by_ticker, get_news_counts
from services.sentiment_service import get_ticker_sentiment
from schedulers.news_fetcher import fetch_news_for_ticker
from schedulers.analyzer import analyze_pending_for_ticker
from logger import logger

router = APIRouter()


@router.get("", response_model=TickerListResponse)
async def list_tickers():
    """Get all watched tickers with their sentiment."""
    start = time.perf_counter()
    logger.info("[API] GET /api/tickers - Starting request")

    logger.info("[API] GET /api/tickers - Fetching tickers from database...")
    db_start = time.perf_counter()
    tickers = get_all_tickers()
    db_elapsed = time.perf_counter() - db_start
    logger.info(f"[API] GET /api/tickers - Database query completed in {db_elapsed:.3f}s, found {len(tickers)} tickers")

    ticker_responses = []
    for t in tickers:
        sentiment_response = None
        if t.sentiment:
            sentiment_response = TickerSentimentResponse(
                ticker=t.sentiment.ticker,
                score=t.sentiment.score,
                normalized_score=t.sentiment.normalized_score,
                sentiment_label=t.sentiment.sentiment_label,
                signal=t.sentiment.signal,
                confidence=t.sentiment.confidence,
                positive_count=t.sentiment.positive_count,
                negative_count=t.sentiment.negative_count,
                neutral_count=t.sentiment.neutral_count,
                total_analyzed=t.sentiment.total_analyzed,
                total_pending=t.sentiment.total_pending,
                updated_at=t.sentiment.updated_at
            )

        ticker_responses.append(TickerResponse(
            id=t.id,
            ticker=t.ticker,
            name=t.name,
            added_at=t.added_at,
            is_active=t.is_active,
            sentiment=sentiment_response
        ))

    elapsed = time.perf_counter() - start
    logger.info(f"[API] GET /api/tickers - Request completed in {elapsed:.3f}s")

    return TickerListResponse(
        tickers=ticker_responses,
        count=len(ticker_responses)
    )


def _do_fetch_news(ticker_symbol: str, hours: int = 24):
    """Actual news fetch (runs in separate thread)."""
    try:
        result = fetch_news_for_ticker(ticker_symbol, hours=hours)
        logger.info(f"Background fetch completed for {ticker_symbol}: {result}")
    except Exception as e:
        logger.warning(f"Background news fetch failed for {ticker_symbol}: {e}")


def _background_fetch_news(ticker_symbol: str, hours: int = 24):
    """Background task that spawns a thread to avoid blocking the event loop."""
    thread = threading.Thread(
        target=_do_fetch_news,
        args=(ticker_symbol, hours),
        daemon=True
    )
    thread.start()
    logger.info(f"Started background fetch thread for {ticker_symbol}")


@router.post("", response_model=TickerResponse, status_code=201)
async def create_ticker(ticker_data: TickerCreate):
    """Add a new ticker to the watchlist. Does NOT fetch news automatically."""
    start = time.perf_counter()
    logger.info(f"[API] POST /api/tickers - Creating ticker: {ticker_data.ticker}")

    ticker = add_ticker(ticker_data.ticker, ticker_data.name)

    elapsed = time.perf_counter() - start
    logger.info(f"[API] POST /api/tickers - Ticker created in {elapsed:.3f}s")

    sentiment_response = None
    if ticker.sentiment:
        sentiment_response = TickerSentimentResponse(
            ticker=ticker.sentiment.ticker,
            score=ticker.sentiment.score,
            normalized_score=ticker.sentiment.normalized_score,
            sentiment_label=ticker.sentiment.sentiment_label,
            signal=ticker.sentiment.signal,
            confidence=ticker.sentiment.confidence,
            positive_count=ticker.sentiment.positive_count,
            negative_count=ticker.sentiment.negative_count,
            neutral_count=ticker.sentiment.neutral_count,
            total_analyzed=ticker.sentiment.total_analyzed,
            total_pending=ticker.sentiment.total_pending,
            updated_at=ticker.sentiment.updated_at
        )

    return TickerResponse(
        id=ticker.id,
        ticker=ticker.ticker,
        name=ticker.name,
        added_at=ticker.added_at,
        is_active=ticker.is_active,
        sentiment=sentiment_response
    )


@router.delete("/{ticker_symbol}", status_code=204)
async def delete_ticker(ticker_symbol: str):
    """Remove a ticker from the watchlist."""
    success = remove_ticker(ticker_symbol)

    if not success:
        raise HTTPException(status_code=404, detail="Ticker not found")

    return None


@router.get("/{ticker_symbol}", response_model=TickerResponse)
async def get_ticker_detail(ticker_symbol: str):
    """Get details for a specific ticker."""
    ticker = get_ticker(ticker_symbol)

    if not ticker:
        raise HTTPException(status_code=404, detail="Ticker not found")

    sentiment_response = None
    if ticker.sentiment:
        sentiment_response = TickerSentimentResponse(
            ticker=ticker.sentiment.ticker,
            score=ticker.sentiment.score,
            normalized_score=ticker.sentiment.normalized_score,
            sentiment_label=ticker.sentiment.sentiment_label,
            signal=ticker.sentiment.signal,
            confidence=ticker.sentiment.confidence,
            positive_count=ticker.sentiment.positive_count,
            negative_count=ticker.sentiment.negative_count,
            neutral_count=ticker.sentiment.neutral_count,
            total_analyzed=ticker.sentiment.total_analyzed,
            total_pending=ticker.sentiment.total_pending,
            updated_at=ticker.sentiment.updated_at
        )

    return TickerResponse(
        id=ticker.id,
        ticker=ticker.ticker,
        name=ticker.name,
        added_at=ticker.added_at,
        is_active=ticker.is_active,
        sentiment=sentiment_response
    )


@router.get("/{ticker_symbol}/news", response_model=NewsListResponse)
async def get_ticker_news(
    ticker_symbol: str,
    status: Optional[str] = Query(None, description="Filter by status: pending, analyzed"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Get news items for a ticker."""
    ticker = get_ticker(ticker_symbol)

    if not ticker:
        raise HTTPException(status_code=404, detail="Ticker not found")

    news_list = get_news_by_ticker(
        ticker_symbol=ticker_symbol,
        status=status,
        limit=limit,
        offset=offset
    )

    counts = get_news_counts(ticker_symbol)

    news_responses = [
        NewsItemResponse(
            id=n.id,
            ticker=n.ticker,
            title=n.title,
            summary=n.summary,
            published_date=n.published_date,
            source=n.source,
            url=n.url,
            relevance_score=n.relevance_score,
            status=NewsStatus(n.status),
            sentiment=n.sentiment,
            justification=n.justification,
            fetched_at=n.fetched_at,
            analyzed_at=n.analyzed_at
        )
        for n in news_list
    ]

    return NewsListResponse(
        news=news_responses,
        count=len(news_responses),
        pending_count=counts["pending"],
        analyzed_count=counts["analyzed"]
    )


@router.get("/{ticker_symbol}/sentiment", response_model=TickerSentimentResponse)
async def get_ticker_sentiment_endpoint(ticker_symbol: str):
    """Get aggregated sentiment for a ticker."""
    ticker = get_ticker(ticker_symbol)

    if not ticker:
        raise HTTPException(status_code=404, detail="Ticker not found")

    sentiment = get_ticker_sentiment(ticker_symbol)

    if not sentiment:
        raise HTTPException(status_code=404, detail="No sentiment data available")

    return TickerSentimentResponse(
        ticker=sentiment.ticker,
        score=sentiment.score,
        normalized_score=sentiment.normalized_score,
        sentiment_label=sentiment.sentiment_label,
        signal=sentiment.signal,
        confidence=sentiment.confidence,
        positive_count=sentiment.positive_count,
        negative_count=sentiment.negative_count,
        neutral_count=sentiment.neutral_count,
        total_analyzed=sentiment.total_analyzed,
        total_pending=sentiment.total_pending,
        updated_at=sentiment.updated_at
    )


@router.post("/{ticker_symbol}/fetch", status_code=202)
async def trigger_fetch(
    ticker_symbol: str,
    background_tasks: BackgroundTasks,
    hours: int = Query(24, ge=1, le=168)
):
    """Trigger news fetch for a specific ticker (runs in background)."""
    ticker = get_ticker(ticker_symbol)

    if not ticker:
        raise HTTPException(status_code=404, detail="Ticker not found")

    background_tasks.add_task(_background_fetch_news, ticker_symbol, hours)
    return {"message": f"News fetch started for {ticker_symbol}", "status": "processing"}


def _do_analyze_news(ticker_symbol: str):
    """Actual news analysis (runs in separate thread)."""
    try:
        result = analyze_pending_for_ticker(ticker_symbol)
        logger.info(f"Background analyze completed for {ticker_symbol}: {result}")
    except Exception as e:
        logger.warning(f"Background analyze failed for {ticker_symbol}: {e}")


def _background_analyze_news(ticker_symbol: str):
    """Background task that spawns a thread to avoid blocking the event loop."""
    thread = threading.Thread(
        target=_do_analyze_news,
        args=(ticker_symbol,),
        daemon=True
    )
    thread.start()
    logger.info(f"Started background analyze thread for {ticker_symbol}")


@router.post("/{ticker_symbol}/analyze", status_code=202)
async def trigger_analyze(
    ticker_symbol: str,
    background_tasks: BackgroundTasks
):
    """Trigger sentiment analysis for pending news of a specific ticker (runs in background)."""
    ticker = get_ticker(ticker_symbol)

    if not ticker:
        raise HTTPException(status_code=404, detail="Ticker not found")

    background_tasks.add_task(_background_analyze_news, ticker_symbol)
    return {"message": f"Analysis started for {ticker_symbol}", "status": "processing"}

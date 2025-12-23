#!/usr/bin/env python3
"""
IA Trading - Market Sentiment Analysis Tool

Analyzes news sentiment for stock tickers using AI to identify trading opportunities.
"""

import argparse
import sys
from datetime import datetime, timedelta
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from config import get_settings
from models import NewsItem, AnalysisResult, SentimentCategory, AnalysisSummary
from news_retriever import get_news_data
from ia_analisis import analyze_news_with_gemini
from database import get_database
from logger import logger, log_success, log_warning, log_error

console = Console()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze market sentiment for stock tickers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s AAPL                    Analyze Apple news from last 7 days
  %(prog)s TSLA --days 30          Analyze Tesla news from last 30 days
  %(prog)s MSFT --from 2024-01-01  Analyze Microsoft news from specific date
  %(prog)s NVDA --save             Analyze and save results to database
  %(prog)s AMZN --summary          Show sentiment summary for ticker
        """
    )

    parser.add_argument(
        "ticker",
        type=str,
        help="Stock ticker symbol (e.g., AAPL, TSLA, MSFT)"
    )

    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back for news (default: 7)"
    )

    parser.add_argument(
        "--from",
        dest="time_from",
        type=str,
        help="Start date in YYYY-MM-DD format"
    )

    parser.add_argument(
        "--to",
        dest="time_to",
        type=str,
        help="End date in YYYY-MM-DD format (default: now)"
    )

    parser.add_argument(
        "--save",
        action="store_true",
        help="Save analysis results to database"
    )

    parser.add_argument(
        "--no-analyze",
        action="store_true",
        help="Fetch news only, skip AI analysis"
    )

    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show sentiment summary from database"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of news items to analyze (default: 50)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    return parser.parse_args()


def parse_date(date_str: str) -> datetime:
    """Parse a date string in YYYY-MM-DD format."""
    return datetime.strptime(date_str, "%Y-%m-%d")


def display_news_table(news_list: list[NewsItem], ticker: str):
    """Display news items in a formatted table."""
    table = Table(title=f"News for {ticker}")
    table.add_column("Date", style="cyan", width=12)
    table.add_column("Source", style="magenta", width=15)
    table.add_column("Title", style="white")

    for news in news_list:
        date_str = news.published_date[:10] if len(news.published_date) >= 10 else news.published_date
        source = news.source or "Unknown"
        table.add_row(date_str, source[:15], news.title[:60])

    console.print(table)


def display_analysis_result(result: AnalysisResult, index: int, total: int):
    """Display a single analysis result."""
    sentiment_colors = {
        SentimentCategory.HIGHLY_POSITIVE: "bold green",
        SentimentCategory.POSITIVE: "green",
        SentimentCategory.NEUTRAL: "yellow",
        SentimentCategory.NEGATIVE: "red",
        SentimentCategory.HIGHLY_NEGATIVE: "bold red",
    }

    console.print(f"\n[bold blue]Analysis {index}/{total}[/bold blue]")
    console.print(f"[dim]Title:[/dim] {result.news.title[:80]}")

    if result.analysis:
        color = sentiment_colors.get(result.analysis.sentiment, "white")
        console.print(f"[dim]Sentiment:[/dim] [{color}]{result.analysis.sentiment.value}[/{color}]")
        console.print(f"[dim]Justification:[/dim] {result.analysis.justification}")
    elif result.error:
        console.print(f"[red]Error:[/red] {result.error}")
    else:
        console.print("[yellow]Analysis failed[/yellow]")


def display_summary(summary: AnalysisSummary):
    """Display analysis summary."""
    table = Table(title=f"Sentiment Summary for {summary.ticker}")
    table.add_column("Sentiment", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Percentage", justify="right")

    total = summary.analyzed_count

    for sentiment, count in summary.sentiment_distribution.items():
        pct = (count / total * 100) if total > 0 else 0
        table.add_row(sentiment, str(count), f"{pct:.1f}%")

    console.print(table)
    console.print(f"\n[dim]Total news:[/dim] {summary.total_news}")
    console.print(f"[dim]Successfully analyzed:[/dim] {summary.analyzed_count}")
    console.print(f"[dim]Failed:[/dim] {summary.failed_count}")
    console.print(f"[dim]Success rate:[/dim] {summary.success_rate:.1f}%")


def run_analysis(
    ticker: str,
    time_from: datetime,
    time_to: datetime,
    save: bool = False,
    skip_analysis: bool = False,
    limit: int = 50
) -> Optional[AnalysisSummary]:
    """Run the sentiment analysis pipeline."""
    ticker = ticker.upper()

    console.print(Panel(
        f"[bold]Analyzing sentiment for {ticker}[/bold]\n"
        f"Period: {time_from.strftime('%Y-%m-%d')} to {time_to.strftime('%Y-%m-%d')}",
        title="IA Trading"
    ))

    # Fetch news
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task("Fetching news from Alpha Vantage...", total=None)
        news_list = get_news_data(ticker, time_from, time_to)

    if not news_list:
        log_warning(f"No news items found for {ticker} in the specified date range")
        return None

    # Limit the number of news items
    if len(news_list) > limit:
        log_warning(f"Limiting analysis to {limit} most recent news items (found {len(news_list)})")
        news_list = news_list[:limit]

    console.print(f"\n[green]Found {len(news_list)} news items[/green]\n")
    display_news_table(news_list, ticker)

    if skip_analysis:
        log_success("Skipping AI analysis as requested")
        return None

    # Analyze news
    results: list[AnalysisResult] = []
    db = get_database() if save else None

    console.print(f"\n[bold]Running AI sentiment analysis...[/bold]\n")

    for i, news in enumerate(news_list, 1):
        # Check for duplicates if saving
        if db and db.check_duplicate(ticker, news.title):
            logger.debug(f"Skipping duplicate: {news.title[:50]}")
            continue

        analysis_dict = analyze_news_with_gemini(ticker, news.summary)

        result = AnalysisResult(
            news=news,
            ticker=ticker,
            analysis=None,
            error=None
        )

        if analysis_dict:
            try:
                from models import SentimentAnalysis
                result.analysis = SentimentAnalysis(
                    SENTIMENT=SentimentCategory(analysis_dict["SENTIMENT"]),
                    JUSTIFICATION=analysis_dict["JUSTIFICATION"]
                )
            except (ValueError, KeyError) as e:
                result.error = f"Invalid analysis response: {e}"
        else:
            result.error = "Analysis returned no result"

        results.append(result)
        display_analysis_result(result, i, len(news_list))

        # Save to database
        if db:
            db.save_result(result)

    # Generate summary
    sentiment_dist = {cat.value: 0 for cat in SentimentCategory}
    for r in results:
        if r.analysis:
            sentiment_dist[r.analysis.sentiment.value] += 1

    summary = AnalysisSummary(
        ticker=ticker,
        total_news=len(news_list),
        analyzed_count=sum(1 for r in results if r.is_successful),
        failed_count=sum(1 for r in results if not r.is_successful),
        sentiment_distribution=sentiment_dist,
        results=results
    )

    console.print("\n")
    display_summary(summary)

    if save:
        log_success(f"Results saved to database ({len(results)} records)")

    return summary


def show_database_summary(ticker: str):
    """Show summary from database for a ticker."""
    db = get_database()
    summary = db.get_sentiment_summary(ticker)

    if summary["total_analyzed"] == 0:
        log_warning(f"No analysis records found for {ticker}")
        return

    table = Table(title=f"Historical Sentiment Summary for {ticker.upper()}")
    table.add_column("Sentiment", style="cyan")
    table.add_column("Count", justify="right")

    for sentiment, count in summary["distribution"].items():
        table.add_row(sentiment, str(count))

    console.print(table)
    console.print(f"\n[dim]Total analyzed:[/dim] {summary['total_analyzed']}")


def main():
    """Main entry point."""
    args = parse_args()

    # Set up time range
    if args.time_from:
        time_from = parse_date(args.time_from)
    else:
        time_from = datetime.now() - timedelta(days=args.days)

    if args.time_to:
        time_to = parse_date(args.time_to)
    else:
        time_to = datetime.now()

    try:
        # Validate settings
        get_settings()
    except Exception as e:
        log_error("Configuration error", e)
        console.print("[red]Please ensure your .env file contains valid API keys[/red]")
        sys.exit(1)

    if args.summary:
        show_database_summary(args.ticker)
    else:
        run_analysis(
            ticker=args.ticker,
            time_from=time_from,
            time_to=time_to,
            save=args.save,
            skip_analysis=args.no_analyze,
            limit=args.limit
        )


if __name__ == "__main__":
    main()

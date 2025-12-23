#!/usr/bin/env python3
"""
IA Trading - Market Sentiment Analysis Tool

Analyzes news sentiment for stock tickers using AI to identify trading opportunities.
"""

import argparse
import sys
from datetime import datetime, timedelta
from typing import Optional, List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from config import get_settings
from models import NewsItem, AnalysisResult, SentimentCategory, AnalysisSummary
from news_retriever import get_news_data
from ia_analisis import analyze_news_with_gemini
from database import get_database
from logger import logger, log_success, log_warning, log_error
from exporter import exporter
from scoring import calculate_trend, SentimentScore

console = Console()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze market sentiment for stock tickers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s AAPL                        Analyze Apple news from last 7 days
  %(prog)s TSLA --days 30              Analyze Tesla news from last 30 days
  %(prog)s MSFT --from 2024-01-01      Analyze Microsoft from specific date
  %(prog)s NVDA --save                 Save results to database
  %(prog)s AMZN --summary              Show sentiment summary from database
  %(prog)s AAPL,MSFT,GOOGL --batch     Analyze multiple tickers
  %(prog)s TSLA --export json          Export results to JSON
  %(prog)s NVDA --export html          Generate HTML report
  %(prog)s AAPL --score                Show sentiment score and signal
        """
    )

    parser.add_argument(
        "ticker",
        type=str,
        help="Stock ticker symbol(s), comma-separated for batch (e.g., AAPL or AAPL,MSFT,GOOGL)"
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
        "--export",
        type=str,
        choices=["json", "csv", "html"],
        help="Export results to file (json, csv, or html)"
    )

    parser.add_argument(
        "--batch",
        action="store_true",
        help="Enable batch processing for multiple tickers"
    )

    parser.add_argument(
        "--score",
        action="store_true",
        help="Show sentiment score and trading signal"
    )

    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching, always fetch fresh data"
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


def display_score(score: SentimentScore):
    """Display sentiment score and trading signal."""
    signal_colors = {
        "STRONG BUY": "bold green",
        "BUY": "green",
        "HOLD": "yellow",
        "SELL": "red",
        "STRONG SELL": "bold red"
    }

    trend_icons = {
        "improving": "[green]↑[/green]",
        "declining": "[red]↓[/red]",
        "stable": "[yellow]→[/yellow]",
        "insufficient_data": "[dim]?[/dim]"
    }

    console.print(Panel(
        f"[bold]{score.ticker} Sentiment Score[/bold]",
        title="Score Analysis"
    ))

    color = signal_colors.get(score.signal, "white")
    trend = trend_icons.get(score.trend or "", "")

    console.print(f"[dim]Signal:[/dim] [{color}]{score.signal}[/{color}] {trend}")
    console.print(f"[dim]Sentiment:[/dim] {score.sentiment_label}")
    console.print(f"[dim]Score:[/dim] {score.normalized_score:+.2f} (scale: -1 to +1)")
    console.print(f"[dim]Confidence:[/dim] {score.confidence:.1%}")

    if score.time_weighted_score is not None:
        console.print(f"[dim]Time-weighted score:[/dim] {score.time_weighted_score:+.2f}")

    console.print(f"\n[dim]Breakdown:[/dim]")
    console.print(f"  [green]Positive:[/green] {score.positive_count}")
    console.print(f"  [yellow]Neutral:[/yellow] {score.neutral_count}")
    console.print(f"  [red]Negative:[/red] {score.negative_count}")


def run_analysis(
    ticker: str,
    time_from: datetime,
    time_to: datetime,
    save: bool = False,
    skip_analysis: bool = False,
    limit: int = 50,
    export_format: Optional[str] = None,
    show_score: bool = False,
    use_cache: bool = True
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

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Analyzing...", total=len(news_list))

        for i, news in enumerate(news_list, 1):
            # Check for duplicates if saving
            if db and db.check_duplicate(ticker, news.title):
                logger.debug(f"Skipping duplicate: {news.title[:50]}")
                progress.advance(task)
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
            progress.advance(task)

            # Save to database
            if db:
                db.save_result(result)

    # Display individual results
    for i, result in enumerate(results, 1):
        display_analysis_result(result, i, len(results))

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

    # Show score if requested
    if show_score and results:
        score = calculate_trend(results)
        if score:
            console.print("\n")
            display_score(score)

    # Export if requested
    if export_format and results:
        console.print("\n")
        if export_format == "json":
            filepath = exporter.to_json(results, ticker)
        elif export_format == "csv":
            filepath = exporter.to_csv(results, ticker)
        elif export_format == "html":
            filepath = exporter.to_html(summary)
        console.print(f"[dim]Exported to:[/dim] {filepath}")

    if save:
        log_success(f"Results saved to database ({len(results)} records)")

    return summary


def run_batch_analysis(
    tickers: List[str],
    time_from: datetime,
    time_to: datetime,
    save: bool = False,
    limit: int = 50,
    export_format: Optional[str] = None,
    show_score: bool = False
) -> dict:
    """Run analysis for multiple tickers."""
    results = {}

    console.print(Panel(
        f"[bold]Batch Analysis[/bold]\n"
        f"Tickers: {', '.join(tickers)}\n"
        f"Period: {time_from.strftime('%Y-%m-%d')} to {time_to.strftime('%Y-%m-%d')}",
        title="IA Trading - Batch Mode"
    ))

    for i, ticker in enumerate(tickers, 1):
        console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
        console.print(f"[bold]Processing {ticker} ({i}/{len(tickers)})[/bold]")
        console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")

        summary = run_analysis(
            ticker=ticker,
            time_from=time_from,
            time_to=time_to,
            save=save,
            limit=limit,
            export_format=export_format,
            show_score=show_score
        )

        if summary:
            results[ticker] = summary

    # Display batch summary
    if results and show_score:
        console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
        console.print("[bold]Batch Summary - All Tickers[/bold]")
        console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")

        table = Table(title="Sentiment Scores")
        table.add_column("Ticker", style="cyan")
        table.add_column("Signal", justify="center")
        table.add_column("Score", justify="right")
        table.add_column("Positive", justify="right", style="green")
        table.add_column("Neutral", justify="right", style="yellow")
        table.add_column("Negative", justify="right", style="red")

        signal_colors = {
            "STRONG BUY": "bold green",
            "BUY": "green",
            "HOLD": "yellow",
            "SELL": "red",
            "STRONG SELL": "bold red"
        }

        for ticker, summary in results.items():
            score = calculate_trend(summary.results)
            if score:
                color = signal_colors.get(score.signal, "white")
                table.add_row(
                    ticker,
                    f"[{color}]{score.signal}[/{color}]",
                    f"{score.normalized_score:+.2f}",
                    str(score.positive_count),
                    str(score.neutral_count),
                    str(score.negative_count)
                )

        console.print(table)

    return results


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

    # Parse tickers
    tickers = [t.strip().upper() for t in args.ticker.split(",")]

    if args.summary:
        for ticker in tickers:
            show_database_summary(ticker)
    elif args.batch or len(tickers) > 1:
        run_batch_analysis(
            tickers=tickers,
            time_from=time_from,
            time_to=time_to,
            save=args.save,
            limit=args.limit,
            export_format=args.export,
            show_score=args.score
        )
    else:
        run_analysis(
            ticker=tickers[0],
            time_from=time_from,
            time_to=time_to,
            save=args.save,
            skip_analysis=args.no_analyze,
            limit=args.limit,
            export_format=args.export,
            show_score=args.score,
            use_cache=not args.no_cache
        )


if __name__ == "__main__":
    main()

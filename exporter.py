"""Export functionality for analysis results."""

import csv
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from models import AnalysisResult, AnalysisSummary, SentimentCategory
from logger import logger, log_success


class Exporter:
    """Export analysis results to various formats."""

    def __init__(self, output_dir: str = "exports"):
        """
        Initialize the exporter.

        Args:
            output_dir: Directory to save export files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, ticker: str, format: str) -> Path:
        """Generate a unique filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.output_dir / f"{ticker}_{timestamp}.{format}"

    def to_json(
        self,
        results: List[AnalysisResult],
        ticker: str,
        filename: Optional[str] = None
    ) -> Path:
        """
        Export results to JSON file.

        Args:
            results: List of analysis results
            ticker: Stock ticker symbol
            filename: Optional custom filename

        Returns:
            Path to the exported file
        """
        if filename:
            filepath = self.output_dir / filename
        else:
            filepath = self._generate_filename(ticker, "json")

        data = {
            "ticker": ticker,
            "exported_at": datetime.now().isoformat(),
            "total_results": len(results),
            "results": [
                {
                    "title": r.news.title,
                    "summary": r.news.summary,
                    "published_date": r.news.published_date,
                    "source": r.news.source,
                    "url": r.news.url,
                    "sentiment": r.analysis.sentiment.value if r.analysis else None,
                    "justification": r.analysis.justification if r.analysis else None,
                    "analyzed_at": r.analyzed_at.isoformat(),
                    "error": r.error
                }
                for r in results
            ]
        }

        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        log_success(f"Exported {len(results)} results to {filepath}")
        return filepath

    def to_csv(
        self,
        results: List[AnalysisResult],
        ticker: str,
        filename: Optional[str] = None
    ) -> Path:
        """
        Export results to CSV file.

        Args:
            results: List of analysis results
            ticker: Stock ticker symbol
            filename: Optional custom filename

        Returns:
            Path to the exported file
        """
        if filename:
            filepath = self.output_dir / filename
        else:
            filepath = self._generate_filename(ticker, "csv")

        fieldnames = [
            "ticker",
            "title",
            "published_date",
            "source",
            "sentiment",
            "justification",
            "analyzed_at",
            "url",
            "error"
        ]

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for r in results:
                writer.writerow({
                    "ticker": ticker,
                    "title": r.news.title,
                    "published_date": r.news.published_date,
                    "source": r.news.source,
                    "sentiment": r.analysis.sentiment.value if r.analysis else "",
                    "justification": r.analysis.justification if r.analysis else "",
                    "analyzed_at": r.analyzed_at.isoformat(),
                    "url": r.news.url or "",
                    "error": r.error or ""
                })

        log_success(f"Exported {len(results)} results to {filepath}")
        return filepath

    def to_html(
        self,
        summary: AnalysisSummary,
        filename: Optional[str] = None
    ) -> Path:
        """
        Export summary to HTML report.

        Args:
            summary: Analysis summary
            filename: Optional custom filename

        Returns:
            Path to the exported file
        """
        if filename:
            filepath = self.output_dir / filename
        else:
            filepath = self._generate_filename(summary.ticker, "html")

        # Calculate sentiment percentages
        total = summary.analyzed_count or 1
        sentiment_data = []
        colors = {
            "Highly Positive": "#22c55e",
            "Positive": "#86efac",
            "Neutral": "#fbbf24",
            "Negative": "#f87171",
            "Highly Negative": "#dc2626"
        }

        for sentiment, count in summary.sentiment_distribution.items():
            pct = (count / total) * 100
            sentiment_data.append({
                "name": sentiment,
                "count": count,
                "pct": pct,
                "color": colors.get(sentiment, "#gray")
            })

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sentiment Analysis Report - {summary.ticker}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; color: #1e293b; line-height: 1.6; padding: 2rem; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
        .subtitle {{ color: #64748b; margin-bottom: 2rem; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .stat-card {{ background: white; padding: 1.5rem; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .stat-value {{ font-size: 2rem; font-weight: bold; color: #3b82f6; }}
        .stat-label {{ color: #64748b; font-size: 0.875rem; }}
        .chart {{ background: white; padding: 1.5rem; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 2rem; }}
        .bar-container {{ margin: 0.5rem 0; }}
        .bar-label {{ display: flex; justify-content: space-between; margin-bottom: 0.25rem; font-size: 0.875rem; }}
        .bar {{ height: 24px; border-radius: 4px; transition: width 0.3s; }}
        .results {{ background: white; border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden; }}
        .result-item {{ padding: 1rem 1.5rem; border-bottom: 1px solid #e2e8f0; }}
        .result-item:last-child {{ border-bottom: none; }}
        .result-title {{ font-weight: 600; margin-bottom: 0.5rem; }}
        .result-meta {{ display: flex; gap: 1rem; font-size: 0.875rem; color: #64748b; margin-bottom: 0.5rem; }}
        .sentiment-badge {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }}
        .justification {{ font-size: 0.875rem; color: #475569; font-style: italic; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Sentiment Analysis Report</h1>
        <p class="subtitle">{summary.ticker} - Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{summary.total_news}</div>
                <div class="stat-label">Total News</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary.analyzed_count}</div>
                <div class="stat-label">Analyzed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary.success_rate:.1f}%</div>
                <div class="stat-label">Success Rate</div>
            </div>
        </div>

        <div class="chart">
            <h2 style="margin-bottom: 1rem;">Sentiment Distribution</h2>
            {"".join(f'''
            <div class="bar-container">
                <div class="bar-label">
                    <span>{s["name"]}</span>
                    <span>{s["count"]} ({s["pct"]:.1f}%)</span>
                </div>
                <div class="bar" style="width: {s["pct"]}%; background: {s["color"]};"></div>
            </div>
            ''' for s in sentiment_data)}
        </div>

        <div class="results">
            <h2 style="padding: 1rem 1.5rem; border-bottom: 1px solid #e2e8f0;">Analysis Results</h2>
            {"".join(f'''
            <div class="result-item">
                <div class="result-title">{r.news.title[:100]}</div>
                <div class="result-meta">
                    <span>{r.news.published_date[:10] if len(r.news.published_date) >= 10 else r.news.published_date}</span>
                    <span>{r.news.source or "Unknown"}</span>
                    <span class="sentiment-badge" style="background: {colors.get(r.analysis.sentiment.value if r.analysis else "", "#e2e8f0")}; color: white;">
                        {r.analysis.sentiment.value if r.analysis else "Failed"}
                    </span>
                </div>
                <div class="justification">{r.analysis.justification if r.analysis else r.error or "No analysis"}</div>
            </div>
            ''' for r in summary.results[:50])}
        </div>
    </div>
</body>
</html>"""

        filepath.write_text(html)
        log_success(f"Exported HTML report to {filepath}")
        return filepath


# Global exporter instance
exporter = Exporter()

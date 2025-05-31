"""
Metrics reporting utilities.

This module provides utilities for periodically reporting
metrics to logs or external monitoring systems.
"""

import logging
import threading
import time
from datetime import datetime
from typing import Optional, Callable

from src.utils.metrics import metrics_collector

logger = logging.getLogger(__name__)


class MetricsReporter:
    """Periodically reports metrics to configured destinations."""
    
    def __init__(self, interval_seconds: int = 300):  # 5 minutes default
        """
        Initialize metrics reporter.
        
        Args:
            interval_seconds: Reporting interval in seconds
        """
        self.interval_seconds = interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: list[Callable] = []
    
    def add_callback(self, callback: Callable) -> None:
        """Add a callback to be called with metrics data."""
        self._callbacks.append(callback)
    
    def start(self) -> None:
        """Start the metrics reporting thread."""
        if self._running:
            logger.warning("Metrics reporter already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"Metrics reporter started with {self.interval_seconds}s interval")
    
    def stop(self) -> None:
        """Stop the metrics reporting thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Metrics reporter stopped")
    
    def _run(self) -> None:
        """Main loop for metrics reporting."""
        while self._running:
            try:
                # Get metrics summary
                summary = metrics_collector.get_summary()
                
                # Log metrics
                self._log_metrics(summary)
                
                # Call callbacks
                for callback in self._callbacks:
                    try:
                        callback(summary)
                    except Exception as e:
                        logger.error(f"Error in metrics callback: {e}", exc_info=True)
                
                # Sleep until next interval
                time.sleep(self.interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in metrics reporter: {e}", exc_info=True)
                # Sleep on error to avoid tight loop
                time.sleep(30)
    
    def _log_metrics(self, summary: dict) -> None:
        """Log metrics summary."""
        # Calculate totals
        total_requests = sum(
            stats['count'] for stats in summary['request_types'].values()
        )
        
        if total_requests == 0:
            logger.info("No requests in the last metrics window")
            return
        
        # Calculate overall stats
        total_errors = summary['counters'].get('errors', 0)
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        # Log summary
        logger.info(
            f"Metrics Summary - Window: {summary['window_minutes']}min, "
            f"Requests: {total_requests}, "
            f"Errors: {total_errors} ({error_rate:.1f}%), "
            f"Slow: {summary['counters'].get('slow_requests', 0)}"
        )
        
        # Log per-request type if verbose
        if logger.isEnabledFor(logging.DEBUG):
            for request_type, stats in summary['request_types'].items():
                logger.debug(
                    f"  {request_type}: "
                    f"count={stats['count']}, "
                    f"avg={stats['avg_duration_ms']:.0f}ms, "
                    f"p95={stats['p95_duration_ms']:.0f}ms, "
                    f"errors={stats['error_count']}"
                )
    
    def report_now(self) -> dict:
        """Generate and return metrics report immediately."""
        summary = metrics_collector.get_summary()
        self._log_metrics(summary)
        
        # Call callbacks
        for callback in self._callbacks:
            try:
                callback(summary)
            except Exception as e:
                logger.error(f"Error in metrics callback: {e}", exc_info=True)
        
        return summary


# Global metrics reporter instance
metrics_reporter = MetricsReporter()


def format_metrics_for_slack(summary: dict) -> str:
    """
    Format metrics summary for Slack display.
    
    Args:
        summary: Metrics summary from collector
        
    Returns:
        Formatted string for Slack
    """
    lines = []
    
    # Header
    lines.append("*📊 Metrics Report*")
    lines.append(f"_Window: Last {summary['window_minutes']} minutes_")
    lines.append(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n")
    
    # Calculate totals
    total_requests = sum(
        stats['count'] for stats in summary['request_types'].values()
    )
    
    if total_requests == 0:
        lines.append("No requests recorded in this window.")
        return "\n".join(lines)
    
    total_errors = summary['counters'].get('errors', 0)
    error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
    
    # Overall stats
    lines.append("*Overall Performance:*")
    lines.append(f"• Total Requests: {total_requests}")
    lines.append(f"• Success Rate: {100 - error_rate:.1f}%")
    lines.append(f"• Errors: {total_errors}")
    lines.append(f"• Slow Requests (>3s): {summary['counters'].get('slow_requests', 0)}")
    
    # Top request types
    if summary['request_types']:
        lines.append("\n*Top Request Types:*")
        
        # Sort by count
        sorted_types = sorted(
            summary['request_types'].items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:5]  # Top 5
        
        for request_type, stats in sorted_types:
            emoji = "✅" if stats['error_rate'] < 0.05 else "⚠️" if stats['error_rate'] < 0.1 else "❌"
            lines.append(
                f"{emoji} `{request_type}`: "
                f"{stats['count']} requests, "
                f"avg {stats['avg_duration_ms']:.0f}ms"
            )
    
    # Alerts
    alerts = []
    
    # High error rate alert
    if error_rate > 10:
        alerts.append(f"🚨 High error rate: {error_rate:.1f}%")
    
    # Slow request types
    slow_types = [
        (req_type, stats) for req_type, stats in summary['request_types'].items()
        if stats['avg_duration_ms'] > 2000  # 2 seconds average
    ]
    
    if slow_types:
        alerts.append(
            f"🐌 Slow request types: {', '.join(t[0] for t in slow_types[:3])}"
        )
    
    if alerts:
        lines.append("\n*Alerts:*")
        lines.extend(alerts)
    
    return "\n".join(lines)
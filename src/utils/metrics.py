#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2025 Fábio Linhares
# -*- coding: utf-8 -*-
"""
============================================================================
SECS Chatbot - Coletor de métricas e estatísticas
============================================================================
Versão: 7.0
Data: 2025-12-04
Descrição: Coletor de métricas e estatísticas
Autoria: Fábio Linhares <fabio.linhares@edu.vertex.org.br>
Repositório: https://github.com/fabiolinhares/secs_chatbot
Licença: MIT
Compatibilidade: Python 3.11+
============================================================================
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import time
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Metric:
    """Single metric data point"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricStats:
    """Aggregated metric statistics"""
    count: int
    mean: float
    min: float
    max: float
    sum: float
    p50: float  # Median
    p95: float
    p99: float


class MetricsCollector:
    """Collects and aggregates metrics"""
    
    def __init__(self, retention_minutes: int = 60):
        self.metrics: List[Metric] = []
        self.retention = timedelta(minutes=retention_minutes)
        self.counters: Dict[str, int] = defaultdict(int)
    
    def record(self, name: str, value: float, **tags):
        """
        Record a metric.
        
        Args:
            name: Metric name
            value: Metric value
            **tags: Additional tags for filtering
            
        Example:
            metrics.record("chat.duration", 1.5, user_role="admin")
            metrics.record("cache.hit", 1, user_id="user123")
        """
        metric = Metric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            tags=tags
        )
        self.metrics.append(metric)
        
        logger.debug(
            f"Metric recorded: {name}",
            value=value,
            **tags
        )
    
    def increment(self, name: str, amount: int = 1, **tags):
        """
        Increment a counter.
        
        Args:
            name: Counter name
            amount: Amount to increment
            **tags: Additional tags
        """
        key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted(tags.items()))}"
        self.counters[key] += amount
        
        # Also record as metric
        self.record(name, amount, **tags)
    
    def get_stats(
        self,
        name: str,
        minutes: int = 60,
        **filter_tags
    ) -> Optional[MetricStats]:
        """
        Get statistics for a metric.
        
        Args:
            name: Metric name
            minutes: Time window in minutes
            **filter_tags: Tags to filter by
            
        Returns:
            MetricStats or None if no data
            
        Example:
            stats = metrics.get_stats("chat.duration", minutes=60, user_role="admin")
            print(f"Mean: {stats.mean}s, P95: {stats.p95}s")
        """
        cutoff = datetime.now() - timedelta(minutes=minutes)
        
        # Filter metrics
        values = []
        for m in self.metrics:
            if m.name != name or m.timestamp < cutoff:
                continue
            
            # Check tag filters
            if filter_tags and not all(
                m.tags.get(k) == v for k, v in filter_tags.items()
            ):
                continue
            
            values.append(m.value)
        
        if not values:
            return None
        
        # Calculate stats
        values.sort()
        n = len(values)
        
        return MetricStats(
            count=n,
            mean=sum(values) / n,
            min=min(values),
            max=max(values),
            sum=sum(values),
            p50=values[n // 2],
            p95=values[int(n * 0.95)] if n > 1 else values[0],
            p99=values[int(n * 0.99)] if n > 1 else values[0]
        )
    
    def get_counter(self, name: str, **tags) -> int:
        """Get counter value"""
        key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted(tags.items()))}"
        return self.counters.get(key, 0)
    
    def cleanup_old_metrics(self):
        """Remove metrics older than retention period"""
        cutoff = datetime.now() - self.retention
        before_count = len(self.metrics)
        
        self.metrics = [m for m in self.metrics if m.timestamp > cutoff]
        
        removed = before_count - len(self.metrics)
        if removed > 0:
            logger.debug(f"Cleaned up {removed} old metrics")
    
    def get_summary(self, minutes: int = 60) -> Dict[str, any]:
        """
        Get summary of all metrics.
        
        Returns:
            Dictionary with metric summaries
        """
        self.cleanup_old_metrics()
        
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [m for m in self.metrics if m.timestamp > cutoff]
        
        # Group by name
        by_name = defaultdict(list)
        for m in recent_metrics:
            by_name[m.name].append(m.value)
        
        summary = {}
        for name, values in by_name.items():
            if values:
                summary[name] = {
                    'count': len(values),
                    'mean': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values)
                }
        
        return summary


# Context manager for timing
class Timer:
    """
    Context manager for timing operations.
    
    Example:
        with Timer(metrics, "operation.duration", user_id="123"):
            # ... operation ...
    """
    def __init__(self, metrics: MetricsCollector, name: str, **tags):
        self.metrics = metrics
        self.name = name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.metrics.record(self.name, duration, **self.tags)
        
        if exc_type is not None:
            self.metrics.increment(f"{self.name}.error", **self.tags)


# Global metrics collector
_metrics_collector = None

def get_metrics_collector() -> MetricsCollector:
    """Get or create metrics collector singleton"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

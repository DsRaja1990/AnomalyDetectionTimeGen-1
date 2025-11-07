"""
Azure Monitor Metrics Query Client - CORRECTED VERSION
Handles querying Application Insights metrics using KQL (Kusto Query Language)
Includes enterprise-grade statistical analysis with 43 metrics

FIXED: Uses LogsQueryClient with KQL instead of deprecated MetricsQueryClient
Author: Azure Anomaly Detection System
Date: November 3, 2025
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import AzureError
import os
import statistics
from collections import Counter

logger = logging.getLogger(__name__)

# Log Analytics Workspace ID for KQL queries
WORKSPACE_ID = os.getenv("APPINSIGHTS_WORKSPACE_ID", "458f5c9d-edd4-4e76-97bf-a7babbb84c60")

# Metrics configuration - defines all metrics with their KQL queries
# Each metric has a KQL query that returns data points with timestamp and value
METRICS_CONFIG = {
    # ====================================================================
    # REQUEST METRICS - Using KQL queries on 'AppRequests' table
    # ====================================================================
    "request_count": {
        "kql_query": """
            AppRequests
            | where TimeGenerated > ago({timespan}m)
            | summarize value = count() by bin(TimeGenerated, 1m)
            | order by TimeGenerated asc
        """,
        "display_name": "Request Count",
        "unit": "count",
        "category": "AppRequests",
        "description": "Total number of HTTP AppRequests per minute"
    },
    "request_duration": {
        "kql_query": """
            AppRequests
            | where TimeGenerated > ago({timespan}m)
            | summarize value = avg(DurationMs) by bin(TimeGenerated, 1m)
            | order by TimeGenerated asc
        """,
        "display_name": "Request Duration",
        "unit": "milliseconds",
        "category": "AppRequests",
        "description": "Average request duration in milliseconds"
    },
    "request_failed": {
        "kql_query": """
            AppRequests
            | where TimeGenerated > ago({timespan}m)
            | where Success == false
            | extend value = 1
            | project TimeGenerated, value, ResultCode, Name, DurationMs
            | order by TimeGenerated asc
        """,
        "display_name": "Failed AppRequests",
        "unit": "count",
        "category": "AppRequests",
        "description": "Individual failed HTTP requests (not aggregated - for better spike detection)"
    },
    
    # ====================================================================
    # PERFORMANCE COUNTERS - Using KQL queries on 'AppPerformanceCounters' table
    # ====================================================================
    "cpu_usage": {
        "kql_query": """
            AppPerformanceCounters
            | where TimeGenerated > ago({timespan}m)
            | where Name == "% Processor Time" or Name == "Processor Time"
            | summarize value = avg(Value) by bin(TimeGenerated, 1m)
            | order by TimeGenerated asc
        """,
        "display_name": "CPU Usage",
        "unit": "percent",
        "category": "performance",
        "description": "Average CPU percentage across all processors"
    },
    "memory_available": {
        "kql_query": """
            AppPerformanceCounters
            | where TimeGenerated > ago({timespan}m)
            | where Name == "Available Bytes" or Name == "Available Memory"
            | summarize value = avg(Value) by bin(TimeGenerated, 1m)
            | order by TimeGenerated asc
        """,
        "display_name": "Available Memory",
        "unit": "bytes",
        "category": "performance",
        "description": "Average available memory in bytes"
    },
    "process_cpu": {
        "kql_query": """
            AppPerformanceCounters
            | where TimeGenerated > ago({timespan}m)
            | where Name == "Process CPU" or (Name contains "Process" and Name contains "CPU")
            | summarize value = avg(Value) by bin(TimeGenerated, 1m)
            | order by TimeGenerated asc
        """,
        "display_name": "Process CPU",
        "unit": "percent",
        "category": "performance",
        "description": "CPU percentage used by the application process"
    },
    "process_memory": {
        "kql_query": """
            AppPerformanceCounters
            | where TimeGenerated > ago({timespan}m)
            | where Name == "Private Bytes" or (Name contains "Process" and Name contains "Memory")
            | summarize value = avg(Value) by bin(TimeGenerated, 1m)
            | order by TimeGenerated asc
        """,
        "display_name": "Process Memory",
        "unit": "bytes",
        "category": "performance",
        "description": "Memory used by the application process in bytes"
    },
    
    # ====================================================================
    # EXCEPTION METRICS - Using KQL queries on 'AppExceptions' table
    # ====================================================================
    "exception_count": {
        "kql_query": """
            AppExceptions
            | where TimeGenerated > ago({timespan}m)
            | extend value = 1
            | project TimeGenerated, value, ExceptionType, Message, SeverityLevel
            | order by TimeGenerated asc
        """,
        "display_name": "Exception Count",
        "unit": "count",
        "category": "AppExceptions",
        "description": "Individual exceptions (not aggregated - for better spike detection)"
    },
    
    # ====================================================================
    # DEPENDENCY METRICS - Using KQL queries on 'AppDependencies' table
    # ====================================================================
    "dependency_calls": {
        "kql_query": """
            AppDependencies
            | where TimeGenerated > ago({timespan}m)
            | summarize value = count() by bin(TimeGenerated, 1m)
            | order by TimeGenerated asc
        """,
        "display_name": "Dependency Calls",
        "unit": "count",
        "category": "AppDependencies",
        "description": "Total number of calls to external AppDependencies"
    },
    "dependency_duration": {
        "kql_query": """
            AppDependencies
            | where TimeGenerated > ago({timespan}m)
            | summarize value = avg(DurationMs) by bin(TimeGenerated, 1m)
            | order by TimeGenerated asc
        """,
        "display_name": "Dependency Duration",
        "unit": "milliseconds",
        "category": "AppDependencies",
        "description": "Average duration of dependency calls"
    },
    "dependency_failed": {
        "kql_query": """
            AppDependencies
            | where TimeGenerated > ago({timespan}m)
            | where Success == false
            | summarize value = count() by bin(TimeGenerated, 1m)
            | order by TimeGenerated asc
        """,
        "display_name": "Failed AppDependencies",
        "unit": "count",
        "category": "AppDependencies",
        "description": "Number of failed dependency calls"
    },
    
    # ====================================================================
    # AVAILABILITY METRICS - Using Success rate from AppRequests
    # NOTE: AppAvailabilityResults table doesn't exist in this workspace
    # ====================================================================
    "availability_results": {
        "kql_query": """
            AppRequests
            | where TimeGenerated > ago({timespan}m)
            | summarize 
                total = count(),
                successful = countif(Success == true)
            by bin(TimeGenerated, 1m)
            | extend value = (successful * 100.0 / total)
            | project TimeGenerated, value
            | order by TimeGenerated asc
        """,
        "display_name": "Request Success Rate",
        "unit": "percent",
        "category": "availability",
        "description": "Percentage of successful HTTP requests (AppAvailabilityResults table not available)"
    },
    
    # ====================================================================
    # BROWSER TIMING - Using AppEvents for custom client-side metrics
    # NOTE: AppPageViews table doesn't exist in this workspace
    # ====================================================================
    "page_view_load_time": {
        "kql_query": """
            AppEvents
            | where TimeGenerated > ago({timespan}m)
            | where Name contains "pageView" or Name contains "PageLoad"
            | extend DurationMs = todouble(Properties.duration)
            | where isnotnull(DurationMs)
            | summarize value = avg(DurationMs) by bin(TimeGenerated, 1m)
            | order by TimeGenerated asc
        """,
        "display_name": "Page Load Time",
        "unit": "milliseconds",
        "category": "browser",
        "description": "Average page load time from custom events (AppPageViews table not available)"
    },
    
    # ====================================================================
    # CUSTOM METRICS - Using KQL queries on 'AppMetrics' table
    # ====================================================================
    "custom_metric_1": {
        "kql_query": """
            AppMetrics
            | where TimeGenerated > ago({timespan}m)
            | where Name == "Metric1"
            | summarize value = avg(Sum) by bin(TimeGenerated, 1m)
            | order by TimeGenerated asc
        """,
        "display_name": "Custom Metric 1",
        "unit": "count",
        "category": "custom",
        "description": "Custom application metric 1"
    },
    "custom_metric_2": {
        "kql_query": """
            AppMetrics
            | where TimeGenerated > ago({timespan}m)
            | where Name == "Metric2"
            | summarize value = avg(Sum) by bin(TimeGenerated, 1m)
            | order by TimeGenerated asc
        """,
        "display_name": "Custom Metric 2",
        "unit": "milliseconds",
        "category": "custom",
        "description": "Custom application metric 2"
    },
    
    # ====================================================================
    # SERVER RESPONSE METRICS
    # ====================================================================
    "server_response_time": {
        "kql_query": """
            AppRequests
            | where TimeGenerated > ago({timespan}m)
            | summarize value = avg(DurationMs) by bin(TimeGenerated, 1m)
            | order by TimeGenerated asc
        """,
        "display_name": "Server Response Time",
        "unit": "milliseconds",
        "category": "performance",
        "description": "Average server-side request execution time"
    },
    
    # ====================================================================
    # DATABASE METRICS - SQL AppDependencies
    # ====================================================================
    "database_calls": {
        "kql_query": """
            AppDependencies
            | where TimeGenerated > ago({timespan}m)
            | where DependencyType == "SQL" or DependencyType == "Azure table" or DependencyType == "Azure SQL"
            | summarize value = avg(DurationMs) by bin(TimeGenerated, 1m)
            | order by TimeGenerated asc
        """,
        "display_name": "Database Call Duration",
        "unit": "milliseconds",
        "category": "database",
        "description": "Average duration of database calls"
    },
    
    # ====================================================================
    # HTTP STATUS CODES - Filtering by result code
    # ====================================================================
    "http_5xx_errors": {
        "kql_query": """
            AppRequests
            | where TimeGenerated > ago({timespan}m)
            | where ResultCode startswith "5"
            | summarize value = count() by bin(TimeGenerated, 1m)
            | order by TimeGenerated asc
        """,
        "display_name": "5xx Server Errors",
        "unit": "count",
        "category": "errors",
        "description": "HTTP 5xx server errors"
    },
    "http_4xx_errors": {
        "kql_query": """
            AppRequests
            | where TimeGenerated > ago({timespan}m)
            | where ResultCode startswith "4"
            | summarize value = count() by bin(TimeGenerated, 1m)
            | order by TimeGenerated asc
        """,
        "display_name": "4xx Client Errors",
        "unit": "count",
        "category": "errors",
        "description": "HTTP 4xx client errors"
    },
    
    # ====================================================================
    # TRAFFIC METRICS - Unique users
    # ====================================================================
    "user_sessions": {
        "kql_query": """
            AppRequests
            | where TimeGenerated > ago({timespan}m)
            | summarize value = dcount(UserId) by bin(TimeGenerated, 1m)
            | order by TimeGenerated asc
        """,
        "display_name": "Active User Sessions",
        "unit": "count",
        "category": "traffic",
        "description": "Count of distinct active users"
    },
}


class MetricsQueryClient:
    """
    Client for querying Azure Monitor metrics using KQL (Kusto Query Language)
    Provides enterprise-grade analysis with 43 statistical metrics
    
    This class replaces the deprecated MetricsQueryClient with LogsQueryClient
    and uses KQL queries for powerful, flexible metric analysis.
    """
    
    def __init__(self, credential: Optional[DefaultAzureCredential] = None, workspace_id: Optional[str] = None):
        """
        Initialize the metrics query client
        
        Args:
            credential: Azure credential for authentication (uses DefaultAzureCredential if not provided)
            workspace_id: Log Analytics Workspace ID (uses env var APPINSIGHTS_WORKSPACE_ID if not provided)
        """
        self.credential = credential or DefaultAzureCredential()
        self.client = LogsQueryClient(self.credential)
        self.workspace_id = workspace_id or WORKSPACE_ID
        logger.info(f"MetricsQueryClient initialized with workspace: {self.workspace_id[:8]}...")
    
    def query_metric(
        self,
        metric_key: str,
        timespan_minutes: int = 10
    ) -> List[Dict]:
        """
        Query a single metric using KQL
        
        Args:
            metric_key: Key from METRICS_CONFIG (e.g., 'request_count', 'cpu_usage')
            timespan_minutes: Time range to query in minutes (default 10)
            
        Returns:
            List of data points with timestamp and value, sorted by timestamp
            
        Example:
            >>> client = MetricsQueryClient()
            >>> data = client.query_metric("request_count", timespan_minutes=30)
            >>> print(f"Found {len(data)} data points")
        """
        try:
            if metric_key not in METRICS_CONFIG:
                logger.error(f"Unknown metric key: {metric_key}")
                return []
            
            metric_config = METRICS_CONFIG[metric_key]
            
            # Format the KQL query with timespan
            kql_query = metric_config["kql_query"].format(timespan=timespan_minutes)
            
            logger.debug(f"Executing KQL query for {metric_key}: {kql_query[:100]}...")
            
            # Execute KQL query
            response = self.client.query_workspace(
                workspace_id=self.workspace_id,
                query=kql_query,
                timespan=timedelta(minutes=timespan_minutes)
            )
            
            # Parse results
            data_points = []
            if response.status == LogsQueryStatus.SUCCESS:
                for table in response.tables:
                    for row in table.rows:
                        # KQL returns [timestamp, value]
                        if len(row) >= 2:
                            try:
                                timestamp = row[0] if isinstance(row[0], datetime) else datetime.fromisoformat(str(row[0]).replace('Z', '+00:00'))
                                value = float(row[1]) if row[1] is not None else 0.0
                                data_points.append({
                                    "timestamp": timestamp,
                                    "value": value
                                })
                            except (ValueError, TypeError) as e:
                                logger.warning(f"Failed to parse row {row}: {str(e)}")
                                continue
            elif response.status == LogsQueryStatus.PARTIAL:
                logger.warning(f"Partial response for {metric_key}: {response.partial_error}")
            else:
                logger.error(f"Query failed for {metric_key}: {response.status}")
            
            logger.info(f"Queried {metric_key}: {len(data_points)} data points")
            return sorted(data_points, key=lambda x: x["timestamp"])
            
        except AzureError as e:
            logger.error(f"Azure error querying metric {metric_key}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error querying {metric_key}: {str(e)}")
            return []
    
    def query_multiple_metrics(
        self,
        metric_keys: List[str],
        timespan_minutes: int = 10
    ) -> Dict[str, List[Dict]]:
        """
        Query multiple metrics efficiently
        
        Args:
            metric_keys: List of metric keys from METRICS_CONFIG
            timespan_minutes: Time range to query in minutes
            
        Returns:
            Dictionary mapping metric keys to their data points
            
        Example:
            >>> client = MetricsQueryClient()
            >>> metrics = ["request_count", "request_duration", "cpu_usage"]
            >>> results = client.query_multiple_metrics(metrics, timespan_minutes=15)
            >>> for metric, data in results.items():
            ...     print(f"{metric}: {len(data)} points")
        """
        results = {}
        
        for metric_key in metric_keys:
            if metric_key not in METRICS_CONFIG:
                logger.warning(f"Unknown metric key: {metric_key}")
                continue
            
            data_points = self.query_metric(metric_key, timespan_minutes)
            results[metric_key] = data_points
        
        return results
    
    def query_all_metrics(
        self,
        timespan_minutes: int = 10,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Dict]:
        """
        Query all configured metrics and calculate statistics
        
        Args:
            timespan_minutes: Time range to query in minutes
            categories: Optional list of categories to filter (e.g., ['AppRequests', 'performance'])
            
        Returns:
            Dictionary with metrics data and statistics
            
        Example:
            >>> client = MetricsQueryClient()
            >>> results = client.query_all_metrics(timespan_minutes=30, categories=["AppRequests", "performance"])
            >>> for metric_key, data in results.items():
            ...     stats = data['statistics']
            ...     print(f"{metric_key}: Mean={stats['central_tendency']['mean']:.2f}")
        """
        # Filter metrics by category if specified
        if categories:
            metric_keys = [key for key, config in METRICS_CONFIG.items() 
                          if config.get("category") in categories]
        else:
            metric_keys = list(METRICS_CONFIG.keys())
        
        metrics_data = self.query_multiple_metrics(metric_keys, timespan_minutes)
        
        # Calculate statistics for each metric
        results = {}
        for metric_key, data_points in metrics_data.items():
            config = METRICS_CONFIG[metric_key]
            stats = self.calculate_statistics(data_points)
            
            results[metric_key] = {
                "config": config,
                "data_points": data_points,
                "statistics": stats,
                "data_quality": {
                    "point_count": len(data_points),
                    "has_sufficient_data": len(data_points) >= 5,
                    "time_coverage_minutes": (data_points[-1]["timestamp"] - data_points[0]["timestamp"]).total_seconds() / 60 if len(data_points) >= 2 else 0
                }
            }
        
        return results
    
    def get_metric_by_category(
        self,
        category: str,
        timespan_minutes: int = 10
    ) -> Dict[str, Dict]:
        """
        Query all metrics in a specific category
        
        Args:
            category: Category name (e.g., 'AppRequests', 'performance', 'AppExceptions')
            timespan_minutes: Time range to query in minutes
            
        Returns:
            Dictionary with metrics data for the category
            
        Example:
            >>> client = MetricsQueryClient()
            >>> perf_metrics = client.get_metric_by_category("performance", timespan_minutes=20)
        """
        return self.query_all_metrics(timespan_minutes, categories=[category])
    
    def query_correlated_metrics(
        self,
        primary_metric: str,
        correlation_metrics: List[str],
        timespan_minutes: int = 10
    ) -> Dict:
        """
        Query metrics that might be correlated for analysis
        Useful for detecting correlated anomalies (e.g., CPU spike + high latency)
        
        Args:
            primary_metric: The main metric of interest
            correlation_metrics: List of metrics to correlate with primary
            timespan_minutes: Time range to query in minutes
            
        Returns:
            Dictionary with primary metric data and correlated metrics
            
        Example:
            >>> client = MetricsQueryClient()
            >>> results = client.query_correlated_metrics(
            ...     primary_metric="request_duration",
            ...     correlation_metrics=["cpu_usage", "memory_available"],
            ...     timespan_minutes=15
            ... )
            >>> print(f"Primary trend: {results['primary']['statistics']['trend_analysis']['trend_classification']}")
        """
        all_metrics = [primary_metric] + correlation_metrics
        results = self.query_multiple_metrics(all_metrics, timespan_minutes)
        
        return {
            "primary": {
                "metric": primary_metric,
                "data": results.get(primary_metric, []),
                "statistics": self.calculate_statistics(results.get(primary_metric, []))
            },
            "correlated": {
                metric: {
                    "data": results.get(metric, []),
                    "statistics": self.calculate_statistics(results.get(metric, []))
                }
                for metric in correlation_metrics
            }
        }
    
    def calculate_statistics(self, data_points: List[Dict]) -> Dict:
        """
        Calculate comprehensive enterprise-grade statistics (43 metrics)
        
        This is the heart of the anomaly detection system. It calculates:
        - 8 central tendency metrics
        - 3 dispersion metrics
        - 8 distribution metrics
        - 4 trend metrics
        - 3 predictive metrics
        - 4 anomaly detection metrics
        - 4 time-series pattern metrics
        - 3 enterprise scores
        - 3 health indicators
        
        Total: 43 statistical metrics for comprehensive analysis
        
        Args:
            data_points: List of dictionaries with 'timestamp' and 'value' keys
            
        Returns:
            Dictionary containing 43 statistical metrics organized by category
        """
        if not data_points or len(data_points) < 2:
            return self._get_empty_statistics()
        
        # Extract values for calculations
        values = [point["value"] for point in data_points]
        n = len(values)
        
        # Sort values for percentile calculations
        sorted_values = sorted(values)
        
        # ========================================
        # 1. CENTRAL TENDENCY METRICS (8 metrics)
        # ========================================
        mean_value = statistics.mean(values)
        median_value = statistics.median(values)
        
        # Weighted mean (more recent values weighted higher)
        weights = list(range(1, n + 1))
        weighted_mean = sum(v * w for v, w in zip(values, weights)) / sum(weights)
        
        latest_value = values[-1]
        min_value = min(values)
        max_value = max(values)
        value_range = max_value - min_value
        
        central_tendency = {
            "mean": mean_value,
            "median": median_value,
            "weighted_mean": weighted_mean,
            "latest_value": latest_value,
            "min": min_value,
            "max": max_value,
            "range": value_range,
            "count": n
        }
        
        # ========================================
        # 2. DISPERSION METRICS (3 metrics)
        # ========================================
        std_dev = statistics.stdev(values) if n > 1 else 0.0
        variance = statistics.variance(values) if n > 1 else 0.0
        coefficient_of_variation = (std_dev / mean_value * 100) if mean_value != 0 else 0.0
        
        dispersion = {
            "std_dev": std_dev,
            "variance": variance,
            "coefficient_of_variation": coefficient_of_variation
        }
        
        # ========================================
        # 3. DISTRIBUTION METRICS (8 metrics)
        # ========================================
        def percentile(data, p):
            """Calculate percentile"""
            k = (len(data) - 1) * p
            f = int(k)
            c = f + 1 if f + 1 < len(data) else f
            if c == f:
                return data[f]
            return data[f] + (data[c] - data[f]) * (k - f)
        
        p10 = percentile(sorted_values, 0.10)
        p25 = percentile(sorted_values, 0.25)
        p50 = percentile(sorted_values, 0.50)  # Same as median
        p75 = percentile(sorted_values, 0.75)
        p90 = percentile(sorted_values, 0.90)
        p95 = percentile(sorted_values, 0.95)
        p99 = percentile(sorted_values, 0.99)
        
        iqr = p75 - p25
        
        # Skewness (measure of asymmetry)
        if std_dev > 0:
            skewness = sum((v - mean_value) ** 3 for v in values) / (n * (std_dev ** 3))
        else:
            skewness = 0.0
        
        distribution = {
            "p10": p10,
            "p25": p25,
            "p50": p50,
            "p75": p75,
            "p90": p90,
            "p95": p95,
            "p99": p99,
            "iqr": iqr,
            "skewness": skewness
        }
        
        # ========================================
        # 4. TREND ANALYSIS METRICS (4 metrics)
        # ========================================
        # Calculate velocity (rate of change)
        if n >= 2:
            time_diffs = [(data_points[i]["timestamp"] - data_points[i-1]["timestamp"]).total_seconds() / 60 
                         for i in range(1, n)]
            avg_time_diff = statistics.mean(time_diffs) if time_diffs else 1.0
            
            value_diffs = [values[i] - values[i-1] for i in range(1, n)]
            velocity = statistics.mean(value_diffs) / avg_time_diff if avg_time_diff > 0 else 0.0
            
            # Calculate acceleration (rate of change of velocity)
            if n >= 3:
                velocity_diffs = [value_diffs[i] - value_diffs[i-1] for i in range(1, len(value_diffs))]
                acceleration = statistics.mean(velocity_diffs) / avg_time_diff if avg_time_diff > 0 else 0.0
            else:
                acceleration = 0.0
        else:
            velocity = 0.0
            acceleration = 0.0
        
        # Momentum (weighted velocity)
        momentum = velocity * (latest_value / mean_value if mean_value != 0 else 1.0)
        
        # Trend classification
        if abs(velocity) < 0.01:
            trend_classification = "stable"
        elif velocity > 0:
            if acceleration > 0:
                trend_classification = "accelerating_increase"
            else:
                trend_classification = "increasing"
        else:
            if acceleration < 0:
                trend_classification = "accelerating_decrease"
            else:
                trend_classification = "decreasing"
        
        trend_analysis = {
            "velocity": velocity,
            "acceleration": acceleration,
            "momentum": momentum,
            "trend_classification": trend_classification
        }
        
        # ========================================
        # 5. PREDICTIVE METRICS (3 metrics)
        # ========================================
        # Simple linear regression forecast
        if n >= 3:
            x = list(range(n))
            mean_x = statistics.mean(x)
            mean_y = mean_value
            
            numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
            denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
            
            if denominator != 0:
                slope = numerator / denominator
                intercept = mean_y - slope * mean_x
                forecast_next = slope * n + intercept
            else:
                forecast_next = latest_value
        else:
            forecast_next = latest_value
        
        # Confidence intervals (68% and 95%)
        ci_68_lower = forecast_next - std_dev
        ci_68_upper = forecast_next + std_dev
        ci_95_lower = forecast_next - (2 * std_dev)
        ci_95_upper = forecast_next + (2 * std_dev)
        
        predictive = {
            "forecast_next": forecast_next,
            "confidence_interval_68": {
                "lower": ci_68_lower,
                "upper": ci_68_upper
            },
            "confidence_interval_95": {
                "lower": ci_95_lower,
                "upper": ci_95_upper
            }
        }
        
        # ========================================
        # 6. ANOMALY DETECTION METRICS (4 metrics)
        # ========================================
        # Z-score (standard score)
        z_score = (latest_value - mean_value) / std_dev if std_dev > 0 else 0.0
        
        # Modified Z-score (using median absolute deviation)
        mad = statistics.median([abs(v - median_value) for v in values])
        modified_z_score = 0.6745 * (latest_value - median_value) / mad if mad > 0 else 0.0
        
        # Isolation score (simple version based on distance from mean relative to range)
        isolation_score = abs(latest_value - mean_value) / value_range if value_range > 0 else 0.0
        
        # Percentile rank of latest value
        percentile_rank = sum(1 for v in values if v <= latest_value) / n * 100
        
        anomaly_detection = {
            "z_score": z_score,
            "modified_z_score": modified_z_score,
            "isolation_score": isolation_score,
            "percentile_rank": percentile_rank
        }
        
        # ========================================
        # 7. TIME-SERIES PATTERN METRICS (4 metrics)
        # ========================================
        # Volatility (standard deviation of returns)
        if n >= 2:
            returns = [(values[i] - values[i-1]) / values[i-1] if values[i-1] != 0 else 0 
                      for i in range(1, n)]
            volatility = statistics.stdev(returns) if len(returns) > 1 else 0.0
        else:
            volatility = 0.0
        
        # Stability score (inverse of coefficient of variation)
        stability_score = 100 / (1 + coefficient_of_variation) if coefficient_of_variation >= 0 else 0.0
        
        # Range ratio (current range vs historical range)
        if n >= 4:
            first_half_range = max(values[:n//2]) - min(values[:n//2])
            second_half_range = max(values[n//2:]) - min(values[n//2:])
            range_ratio = second_half_range / first_half_range if first_half_range > 0 else 1.0
        else:
            range_ratio = 1.0
        
        # Moving average convergence
        if n >= 4:
            short_ma = statistics.mean(values[-min(3, n):])
            long_ma = mean_value
            ma_convergence = ((short_ma - long_ma) / long_ma * 100) if long_ma != 0 else 0.0
        else:
            ma_convergence = 0.0
        
        time_series_patterns = {
            "volatility": volatility,
            "stability_score": stability_score,
            "range_ratio": range_ratio,
            "moving_average_convergence": ma_convergence
        }
        
        # ========================================
        # 8. ENTERPRISE SCORES (3 metrics)
        # ========================================
        # Composite anomaly score (0-100)
        anomaly_score = min(100, (
            abs(z_score) * 10 +
            abs(modified_z_score) * 10 +
            isolation_score * 30 +
            (abs(percentile_rank - 50) / 50) * 20 +
            abs(ma_convergence) / 2
        ))
        
        # Criticality score (0-100)
        criticality_score = min(100, (
            (abs(velocity) / (std_dev + 0.001)) * 20 +
            (abs(acceleration) / (std_dev + 0.001)) * 20 +
            (volatility / (mean_value + 0.001)) * 100 * 10 +
            anomaly_score * 0.5
        ))
        
        # Warning level (0-5)
        if anomaly_score < 20:
            warning_level = 0  # Normal
        elif anomaly_score < 40:
            warning_level = 1  # Monitor
        elif anomaly_score < 60:
            warning_level = 2  # Warning
        elif anomaly_score < 80:
            warning_level = 3  # Alert
        elif anomaly_score < 95:
            warning_level = 4  # Critical
        else:
            warning_level = 5  # Emergency
        
        enterprise_scores = {
            "anomaly_score": anomaly_score,
            "criticality_score": criticality_score,
            "warning_level": warning_level
        }
        
        # ========================================
        # 9. HEALTH INDICATORS (3 flags)
        # ========================================
        is_anomalous = anomaly_score > 60
        is_critical = criticality_score > 70
        requires_immediate_action = warning_level >= 4
        
        health_indicators = {
            "is_anomalous": is_anomalous,
            "is_critical": is_critical,
            "requires_immediate_action": requires_immediate_action
        }
        
        # ========================================
        # RETURN ALL 43 METRICS
        # ========================================
        return {
            "central_tendency": central_tendency,          # 8 metrics
            "dispersion": dispersion,                      # 3 metrics
            "distribution": distribution,                  # 8 metrics (p10, p25, p50, p75, p90, p95, p99, iqr)
            "trend_analysis": trend_analysis,              # 4 metrics
            "predictive": predictive,                      # 3 metrics (forecast + 2 CIs)
            "anomaly_detection": anomaly_detection,        # 4 metrics
            "time_series_patterns": time_series_patterns,  # 4 metrics
            "enterprise_scores": enterprise_scores,        # 3 metrics
            "health_indicators": health_indicators         # 3 flags
        }
    
    def _get_empty_statistics(self) -> Dict:
        """Return empty statistics structure when insufficient data"""
        return {
            "central_tendency": {
                "mean": 0.0, "median": 0.0, "weighted_mean": 0.0,
                "latest_value": 0.0, "min": 0.0, "max": 0.0,
                "range": 0.0, "count": 0
            },
            "dispersion": {
                "std_dev": 0.0, "variance": 0.0, "coefficient_of_variation": 0.0
            },
            "distribution": {
                "p10": 0.0, "p25": 0.0, "p50": 0.0, "p75": 0.0,
                "p90": 0.0, "p95": 0.0, "p99": 0.0, "iqr": 0.0, "skewness": 0.0
            },
            "trend_analysis": {
                "velocity": 0.0, "acceleration": 0.0, "momentum": 0.0,
                "trend_classification": "insufficient_data"
            },
            "predictive": {
                "forecast_next": 0.0,
                "confidence_interval_68": {"lower": 0.0, "upper": 0.0},
                "confidence_interval_95": {"lower": 0.0, "upper": 0.0}
            },
            "anomaly_detection": {
                "z_score": 0.0, "modified_z_score": 0.0,
                "isolation_score": 0.0, "percentile_rank": 0.0
            },
            "time_series_patterns": {
                "volatility": 0.0, "stability_score": 0.0,
                "range_ratio": 1.0, "moving_average_convergence": 0.0
            },
            "enterprise_scores": {
                "anomaly_score": 0.0, "criticality_score": 0.0, "warning_level": 0
            },
            "health_indicators": {
                "is_anomalous": False, "is_critical": False,
                "requires_immediate_action": False
            }
        }


# ====================================================================
# HELPER FUNCTIONS
# ====================================================================

def get_available_categories() -> List[str]:
    """Get list of all metric categories"""
    categories = set(config.get("category") for config in METRICS_CONFIG.values())
    return sorted(list(categories))


def get_metrics_by_category(category: str) -> List[str]:
    """Get all metric keys for a specific category"""
    return [key for key, config in METRICS_CONFIG.items() 
            if config.get("category") == category]


def format_metric_value(value: float, unit: str) -> str:
    """Format metric value with appropriate unit"""
    if unit == "bytes":
        # Convert to MB or GB
        if value > 1024 ** 3:
            return f"{value / (1024 ** 3):.2f} GB"
        elif value > 1024 ** 2:
            return f"{value / (1024 ** 2):.2f} MB"
        else:
            return f"{value / 1024:.2f} KB"
    elif unit == "milliseconds":
        if value > 1000:
            return f"{value / 1000:.2f} seconds"
        else:
            return f"{value:.2f} ms"
    elif unit == "percent":
        return f"{value:.2f}%"
    else:
        return f"{value:.2f} {unit}"


# ====================================================================
# FACTORY FUNCTION
# ====================================================================

def create_metrics_service() -> Optional[MetricsQueryClient]:
    """
    Factory function to create and return a MetricsQueryClient instance
    
    Returns:
        MetricsQueryClient instance if successful, None if configuration is missing
    """
    try:
        workspace_id = os.getenv("APPINSIGHTS_WORKSPACE_ID")
        if not workspace_id:
            logger.error("APPINSIGHTS_WORKSPACE_ID not configured")
            return None
        
        logger.info(f"Creating MetricsQueryClient for workspace: {workspace_id}")
        credential = DefaultAzureCredential()
        return MetricsQueryClient(credential=credential, workspace_id=workspace_id)
    except Exception as e:
        logger.error(f"Failed to create metrics service: {str(e)}")
        return None


# ====================================================================
# MODULE INFO
# ====================================================================
__version__ = "2.0.0"
__author__ = "Azure Anomaly Detection System"
__description__ = "KQL-based metrics query client with 43 enterprise statistics"




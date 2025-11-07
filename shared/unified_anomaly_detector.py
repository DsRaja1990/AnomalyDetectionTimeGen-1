"""
Unified Anomaly Detector - Complete Pre-Detection System
Combines logs analysis, metrics analysis, and trend detection for robust pre-detection.

This module provides:
1. Application Log Anomaly Detection (error spikes, cascades, resource exhaustion)
2. Metrics Trend Analysis (correlations, seasonal patterns, drift)
3. Unified Pre-Detection Engine (log + metric anomalies combined)
4. AI-Powered Root Cause Analysis with context
5. Comprehensive alerting with actionable recommendations

Architecture:
├─ Logs Layer: Extract anomalies from application logs (pre-metric spikes)
├─ Metrics Layer: Detect anomalies in system metrics (performance, resources)
├─ Trends Layer: Analyze time-series patterns and correlations
├─ Correlation Layer: Find relationships between logs and metrics
└─ AI Layer: Synthesize findings into root causes and recommendations
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict, field
import statistics
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)


class AnomalySeverity(Enum):
    """Severity levels for anomalies"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(Enum):
    """Types of anomalies detected"""
    ERROR_SPIKE = "error_spike"
    ERROR_PATTERN = "error_pattern"
    ERROR_CASCADE = "error_cascade"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    SERVICE_FAILURE = "service_failure"
    METRIC_SPIKE = "metric_spike"
    METRIC_TREND = "metric_trend"
    CORRELATION = "correlation"
    SEASONAL_DEVIATION = "seasonal_deviation"
    PERFORMANCE_DEGRADATION = "performance_degradation"


@dataclass
class LogAnomaly:
    """Detected anomaly in application logs"""
    timestamp: str
    anomaly_type: str
    error_category: str
    count: int
    severity: str
    confidence: float
    description: str
    patterns: List[str] = field(default_factory=list)
    recommendation: Optional[str] = None
    related_logs: List[str] = field(default_factory=list)


@dataclass
class MetricAnomaly:
    """Detected anomaly in metrics"""
    timestamp: str
    metric_name: str
    anomaly_type: str
    current_value: float
    baseline_value: float
    deviation_percent: float
    severity: str
    confidence: float
    description: str
    trend: str = "unknown"
    correlation_metrics: List[str] = field(default_factory=list)


@dataclass
class UnifiedAnomaly:
    """Complete anomaly with logs + metrics + correlations"""
    timestamp: str
    severity: str
    confidence: float
    description: str
    anomaly_count: int
    
    log_anomalies: List[LogAnomaly] = field(default_factory=list)
    metric_anomalies: List[MetricAnomaly] = field(default_factory=list)
    
    root_cause: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    prevention_strategies: List[str] = field(default_factory=list)
    
    affected_systems: List[str] = field(default_factory=list)
    impact_score: float = 0.0
    early_warning_time_minutes: int = 0


class UnifiedAnomalyDetector:
    """
    Unified anomaly detection combining logs, metrics, and trends.
    
    Detection Pipeline:
    1. Parse and categorize application logs
    2. Analyze metric time-series
    3. Detect log anomalies (8 categories)
    4. Detect metric anomalies (spike, trend, correlation)
    5. Correlate findings across logs and metrics
    6. Calculate unified severity and confidence
    7. Generate AI-ready anomaly context
    """
    
    # Error categories for log classification
    ERROR_CATEGORIES = {
        "database": ["sql", "db", "database", "connection", "timeout", "deadlock", "query"],
        "authentication": ["401", "403", "unauthorized", "forbidden", "auth", "token", "jwt"],
        "not_found": ["404", "notfound", "not found"],
        "server_error": ["500", "502", "503", "504", "internal server error", "bad gateway"],
        "resource_exhaustion": ["memory", "cpu", "connection", "thread", "pool", "oom"],
        "third_party": ["external", "api", "gateway", "timeout", "rate limit", "throttle"],
        "business_logic": ["validation", "constraint", "business", "rule"],
        "unknown": []
    }
    
    # System components for correlation
    SYSTEM_COMPONENTS = {
        "database": ["database_calls", "database_duration", "database_failed"],
        "network": ["dependency_calls", "dependency_duration", "dependency_failed"],
        "compute": ["cpu_usage", "process_cpu", "process_memory"],
        "requests": ["request_count", "request_duration", "request_failed"],
        "exceptions": ["exception_count"],
    }
    
    def __init__(
        self,
        error_threshold: int = 5,
        spike_multiplier: float = 2.5,
        lookback_minutes: int = 60,
        correlation_threshold: float = 0.7,
        metric_spike_threshold: float = 2.0
    ):
        """
        Initialize unified detector
        
        Args:
            error_threshold: Minimum error count to flag
            spike_multiplier: How much increase = spike (2.5x)
            lookback_minutes: Analysis window
            correlation_threshold: Minimum correlation coefficient
            metric_spike_threshold: Metric spike multiplier vs baseline
        """
        self.error_threshold = error_threshold
        self.spike_multiplier = spike_multiplier
        self.lookback_minutes = lookback_minutes
        self.correlation_threshold = correlation_threshold
        self.metric_spike_threshold = metric_spike_threshold
        
        logger.info(f"UnifiedAnomalyDetector initialized: "
                   f"error_threshold={error_threshold}, "
                   f"spike_multiplier={spike_multiplier}, "
                   f"lookback_minutes={lookback_minutes}")
    
    def detect_anomalies(
        self,
        logs: List[Dict],
        metrics: Dict[str, Dict],
        historical_baseline: Optional[Dict] = None
    ) -> UnifiedAnomaly:
        """
        Unified anomaly detection combining logs and metrics
        
        Args:
            logs: Application log entries
            metrics: Current metric statistics
            historical_baseline: Previous baseline for comparison
            
        Returns:
            UnifiedAnomaly with all findings and correlations
        """
        timestamp = datetime.utcnow().isoformat()
        
        try:
            # Phase 1: Analyze logs
            log_anomalies = self._detect_log_anomalies(logs, historical_baseline)
            
            # Phase 2: Analyze metrics
            metric_anomalies = self._detect_metric_anomalies(metrics, historical_baseline)
            
            # Phase 3: Analyze trends and patterns
            trend_anomalies = self._analyze_trends(metrics, historical_baseline)
            metric_anomalies.extend(trend_anomalies)
            
            # Phase 4: Correlate findings
            correlations = self._correlate_anomalies(log_anomalies, metric_anomalies)
            
            # Phase 5: Calculate unified severity
            severity, confidence = self._calculate_unified_severity(
                log_anomalies, metric_anomalies, correlations
            )
            
            # Phase 6: Identify affected systems
            affected_systems = self._identify_affected_systems(
                log_anomalies, metric_anomalies
            )
            
            # Phase 7: Generate description
            description = self._generate_unified_description(
                log_anomalies, metric_anomalies, correlations
            )
            
            # Phase 8: Calculate impact score
            impact_score = self._calculate_impact_score(
                log_anomalies, metric_anomalies, correlations
            )
            
            # Phase 9: Estimate early warning time
            early_warning_time = self._estimate_early_warning_time(
                log_anomalies, metric_anomalies
            )
            
            # Create unified anomaly
            unified = UnifiedAnomaly(
                timestamp=timestamp,
                severity=severity,
                confidence=confidence,
                description=description,
                anomaly_count=len(log_anomalies) + len(metric_anomalies),
                log_anomalies=log_anomalies,
                metric_anomalies=metric_anomalies,
                affected_systems=affected_systems,
                impact_score=impact_score,
                early_warning_time_minutes=early_warning_time
            )
            
            # Phase 10: Generate recommendations
            unified.recommendations = self._generate_recommendations(
                log_anomalies, metric_anomalies, affected_systems
            )
            unified.prevention_strategies = self._generate_prevention_strategies(
                log_anomalies, metric_anomalies
            )
            
            logger.info(f"Unified detection complete: "
                       f"severity={severity}, confidence={confidence:.2%}, "
                       f"log_anomalies={len(log_anomalies)}, "
                       f"metric_anomalies={len(metric_anomalies)}, "
                       f"correlations={len(correlations)}")
            
            return unified
            
        except Exception as e:
            logger.error(f"Error in unified anomaly detection: {e}", exc_info=True)
            return self._create_error_anomaly(timestamp, str(e))
    
    def _detect_log_anomalies(
        self,
        logs: List[Dict],
        historical_baseline: Optional[Dict] = None
    ) -> List[LogAnomaly]:
        """Detect anomalies in application logs"""
        anomalies = []
        
        if not logs:
            return anomalies
        
        # Parse logs
        parsed_logs = self._parse_logs(logs)
        
        # Aggregate statistics
        error_stats = self._aggregate_error_stats(parsed_logs)
        
        # Detect spikes
        anomalies.extend(self._detect_log_spikes(error_stats, historical_baseline))
        
        # Detect patterns
        anomalies.extend(self._detect_error_patterns(error_stats, parsed_logs))
        
        # Detect cascades
        anomalies.extend(self._detect_error_cascades(parsed_logs))
        
        # Detect resource exhaustion
        anomalies.extend(self._detect_resource_issues(parsed_logs))
        
        # Detect service failures
        anomalies.extend(self._detect_service_failures(parsed_logs))
        
        return sorted(
            anomalies,
            key=lambda x: (
                {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(x.severity, 0),
                x.confidence
            ),
            reverse=True
        )
    
    def _parse_logs(self, logs: List[Dict]) -> List[Dict]:
        """Parse and normalize log entries"""
        parsed = []
        
        for log in logs:
            try:
                parsed_log = {
                    "timestamp": log.get("timestamp", datetime.utcnow().isoformat()),
                    "level": log.get("level", "INFO").upper(),
                    "message": log.get("message", ""),
                    "exception": log.get("exception"),
                    "operation_name": log.get("operation_name", "unknown"),
                    "duration_ms": log.get("duration_ms", 0),
                    "status_code": log.get("status_code"),
                    "error_category": self._categorize_error(
                        log.get("message", ""),
                        log.get("exception")
                    )
                }
                parsed.append(parsed_log)
            except Exception as e:
                logger.warning(f"Error parsing log: {e}")
                continue
        
        return parsed
    
    def _categorize_error(self, message: str, exception: Optional[str] = None) -> str:
        """Categorize error by type"""
        full_text = f"{message} {exception or ''}".lower()
        
        for category, keywords in self.ERROR_CATEGORIES.items():
            if any(keyword in full_text for keyword in keywords):
                return category
        
        return "unknown"
    
    def _aggregate_error_stats(self, parsed_logs: List[Dict]) -> Dict:
        """Aggregate error statistics"""
        stats = {
            "total_errors": sum(1 for log in parsed_logs if log["level"] in ["ERROR", "CRITICAL", "WARNING"]),
            "critical_count": sum(1 for log in parsed_logs if log["level"] == "CRITICAL"),
            "error_count": sum(1 for log in parsed_logs if log["level"] == "ERROR"),
            "warning_count": sum(1 for log in parsed_logs if log["level"] == "WARNING"),
            "by_category": Counter(log["error_category"] for log in parsed_logs if log["level"] in ["ERROR", "CRITICAL"]),
            "by_operation": defaultdict(list),
            "error_rate": 0.0,
            "total_logs": len(parsed_logs)
        }
        
        for log in parsed_logs:
            if log["level"] in ["ERROR", "CRITICAL"]:
                stats["by_operation"][log["operation_name"]].append(log)
        
        stats["error_rate"] = stats["total_errors"] / len(parsed_logs) if parsed_logs else 0.0
        stats["by_category"] = dict(stats["by_category"])
        
        return stats
    
    def _detect_log_spikes(
        self,
        error_stats: Dict,
        historical_baseline: Optional[Dict] = None
    ) -> List[LogAnomaly]:
        """Detect error spikes in logs"""
        anomalies = []
        current_errors = error_stats["total_errors"]
        
        if historical_baseline:
            baseline_errors = historical_baseline.get("average_errors", 0)
            if baseline_errors > 0 and current_errors > baseline_errors * self.spike_multiplier:
                increase_pct = ((current_errors - baseline_errors) / baseline_errors) * 100
                severity = "critical" if increase_pct > 300 else "high"
                
                anomaly = LogAnomaly(
                    timestamp=datetime.utcnow().isoformat(),
                    anomaly_type="error_spike",
                    error_category="system",
                    count=current_errors,
                    severity=severity,
                    confidence=min(increase_pct / 500, 1.0),
                    description=f"Error spike: {current_errors} errors ({increase_pct:.0f}% above baseline)",
                    patterns=[f"Errors increased by {increase_pct:.1f}% vs baseline"]
                )
                anomalies.append(anomaly)
        
        if current_errors > self.error_threshold * 2:
            severity = "critical" if current_errors > self.error_threshold * 5 else "high"
            anomaly = LogAnomaly(
                timestamp=datetime.utcnow().isoformat(),
                anomaly_type="error_spike",
                error_category="system",
                count=current_errors,
                severity=severity,
                confidence=min(current_errors / (self.error_threshold * 10), 1.0),
                description=f"High error volume: {current_errors} errors exceed threshold",
                patterns=[f"{current_errors} errors > {self.error_threshold} threshold"]
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_error_patterns(
        self,
        error_stats: Dict,
        parsed_logs: List[Dict]
    ) -> List[LogAnomaly]:
        """Detect repetitive error patterns"""
        anomalies = []
        
        # Find most common exceptions
        exception_counts = Counter(
            log["exception"][:50] for log in parsed_logs
            if log.get("exception") and log["level"] in ["ERROR", "CRITICAL"]
        )
        
        for exception, count in exception_counts.most_common(5):
            if count >= 3:
                anomaly = LogAnomaly(
                    timestamp=datetime.utcnow().isoformat(),
                    anomaly_type="error_pattern",
                    error_category="repetitive",
                    count=count,
                    severity="high" if count >= 10 else "medium",
                    confidence=min(count / 20, 1.0),
                    description=f"Repetitive error: {exception} ({count} times)",
                    patterns=[f"Same error occurred {count} times", exception]
                )
                anomalies.append(anomaly)
        
        # Find error category spikes
        for category, count in error_stats["by_category"].items():
            if count >= 5 and category != "unknown":
                anomaly = LogAnomaly(
                    timestamp=datetime.utcnow().isoformat(),
                    anomaly_type="error_pattern",
                    error_category=category,
                    count=count,
                    severity="high" if count >= 15 else "medium",
                    confidence=min(count / 30, 1.0),
                    description=f"{category.upper()} errors spiking: {count} occurrences",
                    patterns=[f"{category} errors: {count}"]
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_error_cascades(self, parsed_logs: List[Dict]) -> List[LogAnomaly]:
        """Detect cascading failures"""
        anomalies = []
        
        operation_errors = defaultdict(list)
        for log in parsed_logs:
            if log["level"] in ["ERROR", "CRITICAL"]:
                operation_errors[log["operation_name"]].append(log)
        
        for operation, errors in operation_errors.items():
            if len(errors) >= 3:
                timestamps = sorted([
                    datetime.fromisoformat(e["timestamp"]) for e in errors
                ])
                
                deltas = [
                    (timestamps[i] - timestamps[i-1]).total_seconds()
                    for i in range(1, len(timestamps))
                ]
                
                if deltas and all(d < 5 for d in deltas):
                    anomaly = LogAnomaly(
                        timestamp=datetime.utcnow().isoformat(),
                        anomaly_type="error_cascade",
                        error_category="cascade",
                        count=len(errors),
                        severity="critical",
                        confidence=0.9,
                        description=f"Cascading failures in {operation}: {len(errors)} sequential errors",
                        patterns=[f"{len(errors)} errors in {max(deltas):.1f}s"]
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_resource_issues(self, parsed_logs: List[Dict]) -> List[LogAnomaly]:
        """Detect resource exhaustion in logs"""
        anomalies = []
        
        resource_errors = [
            log for log in parsed_logs
            if any(kw in log["message"].lower() for kw in ["memory", "cpu", "connection", "pool"])
            and log["level"] in ["ERROR", "CRITICAL"]
        ]
        
        if len(resource_errors) >= 2:
            anomaly = LogAnomaly(
                timestamp=datetime.utcnow().isoformat(),
                anomaly_type="resource_exhaustion",
                error_category="resource",
                count=len(resource_errors),
                severity="critical",
                confidence=0.95,
                description=f"Resource exhaustion detected: {len(resource_errors)} incidents",
                patterns=list(set(log["message"][:40] for log in resource_errors))
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_service_failures(self, parsed_logs: List[Dict]) -> List[LogAnomaly]:
        """Detect third-party service failures"""
        anomalies = []
        
        service_errors = [
            log for log in parsed_logs
            if any(kw in log["message"].lower() for kw in ["api", "gateway", "timeout", "unavailable"])
            and log["level"] in ["ERROR", "CRITICAL"]
        ]
        
        if len(service_errors) >= 2:
            anomaly = LogAnomaly(
                timestamp=datetime.utcnow().isoformat(),
                anomaly_type="service_failure",
                error_category="third_party",
                count=len(service_errors),
                severity="high",
                confidence=0.85,
                description=f"Service failures detected: {len(service_errors)} incidents",
                patterns=list(set(log["message"][:40] for log in service_errors))
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_metric_anomalies(
        self,
        metrics: Dict[str, Dict],
        historical_baseline: Optional[Dict] = None
    ) -> List[MetricAnomaly]:
        """Detect anomalies in metrics"""
        anomalies = []
        
        for metric_name, metric_data in metrics.items():
            if not metric_data:
                continue
            
            try:
                current_value = metric_data.get("latest", 0)
                avg_value = metric_data.get("avg", 0)
                values = metric_data.get("data_points", [])
                
                # Check for spikes
                if avg_value > 0:
                    deviation_pct = ((current_value - avg_value) / avg_value) * 100
                    
                    if current_value > avg_value * self.metric_spike_threshold:
                        severity = "critical" if deviation_pct > 150 else "high"
                        
                        anomaly = MetricAnomaly(
                            timestamp=datetime.utcnow().isoformat(),
                            metric_name=metric_name,
                            anomaly_type="metric_spike",
                            current_value=current_value,
                            baseline_value=avg_value,
                            deviation_percent=deviation_pct,
                            severity=severity,
                            confidence=min(abs(deviation_pct) / 200, 1.0),
                            description=f"{metric_name} spike: {current_value:.2f} ({deviation_pct:.0f}% above avg)"
                        )
                        anomalies.append(anomaly)
                
                # Check for concerning trends
                if "trend" in metric_data:
                    trend = metric_data["trend"]
                    if trend == "increasing" and "failed" in metric_name.lower():
                        anomaly = MetricAnomaly(
                            timestamp=datetime.utcnow().isoformat(),
                            metric_name=metric_name,
                            anomaly_type="metric_trend",
                            current_value=current_value,
                            baseline_value=avg_value,
                            deviation_percent=((current_value - avg_value) / avg_value * 100) if avg_value > 0 else 0,
                            severity="high",
                            confidence=0.75,
                            description=f"{metric_name} showing increasing trend",
                            trend=trend
                        )
                        anomalies.append(anomaly)
            
            except Exception as e:
                logger.warning(f"Error detecting metric anomalies for {metric_name}: {e}")
                continue
        
        return anomalies
    
    def _analyze_trends(
        self,
        metrics: Dict[str, Dict],
        historical_baseline: Optional[Dict] = None
    ) -> List[MetricAnomaly]:
        """Analyze metric trends"""
        anomalies = []
        
        # Check for correlations between metrics
        metric_pairs = [
            ("request_failed", "request_duration"),
            ("exception_count", "request_failed"),
            ("cpu_usage", "process_memory"),
        ]
        
        for metric1, metric2 in metric_pairs:
            if metric1 in metrics and metric2 in metrics:
                m1_data = metrics[metric1].get("data_points", [])
                m2_data = metrics[metric2].get("data_points", [])
                
                if len(m1_data) > 2 and len(m2_data) > 2:
                    try:
                        correlation = self._calculate_correlation(m1_data, m2_data)
                        if abs(correlation) > self.correlation_threshold:
                            anomaly = MetricAnomaly(
                                timestamp=datetime.utcnow().isoformat(),
                                metric_name=f"{metric1}+{metric2}",
                                anomaly_type="correlation",
                                current_value=correlation,
                                baseline_value=0,
                                deviation_percent=0,
                                severity="medium",
                                confidence=abs(correlation),
                                description=f"Strong correlation between {metric1} and {metric2} (r={correlation:.2f})",
                                correlation_metrics=[metric1, metric2]
                            )
                            anomalies.append(anomaly)
                    except:
                        continue
        
        return anomalies
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        try:
            x_arr = np.array(x, dtype=float)
            y_arr = np.array(y, dtype=float)
            
            x_mean = np.mean(x_arr)
            y_mean = np.mean(y_arr)
            
            numerator = np.sum((x_arr - x_mean) * (y_arr - y_mean))
            denominator = np.sqrt(
                np.sum((x_arr - x_mean) ** 2) * np.sum((y_arr - y_mean) ** 2)
            )
            
            return numerator / denominator if denominator > 0 else 0.0
        except:
            return 0.0
    
    def _correlate_anomalies(
        self,
        log_anomalies: List[LogAnomaly],
        metric_anomalies: List[MetricAnomaly]
    ) -> List[Tuple[LogAnomaly, MetricAnomaly]]:
        """Find correlations between log and metric anomalies"""
        correlations = []
        
        # Map error categories to system components
        category_to_systems = {
            "database": ["database_calls", "database_duration"],
            "third_party": ["dependency_calls", "dependency_failed"],
            "resource_exhaustion": ["cpu_usage", "process_memory"],
            "server_error": ["request_failed", "request_duration"],
        }
        
        for log_anom in log_anomalies:
            systems = category_to_systems.get(log_anom.error_category, [])
            
            for metric_anom in metric_anomalies:
                # Check if metric is related to error category
                if any(sys in metric_anom.metric_name for sys in systems):
                    correlations.append((log_anom, metric_anom))
        
        return correlations
    
    def _calculate_unified_severity(
        self,
        log_anomalies: List[LogAnomaly],
        metric_anomalies: List[MetricAnomaly],
        correlations: List[Tuple]
    ) -> Tuple[str, float]:
        """Calculate unified severity across all anomalies"""
        if not log_anomalies and not metric_anomalies:
            return "low", 0.0
        
        severity_scores = {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1
        }
        
        # Get max severity from logs
        log_severity = max(
            [severity_scores.get(a.severity, 0) for a in log_anomalies],
            default=0
        )
        
        # Get max severity from metrics
        metric_severity = max(
            [severity_scores.get(a.severity, 0) for a in metric_anomalies],
            default=0
        )
        
        # Boost severity if log and metric anomalies correlate
        final_score = max(log_severity, metric_severity)
        if correlations and max(log_severity, metric_severity) > 0:
            final_score = min(final_score + 1, 4)  # Boost by one level if correlated
        
        # Map back to severity
        severity_map = {4: "critical", 3: "high", 2: "medium", 1: "low", 0: "low"}
        final_severity = severity_map[final_score]
        
        # Calculate confidence
        total_anomalies = len(log_anomalies) + len(metric_anomalies)
        avg_confidence = (
            (sum(a.confidence for a in log_anomalies) +
             sum(a.confidence for a in metric_anomalies)) / total_anomalies
            if total_anomalies > 0 else 0.0
        )
        
        # Boost confidence with correlations
        correlation_boost = min(len(correlations) * 0.1, 0.3)
        final_confidence = min(avg_confidence + correlation_boost, 1.0)
        
        return final_severity, final_confidence
    
    def _identify_affected_systems(
        self,
        log_anomalies: List[LogAnomaly],
        metric_anomalies: List[MetricAnomaly]
    ) -> List[str]:
        """Identify which systems are affected"""
        systems: Set[str] = set()
        
        # From logs
        for log_anom in log_anomalies:
            if log_anom.error_category == "database":
                systems.add("database")
            elif log_anom.error_category == "third_party":
                systems.add("external_services")
            elif log_anom.error_category == "resource_exhaustion":
                systems.add("compute_resources")
            elif log_anom.error_category == "server_error":
                systems.add("web_server")
        
        # From metrics
        for metric_anom in metric_anomalies:
            if "database" in metric_anom.metric_name:
                systems.add("database")
            elif "cpu" in metric_anom.metric_name or "memory" in metric_anom.metric_name:
                systems.add("compute_resources")
            elif "request" in metric_anom.metric_name:
                systems.add("web_server")
        
        return sorted(list(systems))
    
    def _generate_unified_description(
        self,
        log_anomalies: List[LogAnomaly],
        metric_anomalies: List[MetricAnomaly],
        correlations: List[Tuple]
    ) -> str:
        """Generate unified anomaly description"""
        parts = []
        
        if log_anomalies:
            parts.append(f"{len(log_anomalies)} log anomalies detected")
        
        if metric_anomalies:
            parts.append(f"{len(metric_anomalies)} metric anomalies detected")
        
        if correlations:
            parts.append(f"{len(correlations)} correlations found")
        
        return " | ".join(parts)
    
    def _calculate_impact_score(
        self,
        log_anomalies: List[LogAnomaly],
        metric_anomalies: List[MetricAnomaly],
        correlations: List[Tuple]
    ) -> float:
        """Calculate overall impact score (0-1)"""
        if not log_anomalies and not metric_anomalies:
            return 0.0
        
        severity_scores = {"critical": 1.0, "high": 0.75, "medium": 0.5, "low": 0.25}
        
        log_score = (
            sum(severity_scores.get(a.severity, 0.5) for a in log_anomalies) /
            len(log_anomalies)
            if log_anomalies else 0.0
        )
        
        metric_score = (
            sum(severity_scores.get(a.severity, 0.5) for a in metric_anomalies) /
            len(metric_anomalies)
            if metric_anomalies else 0.0
        )
        
        base_score = max(log_score, metric_score)
        
        # Boost with correlations
        correlation_boost = min(len(correlations) * 0.1, 0.2)
        
        return min(base_score + correlation_boost, 1.0)
    
    def _estimate_early_warning_time(
        self,
        log_anomalies: List[LogAnomaly],
        metric_anomalies: List[MetricAnomaly]
    ) -> int:
        """Estimate how many minutes early this detects vs metrics alone"""
        # Logs typically detected 5-10 minutes before metric spikes
        has_log_anomaly = len(log_anomalies) > 0
        has_metric_anomaly = len(metric_anomalies) > 0
        
        if has_log_anomaly and not has_metric_anomaly:
            return 10  # Logs detected, metrics not yet spiked
        elif has_log_anomaly and has_metric_anomaly:
            return 5   # Both detected, but logs typically first
        else:
            return 0   # Metrics only
    
    def _generate_recommendations(
        self,
        log_anomalies: List[LogAnomaly],
        metric_anomalies: List[MetricAnomaly],
        affected_systems: List[str]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # From database anomalies
        if any("database" in sys for sys in affected_systems):
            recommendations.append("Check database connection pool status")
            recommendations.append("Verify database query performance")
        
        # From resource anomalies
        if any("compute" in sys for sys in affected_systems):
            recommendations.append("Consider scaling up compute resources")
            recommendations.append("Review memory leak patterns")
        
        # From external service anomalies
        if any("external" in sys for sys in affected_systems):
            recommendations.append("Check external API health")
            recommendations.append("Review timeout configurations")
        
        # From error spikes
        error_spike_logs = [
            a for a in log_anomalies
            if a.anomaly_type == "error_spike"
        ]
        if error_spike_logs:
            recommendations.append("Investigate recent deployment changes")
            recommendations.append("Review application error logs for patterns")
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _generate_prevention_strategies(
        self,
        log_anomalies: List[LogAnomaly],
        metric_anomalies: List[MetricAnomaly]
    ) -> List[str]:
        """Generate prevention strategies"""
        strategies = []
        
        # Monitoring
        strategies.append("Implement proactive error rate monitoring")
        
        # Alerting
        strategies.append("Set up alerts for error spike patterns")
        
        # Health checks
        strategies.append("Add application health check endpoints")
        
        # Load testing
        strategies.append("Perform load testing to identify capacity limits")
        
        # Circuit breakers
        if any("third_party" in a.error_category for a in log_anomalies):
            strategies.append("Implement circuit breaker for external dependencies")
        
        return strategies[:4]
    
    def _create_error_anomaly(self, timestamp: str, error: str) -> UnifiedAnomaly:
        """Create error anomaly when detection fails"""
        return UnifiedAnomaly(
            timestamp=timestamp,
            severity="low",
            confidence=0.0,
            description=f"Detection error: {error}",
            anomaly_count=0,
            recommendations=["Check system logs for detection errors"]
        )


def create_unified_detector(
    error_threshold: int = 5,
    spike_multiplier: float = 2.5,
    lookback_minutes: int = 60
) -> UnifiedAnomalyDetector:
    """
    Factory function to create unified detector
    
    Returns:
        UnifiedAnomalyDetector instance
    """
    logger.info("Creating unified anomaly detector")
    return UnifiedAnomalyDetector(
        error_threshold=error_threshold,
        spike_multiplier=spike_multiplier,
        lookback_minutes=lookback_minutes
    )

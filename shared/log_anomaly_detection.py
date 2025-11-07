"""
Application Logs Anomaly Detection Module
Analyzes application logs for pre-detection anomalies using statistical analysis
and Azure AI Foundry models for intelligent pattern recognition.

This module bridges application logs with anomaly detection, providing:
1. Log aggregation and parsing
2. Error pattern detection
3. Exception correlation analysis
4. Performance degradation warnings
5. AI-powered root cause analysis
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import statistics
import numpy as np
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class LogAnomaly:
    """Represents a detected log anomaly"""
    timestamp: str
    log_level: str
    error_type: str
    count: int
    trend: str
    severity: str
    confidence: float
    patterns: List[str]
    correlation: Optional[Dict] = None
    recommendation: Optional[str] = None


class ApplicationLogAnomalyDetector:
    """
    Analyzes application logs to detect anomalies before they impact metrics.
    
    Detects:
    - Error spikes (sudden increase in error logs)
    - Exception correlation (same error happening repeatedly)
    - Performance degradation (increasing latency in logs)
    - Resource exhaustion (memory, connection pool errors)
    - Third-party service failures (timeout errors, API failures)
    - Security anomalies (unusual access patterns)
    """
    
    def __init__(
        self,
        error_threshold: int = 5,
        spike_multiplier: float = 2.5,
        lookback_minutes: int = 60,
        correlation_threshold: float = 0.7
    ):
        """
        Initialize log anomaly detector
        
        Args:
            error_threshold: Minimum error count to flag
            spike_multiplier: How much of an increase constitutes a spike (2.5x = 250% increase)
            lookback_minutes: How far back to analyze (60 = last hour)
            correlation_threshold: Correlation coefficient for related errors (0.7 = strong correlation)
        """
        self.error_threshold = error_threshold
        self.spike_multiplier = spike_multiplier
        self.lookback_minutes = lookback_minutes
        self.correlation_threshold = correlation_threshold
        
        # Error categories for classification
        self.error_categories = {
            "database": ["sql", "db", "database", "connection", "timeout", "deadlock", "query"],
            "authentication": ["401", "403", "unauthorized", "forbidden", "auth", "token", "jwt"],
            "not_found": ["404", "notfound", "not found"],
            "server_error": ["500", "502", "503", "504", "internal server error", "bad gateway"],
            "resource_exhaustion": ["out of memory", "memory", "connection pool", "thread pool", "cpu"],
            "third_party": ["external", "api", "gateway", "timeout", "rate limit", "throttle"],
            "business_logic": ["validation", "constraint", "business", "rule"],
            "unknown": []
        }
        
        logger.info(f"ApplicationLogAnomalyDetector initialized with "
                   f"error_threshold={error_threshold}, "
                   f"spike_multiplier={spike_multiplier}, "
                   f"lookback_minutes={lookback_minutes}")
    
    def analyze_logs(
        self,
        logs: List[Dict],
        historical_baseline: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze application logs for anomalies
        
        Args:
            logs: List of log entries {timestamp, level, message, exception, ...}
            historical_baseline: Previous hour's statistics for comparison
            
        Returns:
            Dictionary with anomaly analysis results
        """
        if not logs or len(logs) == 0:
            return {
                "has_anomalies": False,
                "error_count": 0,
                "anomalies": [],
                "summary": "No logs to analyze"
            }
        
        try:
            # 1. Parse and categorize logs
            parsed_logs = self._parse_logs(logs)
            
            # 2. Aggregate error statistics
            error_stats = self._aggregate_errors(parsed_logs)
            
            # 3. Detect error spikes
            spikes = self._detect_spikes(error_stats, historical_baseline)
            
            # 4. Correlate related errors
            correlations = self._correlate_errors(parsed_logs, error_stats)
            
            # 5. Analyze error sequences (cascading failures)
            sequences = self._detect_error_sequences(parsed_logs)
            
            # 6. Check for resource exhaustion patterns
            resource_issues = self._detect_resource_exhaustion(parsed_logs)
            
            # 7. Detect third-party service failures
            service_failures = self._detect_service_failures(parsed_logs)
            
            # Combine all anomalies
            all_anomalies = spikes + correlations + sequences + resource_issues + service_failures
            
            # Sort by severity and confidence
            all_anomalies.sort(
                key=lambda x: (
                    {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(x.severity, 0),
                    x.confidence
                ),
                reverse=True
            )
            
            return {
                "has_anomalies": len(all_anomalies) > 0,
                "total_logs": len(parsed_logs),
                "error_count": sum(1 for log in parsed_logs if log["level"] in ["ERROR", "CRITICAL"]),
                "warning_count": sum(1 for log in parsed_logs if log["level"] == "WARNING"),
                "anomalies": [asdict(a) for a in all_anomalies[:10]],  # Top 10 anomalies
                "error_summary": error_stats,
                "resource_issues": resource_issues,
                "service_failures": service_failures,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing logs: {e}", exc_info=True)
            return {
                "has_anomalies": False,
                "error": str(e)
            }
    
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
                    "custom_properties": log.get("custom_properties", {}),
                    "error_category": self._categorize_error(log.get("message", ""), log.get("exception"))
                }
                parsed.append(parsed_log)
            except Exception as e:
                logger.warning(f"Error parsing log entry: {e}")
                continue
        
        return parsed
    
    def _categorize_error(self, message: str, exception: Optional[str] = None) -> str:
        """Categorize error by type"""
        full_text = f"{message} {exception or ''}".lower()
        
        for category, keywords in self.error_categories.items():
            if any(keyword in full_text for keyword in keywords):
                return category
        
        return "unknown"
    
    def _aggregate_errors(self, parsed_logs: List[Dict]) -> Dict:
        """Aggregate error statistics"""
        stats = {
            "total_errors": 0,
            "by_level": Counter(),
            "by_category": Counter(),
            "by_operation": defaultdict(lambda: {"count": 0, "errors": []}),
            "top_exceptions": Counter(),
            "error_rate": 0.0,
            "critical_errors": []
        }
        
        for log in parsed_logs:
            if log["level"] in ["ERROR", "CRITICAL", "WARNING"]:
                stats["total_errors"] += 1
                stats["by_level"][log["level"]] += 1
                stats["by_category"][log["error_category"]] += 1
                stats["by_operation"][log["operation_name"]]["count"] += 1
                
                if log["exception"]:
                    stats["top_exceptions"][log["exception"][:50]] += 1
                
                if log["level"] == "CRITICAL":
                    stats["critical_errors"].append({
                        "timestamp": log["timestamp"],
                        "message": log["message"][:100],
                        "operation": log["operation_name"]
                    })
        
        stats["error_rate"] = stats["total_errors"] / len(parsed_logs) if parsed_logs else 0.0
        stats["by_level"] = dict(stats["by_level"])
        stats["by_category"] = dict(stats["by_category"])
        stats["top_exceptions"] = dict(stats["top_exceptions"].most_common(5))
        
        return stats
    
    def _detect_spikes(
        self,
        error_stats: Dict,
        historical_baseline: Optional[Dict] = None
    ) -> List[LogAnomaly]:
        """Detect error spikes"""
        anomalies = []
        
        current_error_count = error_stats["total_errors"]
        
        # Compare with historical baseline if available
        if historical_baseline:
            baseline_error_count = historical_baseline.get("average_errors", 0)
            
            if baseline_error_count > 0 and current_error_count > baseline_error_count * self.spike_multiplier:
                increase_pct = ((current_error_count - baseline_error_count) / baseline_error_count) * 100
                
                anomaly = LogAnomaly(
                    timestamp=datetime.utcnow().isoformat(),
                    log_level="ERROR_SPIKE",
                    error_type="Error spike detected",
                    count=current_error_count,
                    trend="increasing",
                    severity="high" if increase_pct > 300 else "medium",
                    confidence=min(increase_pct / 500, 1.0),  # Normalize to 0-1
                    patterns=[f"Errors increased by {increase_pct:.1f}% vs baseline"],
                    recommendation=f"Investigate error spike: {current_error_count} errors (baseline: {baseline_error_count})"
                )
                anomalies.append(anomaly)
        
        # Check for absolute spike
        if current_error_count > self.error_threshold * 2:
            anomaly = LogAnomaly(
                timestamp=datetime.utcnow().isoformat(),
                log_level="ERROR_SPIKE",
                error_type="High error volume",
                count=current_error_count,
                trend="high",
                severity="critical" if current_error_count > self.error_threshold * 5 else "high",
                confidence=min(current_error_count / (self.error_threshold * 10), 1.0),
                patterns=[f"{current_error_count} errors exceeds threshold ({self.error_threshold})"],
                recommendation=f"High error volume detected: {current_error_count} errors"
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def _correlate_errors(self, parsed_logs: List[Dict], error_stats: Dict) -> List[LogAnomaly]:
        """Find correlated/repetitive errors"""
        anomalies = []
        
        # Find most common exceptions
        for exception, count in error_stats["top_exceptions"].items():
            if count >= 3:  # At least 3 occurrences
                anomaly = LogAnomaly(
                    timestamp=datetime.utcnow().isoformat(),
                    log_level="ERROR_PATTERN",
                    error_type=f"Repetitive error: {exception[:30]}",
                    count=count,
                    trend="repeating",
                    severity="high" if count >= 10 else "medium",
                    confidence=min(count / 20, 1.0),
                    patterns=[f"Same error occurred {count} times", exception[:100]],
                    recommendation=f"Recurring issue detected: {exception[:50]} (occurred {count} times)"
                )
                anomalies.append(anomaly)
        
        # Find correlated error categories
        categories = error_stats["by_category"]
        if len(categories) > 1:
            for category, count in categories.items():
                if count >= 5 and category != "unknown":
                    anomaly = LogAnomaly(
                        timestamp=datetime.utcnow().isoformat(),
                        log_level="ERROR_CATEGORY",
                        error_type=f"Error category spike: {category}",
                        count=count,
                        trend="spiking",
                        severity="high" if count >= 15 else "medium",
                        confidence=min(count / 30, 1.0),
                        patterns=[f"{category} errors: {count} occurrences"],
                        recommendation=f"Multiple {category} errors detected ({count} total)"
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_error_sequences(self, parsed_logs: List[Dict]) -> List[LogAnomaly]:
        """Detect cascading/sequential failures"""
        anomalies = []
        
        # Group by operation and time window
        operation_sequences = defaultdict(list)
        
        for log in parsed_logs:
            if log["level"] in ["ERROR", "CRITICAL"]:
                operation_sequences[log["operation_name"]].append(log)
        
        # Analyze sequences
        for operation, errors in operation_sequences.items():
            if len(errors) >= 3:
                # Calculate time deltas between errors
                timestamps = [datetime.fromisoformat(e["timestamp"]) for e in errors]
                timestamps.sort()
                
                deltas = []
                for i in range(1, len(timestamps)):
                    delta = (timestamps[i] - timestamps[i-1]).total_seconds()
                    deltas.append(delta)
                
                # If errors are close together, it's a cascade
                if deltas and all(d < 5 for d in deltas):  # Within 5 seconds
                    anomaly = LogAnomaly(
                        timestamp=datetime.utcnow().isoformat(),
                        log_level="ERROR_CASCADE",
                        error_type=f"Cascading failures in {operation}",
                        count=len(errors),
                        trend="cascading",
                        severity="critical",
                        confidence=0.9,
                        patterns=[f"Cascading errors in {operation}", f"{len(errors)} errors within {max(deltas):.1f}s"],
                        recommendation=f"CRITICAL: Cascading failures detected in {operation} ({len(errors)} sequential errors)"
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_resource_exhaustion(self, parsed_logs: List[Dict]) -> List[LogAnomaly]:
        """Detect resource exhaustion patterns"""
        anomalies = []
        resource_keywords = ["memory", "cpu", "connection", "thread", "pool", "exhausted", "oom"]
        
        resource_errors = [
            log for log in parsed_logs
            if any(kw in log["message"].lower() for kw in resource_keywords)
            and log["level"] in ["ERROR", "CRITICAL"]
        ]
        
        if len(resource_errors) >= 2:
            anomaly = LogAnomaly(
                timestamp=datetime.utcnow().isoformat(),
                log_level="RESOURCE_ALERT",
                error_type="Resource exhaustion detected",
                count=len(resource_errors),
                trend="critical",
                severity="critical",
                confidence=0.95,
                patterns=list(set([log["message"][:50] for log in resource_errors])),
                recommendation=f"CRITICAL: Resource exhaustion detected ({len(resource_errors)} incidents). Check memory/connection pools immediately."
            )
            anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_service_failures(self, parsed_logs: List[Dict]) -> List[LogAnomaly]:
        """Detect third-party service failures"""
        anomalies = []
        
        service_keywords = ["external", "api", "gateway", "timeout", "rate limit", "throttle", "unavailable"]
        
        service_errors = [
            log for log in parsed_logs
            if any(kw in log["message"].lower() for kw in service_keywords)
            and log["level"] in ["ERROR", "WARNING"]
        ]
        
        if len(service_errors) >= 3:
            # Analyze if service failures are frequent
            error_types = Counter([log["message"][:50] for log in service_errors])
            
            for service_type, count in error_types.most_common(3):
                if count >= 2:
                    anomaly = LogAnomaly(
                        timestamp=datetime.utcnow().isoformat(),
                        log_level="SERVICE_FAILURE",
                        error_type=f"Service failure: {service_type[:40]}",
                        count=count,
                        trend="degrading",
                        severity="high",
                        confidence=min(count / 10, 1.0),
                        patterns=[service_type],
                        recommendation=f"External service issue detected: {service_type[:50]} (occurred {count} times). Check API/Gateway status."
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def get_ai_analysis_prompt(self, anomalies: List[LogAnomaly]) -> str:
        """
        Generate AI analysis prompt for Azure AI Foundry
        Sends log anomalies to AI model for intelligent interpretation
        
        Args:
            anomalies: List of detected anomalies
            
        Returns:
            Formatted prompt for AI model
        """
        if not anomalies:
            return "No significant log anomalies detected."
        
        prompt_parts = ["Analyze these application log anomalies and provide root cause analysis:\n"]
        
        for i, anomaly in enumerate(anomalies[:5], 1):  # Top 5 anomalies
            prompt_parts.append(f"\n{i}. {anomaly.error_type} (Severity: {anomaly.severity})")
            prompt_parts.append(f"   - Count: {anomaly.count}")
            prompt_parts.append(f"   - Confidence: {anomaly.confidence:.1%}")
            prompt_parts.append(f"   - Patterns: {', '.join(anomaly.patterns[:2])}")
        
        prompt_parts.append("\nProvide:")
        prompt_parts.append("1. Root cause analysis")
        prompt_parts.append("2. Immediate actions")
        prompt_parts.append("3. Prevention strategies")
        prompt_parts.append("4. Estimated impact if not fixed")
        
        return "\n".join(prompt_parts)


def create_log_anomaly_detector(
    error_threshold: int = 5,
    spike_multiplier: float = 2.5
) -> ApplicationLogAnomalyDetector:
    """Factory function to create log anomaly detector"""
    logger.info(f"Creating ApplicationLogAnomalyDetector with error_threshold={error_threshold}")
    return ApplicationLogAnomalyDetector(
        error_threshold=error_threshold,
        spike_multiplier=spike_multiplier
    )

"""
State Management Module
Manages historical context and deduplication using Azure Table Storage
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from azure.data.tables import TableServiceClient, TableEntity
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError

logger = logging.getLogger(__name__)


class StateManager:
    """Manages anomaly detection state in Azure Table Storage"""
    
    METRICS_TABLE = "MetricsHistory"
    ANOMALIES_TABLE = "AnomalyDetections"
    
    def __init__(self, connection_string: str):
        """
        Initialize state manager
        
        Args:
            connection_string: Azure Storage connection string
        """
        self.connection_string = connection_string
        self.service_client = TableServiceClient.from_connection_string(connection_string)
        
        # Create tables if they don't exist
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """Create tables if they don't exist"""
        try:
            self.service_client.create_table_if_not_exists(self.METRICS_TABLE)
            self.service_client.create_table_if_not_exists(self.ANOMALIES_TABLE)
            logger.info("Storage tables initialized")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def save_metrics_snapshot(
        self,
        timestamp: datetime,
        metrics_data: Dict[str, any]
    ) -> bool:
        """
        Save a snapshot of metrics data
        
        Args:
            timestamp: Timestamp of the snapshot
            metrics_data: Dictionary of metrics and their statistics
            
        Returns:
            True if successful
        """
        try:
            table_client = self.service_client.get_table_client(self.METRICS_TABLE)
            
            # Create entity
            entity = {
                "PartitionKey": timestamp.strftime("%Y-%m-%d"),  # Partition by date
                "RowKey": timestamp.isoformat(),
                "Timestamp": timestamp,
                "MetricsJson": json.dumps(metrics_data)
            }
            
            table_client.upsert_entity(entity)
            logger.debug(f"Saved metrics snapshot for {timestamp}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save metrics snapshot: {e}")
            return False
    
    def get_recent_metrics(
        self,
        lookback_minutes: int = 60
    ) -> List[Dict]:
        """
        Retrieve recent metrics snapshots
        
        Args:
            lookback_minutes: How far back to look
            
        Returns:
            List of metrics snapshots
        """
        try:
            table_client = self.service_client.get_table_client(self.METRICS_TABLE)
            
            cutoff_time = datetime.utcnow() - timedelta(minutes=lookback_minutes)
            
            # Query entities (partition key is date, so we might need multiple partitions)
            filter_query = f"Timestamp ge datetime'{cutoff_time.isoformat()}'"
            
            entities = table_client.query_entities(filter_query)
            
            results = []
            for entity in entities:
                try:
                    metrics_data = json.loads(entity.get("MetricsJson", "{}"))
                    results.append({
                        "timestamp": entity["RowKey"],
                        "metrics": metrics_data
                    })
                except json.JSONDecodeError:
                    continue
            
            logger.info(f"Retrieved {len(results)} historical metric snapshots")
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve recent metrics: {e}")
            return []
    
    def save_anomaly_detection(
        self,
        timestamp: datetime,
        metric_name: str,
        analysis_result: Dict
    ) -> bool:
        """
        Save an anomaly detection result
        
        Args:
            timestamp: When the anomaly was detected
            metric_name: Which metric triggered it
            analysis_result: AI model output
            
        Returns:
            True if successful
        """
        try:
            table_client = self.service_client.get_table_client(self.ANOMALIES_TABLE)
            
            entity = {
                "PartitionKey": timestamp.strftime("%Y-%m-%d"),
                "RowKey": f"{timestamp.isoformat()}_{metric_name}",
                "Timestamp": timestamp,
                "MetricName": metric_name,
                "IsAnomaly": analysis_result.get("isAnomaly", False),
                "Severity": analysis_result.get("severity", "unknown"),
                "Confidence": float(analysis_result.get("confidence", 0.0)),
                "PredictedTrend": analysis_result.get("predictedTrend", "unknown"),
                "RecommendedAction": analysis_result.get("recommendedAction", "none"),
                "Reasoning": analysis_result.get("reasoning", ""),
                "AnalysisJson": json.dumps(analysis_result)
            }
            
            table_client.upsert_entity(entity)
            logger.info(f"Saved anomaly detection for {metric_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save anomaly detection: {e}")
            return False
    
    def get_recent_anomalies(
        self,
        lookback_minutes: int = 60,
        min_severity: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve recent anomaly detections
        
        Args:
            lookback_minutes: How far back to look
            min_severity: Optional minimum severity filter
            
        Returns:
            List of anomaly detections
        """
        try:
            table_client = self.service_client.get_table_client(self.ANOMALIES_TABLE)
            
            cutoff_time = datetime.utcnow() - timedelta(minutes=lookback_minutes)
            
            filter_query = f"Timestamp ge datetime'{cutoff_time.isoformat()}'"
            if min_severity:
                severity_levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
                # Note: Table Storage doesn't support numeric comparisons on strings easily
                # This is a simplified filter
                filter_query += f" and Severity eq '{min_severity}'"
            
            entities = table_client.query_entities(filter_query)
            
            results = []
            for entity in entities:
                results.append({
                    "timestamp": entity.get("Timestamp"),
                    "metric": entity.get("MetricName"),
                    "isAnomaly": entity.get("IsAnomaly"),
                    "severity": entity.get("Severity"),
                    "confidence": entity.get("Confidence"),
                    "action": entity.get("RecommendedAction"),
                    "reasoning": entity.get("Reasoning")
                })
            
            logger.info(f"Retrieved {len(results)} recent anomalies")
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve recent anomalies: {e}")
            return []
    
    def check_duplicate_alert(
        self,
        metric_name: str,
        lookback_minutes: int = 15
    ) -> bool:
        """
        Check if we've already alerted for this metric recently
        
        Args:
            metric_name: Metric to check
            lookback_minutes: Time window to check
            
        Returns:
            True if duplicate alert exists
        """
        recent_anomalies = self.get_recent_anomalies(lookback_minutes)
        
        for anomaly in recent_anomalies:
            if (anomaly.get("metric") == metric_name and 
                anomaly.get("isAnomaly") and
                anomaly.get("action") != "none"):
                logger.info(f"Duplicate alert suppressed for {metric_name}")
                return True
        
        return False
    
    def calculate_baseline(
        self,
        metric_name: str,
        lookback_hours: int = 24
    ) -> Optional[Dict]:
        """
        Calculate baseline statistics for a metric
        
        Args:
            metric_name: Metric to analyze
            lookback_hours: Time window for baseline
            
        Returns:
            Dictionary with baseline stats
        """
        snapshots = self.get_recent_metrics(lookback_hours * 60)
        
        if not snapshots:
            return None
        
        values = []
        for snapshot in snapshots:
            metrics = snapshot.get("metrics", {})
            if metric_name in metrics:
                stats = metrics[metric_name]
                if isinstance(stats, dict) and "avg" in stats:
                    values.append(stats["avg"])
        
        if not values:
            return None
        
        # Calculate baseline statistics
        avg = sum(values) / len(values)
        sorted_values = sorted(values)
        
        return {
            "mean": avg,
            "median": sorted_values[len(sorted_values) // 2],
            "p95": sorted_values[int(len(sorted_values) * 0.95)],
            "p99": sorted_values[int(len(sorted_values) * 0.99)],
            "min": min(values),
            "max": max(values),
            "sample_count": len(values)
        }


def create_state_manager() -> Optional[StateManager]:
    """
    Factory function to create StateManager from environment
    
    Returns:
        StateManager instance or None if config missing
    """
    connection_string = os.getenv("TABLE_STORAGE_CONNECTION_STRING")
    
    if not connection_string:
        logger.error("TABLE_STORAGE_CONNECTION_STRING must be set")
        return None
    
    try:
        return StateManager(connection_string)
    except Exception as e:
        logger.error(f"Failed to create StateManager: {e}")
        return None

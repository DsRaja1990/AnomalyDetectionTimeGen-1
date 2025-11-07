"""
Logic App Integration
Sends alerts and remediation requests to Azure Logic App
"""
import os
import logging
from typing import Dict, Optional
from datetime import datetime
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class LogicAppClient:
    """Client for sending alerts to Azure Logic App"""
    
    def __init__(self, webhook_url: str, timeout: int = 30):
        """
        Initialize Logic App client
        
        Args:
            webhook_url: Logic App HTTP trigger URL
            timeout: Request timeout in seconds
        """
        self.webhook_url = webhook_url
        self.timeout = timeout
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def send_alert(
        self,
        metric_name: str,
        current_value: float,
        analysis: Dict,
        historical_context: Optional[Dict] = None
    ) -> bool:
        """
        Send alert to Logic App
        
        Args:
            metric_name: Name of the metric
            current_value: Current metric value
            analysis: AI analysis result
            historical_context: Optional historical stats
            
        Returns:
            True if successful
        """
        # Build enhanced payload
        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metric": metric_name,
            "currentValue": current_value,
            "expectedValue": analysis.get("expectedNextValue", 0),
            "threshold": self._get_threshold_for_metric(metric_name),
            "predictedTrend": analysis.get("predictedTrend", "unknown"),
            "confidence": analysis.get("confidence", 0.0),
            "severity": analysis.get("severity", "unknown"),
            "isAnomaly": analysis.get("isAnomaly", False),
            "reasoning": analysis.get("reasoning", ""),
            "recommendedAction": analysis.get("recommendedAction", "none")
        }
        
        # Add historical context if available
        if historical_context:
            payload["historicalContext"] = historical_context
        
        try:
            logger.info(f"Sending alert to Logic App for {metric_name}")
            logger.debug(f"Payload: {payload}")
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            
            logger.info(f"Alert sent successfully. Status: {response.status_code}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send alert to Logic App: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending alert: {e}")
            return False
    
    def _get_threshold_for_metric(self, metric_name: str) -> float:
        """Get threshold value for metric (should match prefilter)"""
        thresholds = {
            "performance_counters_processor_time": 80.0,
            "performance_counters_memory": 104857600.0,  # 100MB
            "requests_duration": 1000.0,
            "requests_failed": 0.0
        }
        return thresholds.get(metric_name, 0.0)


def create_logic_app_client() -> Optional[LogicAppClient]:
    """
    Factory function to create LogicAppClient from environment
    
    Returns:
        LogicAppClient instance or None if config missing
    """
    webhook_url = os.getenv("LOGIC_APP_URL")
    
    if not webhook_url:
        logger.error("LOGIC_APP_URL must be set")
        return None
    
    return LogicAppClient(webhook_url)

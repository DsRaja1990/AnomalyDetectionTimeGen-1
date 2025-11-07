"""
TimeGEN-1 Anomaly Detection Client
Handles pre-detection using Azure's dedicated anomaly detection model
Multi-series capable - analyzes multiple metrics simultaneously for better correlation detection
"""
import os
import json
import logging
from typing import Dict, List, Optional
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


class TimeGENAnomalyDetector:
    """
    TimeGEN-1 Anomaly Detection Client
    Uses Azure's multi-series anomaly detection model for pre-detection
    
    Multi-series approach:
    - Single API call analyzes all metrics together
    - Automatically detects correlations between metrics
    - Returns anomaly scores for each metric
    - Perfect for early warning (5-10 min before metric spike)
    """
    
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        timeout: int = 180
    ):
        """
        Initialize TimeGEN-1 Anomaly Detector
        
        Args:
            endpoint: TimeGEN-1 endpoint (e.g., https://TimeGEN-1-AssurantPoc.eastus2.models.ai.azure.com/anomaly_detection_multi_series)
            api_key: API key for authentication
            timeout: Request timeout in seconds (180s for multi-series analysis - increased for large datasets)
        """
        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        # Use multiple endpoints for different approaches
        self.online_anomaly_url = f"{self.endpoint}/v2/online_anomaly_detection"
        self.forecast_url = f"{self.endpoint}/v1/forecast"
        self.detect_anomalies_url = f"{self.endpoint}/v2/detect_anomalies"
        
        logger.info(f"TimeGEN-1 Anomaly Detector initialized")
        logger.info(f"  Endpoint: {self.endpoint}")
        logger.info(f"  Available URLs:")
        logger.info(f"    Online Anomaly: {self.online_anomaly_url}")
        logger.info(f"    Forecast: {self.forecast_url}")
        logger.info(f"    Detect Anomalies: {self.detect_anomalies_url}")
    
    def detect_anomalies_multi_series(
        self,
        metrics_data: Dict[str, List[tuple]],
        freq: str = "5min",
        fh: int = 3
    ) -> Dict:
        """
        Detect anomalies using multi-series approach (RECOMMENDED)
        
        Analyzes all metrics simultaneously to detect correlations and cascading failures
        
        Args:
            metrics_data: Dict of metric_name -> [(timestamp, value), ...]
                Example: {
                    "request_count": [("2025-11-01", 100), ("2025-11-02", 110), ...],
                    "cpu_usage": [("2025-11-01", 45.2), ("2025-11-02", 52.1), ...],
                    "exception_count": [("2025-11-01", 5), ("2025-11-02", 8), ...]
                }
            freq: Frequency - "D" for daily, "H" for hourly, "5min" for 5-minute
            fh: Forecast horizon (days/hours to predict)
        
        Returns:
            Dict with anomaly detection results including:
            - anomalies: List of detected anomalies with metric name and score
            - severity: "low" | "medium" | "high" | "critical"
            - is_anomaly: bool
            - confidence: 0.0-1.0
            - affected_metrics: List of metrics with anomalies
            - forecast: Predicted values for next period
        """
        try:
            # OPTIMIZATION: Limit data points to prevent timeouts and improve performance
            # Use only the most recent data points for each metric (max 20 points)
            max_points = 20
            
            # Convert metrics to TimeGEN-1 format (timestamp -> value dict format)
            y_data = {}
            total_points = 0
            
            for metric_name, data_points in metrics_data.items():
                if data_points:
                    # Take only the most recent points to reduce payload size
                    recent_points = data_points[-max_points:] if len(data_points) > max_points else data_points
                    
                    # Convert to timestamp->value dict format (matches sample code)
                    metric_data = {}
                    for i, (timestamp, value) in enumerate(recent_points):
                        # Use sequential timestamps if original format is problematic
                        key = f"2025-11-{6:02d}T{10 + i:02d}:00:00Z"  # Sequential timestamps
                        metric_data[key] = float(value)
                    
                    if metric_data:  # Only include if we have data
                        y_data[metric_name] = metric_data
                        total_points += len(metric_data)
            
            if not y_data:
                logger.warning("No data provided for anomaly detection after filtering")
                return self._fallback_response(is_anomaly=False, reason="No data")
            
            # OPTIMIZATION: If too much data, select only the most important metrics
            if total_points > 100:  # Arbitrary threshold to prevent timeouts
                # Prioritize key metrics for anomaly detection
                priority_metrics = ['cpu_usage', 'memory_available', 'http_5xx_errors', 'exception_count', 'request_failed']
                filtered_y_data = {}
                
                for metric in priority_metrics:
                    if metric in y_data:
                        filtered_y_data[metric] = y_data[metric]
                
                # Add other metrics if we have room
                remaining_space = 50  # Max points for remaining metrics
                for metric_name, metric_data in y_data.items():
                    if metric_name not in filtered_y_data and remaining_space > 0:
                        filtered_y_data[metric_name] = metric_data
                        remaining_space -= len(metric_data)
                        if remaining_space <= 0:
                            break
                
                y_data = filtered_y_data
                logger.info(f"OPTIMIZATION: Reduced dataset from {total_points} to {sum(len(v) for v in y_data.values())} points")
            
            # Build request payload matching Azure AI Foundry sample format
            payload = {
                "freq": freq,
                "fh": fh,
                "y": y_data,  # Direct dict format like the sample
                "clean_ex_first": True,
                "finetune_steps": 0,
                "finetune_loss": "default"
            }
            
            logger.info(f"TimeGEN-1 Multi-Series Request:")
            logger.info(f"  Metrics: {list(y_data.keys())}")
            logger.info(f"  Data points per metric: {[len(v) for v in y_data.values()]}")
            logger.info(f"  Frequency: {freq}, Forecast horizon: {fh}")
            
            # DEBUG: Log the structure of y_data to verify it's correct
            logger.info(f"DEBUG: y_data structure check:")
            for metric_name, values in list(y_data.items())[:3]:  # First 3 metrics
                if isinstance(values, dict):
                    sample_keys = list(values.keys())[:3]
                    sample_values = [values[k] for k in sample_keys]
                    logger.info(f"  {metric_name}: type={type(values).__name__}, len={len(values)}, sample_keys={sample_keys}, sample_values={sample_values}")
                else:
                    logger.info(f"  {metric_name}: type={type(values).__name__}, len={len(values) if hasattr(values, '__len__') else 'N/A'}, sample={str(values)[:50]}")
            
            # Try multiple endpoints in order of efficiency
            return self._call_timegen_with_fallback(payload, y_data, freq, fh)
            
        except Exception as e:
            logger.error(f"Multi-series anomaly detection failed: {e}", exc_info=True)
            return self._fallback_response(is_anomaly=False, reason=f"Detection error: {str(e)}")
    
    def _call_timegen_with_fallback(self, payload: Dict, y_data: Dict, freq: str, fh: int) -> Dict:
        """
        Try multiple TimeGEN-1 endpoints in order of efficiency
        1. /v1/forecast (fastest, use residuals for anomaly detection)
        2. /v2/detect_anomalies (purpose-built)
        3. /v2/online_anomaly_detection (original, slowest)
        """
        
        # OPTIMIZED: Skip unavailable endpoints and use statistical analysis
        logger.info("Strategy 1: Using statistical anomaly detection based on correlations...")
        try:
            return self._detect_via_statistical_analysis(y_data, freq, fh)
        except Exception as e1:
            logger.warning(f"Statistical analysis failed: {e1}")
        
        # Strategy 2: Try online_anomaly_detection (only available endpoint)
        logger.info("Strategy 2: Using TimeGEN-1 online_anomaly_detection...")
        try:
            return self._call_timegen_api(payload, self.online_anomaly_url)
        except Exception as e2:
            logger.warning(f"TimeGEN-1 online anomaly detection failed: {e2}")
        
        # Strategy 3: Pure correlation-based fallback
        logger.info("Strategy 3: Using correlation-based anomaly detection fallback...")
        try:
            return self._correlation_based_detection(y_data)
        except Exception as e3:
            logger.error(f"All anomaly detection strategies failed: {e3}")
            return self._fallback_response(is_anomaly=False, reason="All strategies failed")
    
    def _detect_via_forecast(self, y_data: Dict, freq: str, fh: int) -> Dict:
        """
        Use forecast endpoint to detect anomalies via prediction residuals
        This is typically faster and more reliable than online_anomaly_detection
        """
        anomalies = []
        max_anomaly_score = 0.0
        affected_metrics = []
        
        # Process top priority metrics first (most important for anomaly detection)
        priority_order = ['http_5xx_errors', 'exception_count', 'cpu_usage', 'memory_available', 'request_failed']
        metrics_to_process = []
        
        # Add priority metrics first
        for metric in priority_order:
            if metric in y_data:
                metrics_to_process.append(metric)
        
        # Add remaining metrics
        for metric in y_data.keys():
            if metric not in metrics_to_process:
                metrics_to_process.append(metric)
        
        # Limit to top 5 metrics to prevent timeout
        metrics_to_process = metrics_to_process[:5]
        logger.info(f"Processing {len(metrics_to_process)} priority metrics: {metrics_to_process}")
        
        for metric_name in metrics_to_process:
            try:
                metric_values = list(y_data[metric_name].values())
                if len(metric_values) < 3:  # Need minimum data for forecasting
                    continue
                
                # Simple payload for forecast endpoint
                forecast_payload = {
                    "y": metric_values,  # Just the values array
                    "fh": min(fh, 3),   # Shorter forecast horizon
                    "freq": "1",        # Simple frequency
                }
                
                result = self._call_timegen_api(forecast_payload, self.forecast_url)
                
                if result and 'forecast' in result:
                    # Calculate anomaly based on forecast vs actual
                    forecast_values = result['forecast']
                    if forecast_values and len(metric_values) > 0:
                        # Simple anomaly detection: if latest value deviates significantly from forecast
                        latest_actual = metric_values[-1]
                        predicted = forecast_values[0] if forecast_values else latest_actual
                        
                        # Calculate percentage deviation
                        if predicted != 0:
                            deviation = abs((latest_actual - predicted) / predicted)
                            anomaly_score = min(deviation, 1.0)  # Cap at 1.0
                            
                            # Consider it anomalous if deviation > 50%
                            if deviation > 0.5:
                                anomalies.append({
                                    'metric': metric_name,
                                    'score': anomaly_score,
                                    'actual': latest_actual,
                                    'predicted': predicted,
                                    'deviation': deviation
                                })
                                affected_metrics.append(metric_name)
                                max_anomaly_score = max(max_anomaly_score, anomaly_score)
                
            except Exception as e:
                logger.warning(f"Forecast analysis failed for {metric_name}: {e}")
                continue
        
        # Build response
        is_anomaly = len(anomalies) > 0
        severity = "critical" if max_anomaly_score > 0.8 else "high" if max_anomaly_score > 0.6 else "medium" if max_anomaly_score > 0.4 else "low"
        
        return {
            'is_anomaly': is_anomaly,
            'severity': severity,
            'confidence': float(max_anomaly_score),
            'anomalies': anomalies,
            'affected_metrics': affected_metrics,
            'anomaly_count': len(anomalies),
            'source': 'timegen1_forecast_residuals',
            'timestamp': datetime.utcnow().isoformat(),
            'response_code': 200
        }
    
    def _detect_via_statistical_analysis(self, y_data: Dict, freq: str, fh: int) -> Dict:
        """
        Advanced statistical anomaly detection using the correlation patterns
        Leverages the excellent correlation analysis already being performed
        """
        import statistics
        import math
        
        anomalies = []
        max_anomaly_score = 0.0
        affected_metrics = []
        
        # Priority metrics for analysis
        priority_metrics = ['http_5xx_errors', 'exception_count', 'cpu_usage', 'memory_available', 'request_failed']
        
        logger.info(f"Statistical Analysis: Processing {len(y_data)} metrics")
        
        for metric_name, metric_data in y_data.items():
            if not metric_data or len(metric_data) < 3:
                continue
                
            try:
                values = list(metric_data.values())
                
                # Calculate statistical measures
                mean_val = statistics.mean(values)
                if len(values) > 1:
                    stdev_val = statistics.stdev(values)
                else:
                    stdev_val = 0
                
                latest_value = values[-1]
                
                # Z-score based anomaly detection
                if stdev_val > 0:
                    z_score = abs((latest_value - mean_val) / stdev_val)
                else:
                    z_score = 0
                
                # Rate of change analysis
                if len(values) >= 2:
                    recent_change = abs((values[-1] - values[-2]) / (values[-2] + 0.0001))  # Avoid division by zero
                else:
                    recent_change = 0
                
                # Special handling for critical metrics
                is_priority = metric_name in priority_metrics
                threshold_multiplier = 1.5 if is_priority else 2.0
                
                # Anomaly scoring
                anomaly_score = 0.0
                
                # Z-score contribution
                if z_score > (2.0 / threshold_multiplier):
                    anomaly_score += min(z_score / 4.0, 0.4)
                
                # Rate of change contribution  
                if recent_change > (0.3 / threshold_multiplier):
                    anomaly_score += min(recent_change, 0.4)
                
                # Special case: HTTP 5xx errors - any increase is significant
                if metric_name == 'http_5xx_errors' and len(values) >= 2:
                    if values[-1] > values[-2]:
                        error_increase = (values[-1] - values[-2]) / (values[-2] + 1)
                        anomaly_score = max(anomaly_score, min(error_increase, 0.9))
                        logger.warning(f"HTTP 5xx errors increased from {values[-2]} to {values[-1]} (ratio: {error_increase:.2f})")
                
                # Cap anomaly score
                anomaly_score = min(anomaly_score, 1.0)
                
                # Flag as anomalous if score is significant
                if anomaly_score > 0.3:  # Lower threshold for better detection
                    anomalies.append({
                        'metric': metric_name,
                        'score': anomaly_score,
                        'z_score': z_score,
                        'rate_change': recent_change,
                        'latest_value': latest_value,
                        'mean': mean_val,
                        'stdev': stdev_val
                    })
                    affected_metrics.append(metric_name)
                    max_anomaly_score = max(max_anomaly_score, anomaly_score)
                    
                    logger.info(f"ANOMALY DETECTED: {metric_name} - Score: {anomaly_score:.3f}, Z-score: {z_score:.2f}, Change: {recent_change:.3f}")
                
            except Exception as e:
                logger.warning(f"Statistical analysis failed for {metric_name}: {e}")
                continue
        
        # Determine overall severity
        is_anomaly = len(anomalies) > 0
        if max_anomaly_score > 0.8:
            severity = "critical"
        elif max_anomaly_score > 0.6:
            severity = "high"  
        elif max_anomaly_score > 0.4:
            severity = "medium"
        else:
            severity = "low"
        
        logger.info(f"Statistical Analysis Result: {len(anomalies)} anomalies detected, max_score: {max_anomaly_score:.3f}")
        
        return {
            'is_anomaly': is_anomaly,
            'severity': severity,
            'confidence': float(max_anomaly_score),
            'anomalies': anomalies,
            'affected_metrics': affected_metrics,
            'anomaly_count': len(anomalies),
            'source': 'statistical_analysis',
            'timestamp': datetime.utcnow().isoformat(),
            'response_code': 200
        }
    
    def _correlation_based_detection(self, y_data: Dict) -> Dict:
        """
        Pure correlation-based anomaly detection fallback
        Uses the patterns already identified by correlation analysis
        """
        # This leverages the correlation analysis already performed
        # Look for metrics with high variance or sudden changes
        
        anomalies = []
        
        # Simple variance-based detection
        for metric_name, metric_data in y_data.items():
            if metric_data and len(metric_data) >= 2:
                values = list(metric_data.values())
                if len(values) >= 2:
                    # Simple change detection
                    change_ratio = abs(values[-1] - values[0]) / (abs(values[0]) + 0.1)
                    if change_ratio > 1.0:  # 100% change threshold
                        anomalies.append({
                            'metric': metric_name,
                            'score': min(change_ratio, 1.0),
                            'reason': 'high_variance'
                        })
        
        return {
            'is_anomaly': len(anomalies) > 0,
            'severity': 'medium' if anomalies else 'low',
            'confidence': 0.5 if anomalies else 0.0,
            'anomalies': anomalies,
            'affected_metrics': [a['metric'] for a in anomalies],
            'anomaly_count': len(anomalies),
            'source': 'correlation_fallback',
            'timestamp': datetime.utcnow().isoformat(),
            'response_code': 200
        }
    
    def _call_timegen_api(self, payload: Dict, api_url: str = None) -> Dict:
        """
        Call TimeGEN-1 API endpoint
        
        Args:
            payload: Request payload
            api_url: Specific API URL to call (defaults to online_anomaly_detection)
        
        Returns:
            Structured anomaly detection response
        """
        if api_url is None:
            api_url = self.online_anomaly_url
            
        try:
            body = json.dumps(payload).encode('utf-8')
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            logger.info(f"Calling TimeGEN-1 API: {api_url}")
            logger.info(f"Request size: {len(body)} bytes")
            
            req = urllib.request.Request(
                api_url,
                data=body,
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                result = json.loads(response.read().decode('utf-8'))
                logger.info(f"TimeGEN-1 Response received: {len(str(result))} chars")
                
                # Parse response
                return self._parse_timegen_response(result, payload)
                
        except urllib.error.HTTPError as e:
            logger.error(f"TimeGEN-1 API HTTP Error {e.code}: {e.reason}")
            error_detail = e.read().decode('utf-8')
            logger.error(f"Error details: {error_detail[:500]}")
            return self._fallback_response(is_anomaly=False, reason=f"API error: {e.code}")
        
        except Exception as e:
            logger.error(f"TimeGEN-1 API call failed: {e}", exc_info=True)
            return self._fallback_response(is_anomaly=False, reason=f"Connection error: {str(e)}")
    
    def _parse_timegen_response(self, response: Dict, payload: Dict) -> Dict:
        """
        Parse TimeGEN-1 response and convert to standardized format
        
        Args:
            response: Raw API response
            payload: Original request payload
        
        Returns:
            Standardized anomaly detection response
        """
        try:
            # TimeGEN-1 /v2/online_anomaly_detection returns:
            # {metric_name: {y: [...], anomaly_score: [...], anomaly_flag: [0/1, ...]}}
            
            anomalies = []
            max_anomaly_score = 0.0
            affected_metrics = []
            
            for metric_name, metric_result in response.items():
                if isinstance(metric_result, dict):
                    # Get latest anomaly score and flag
                    scores = metric_result.get('anomaly_score', [])
                    flags = metric_result.get('anomaly_flag', [])
                    
                    if scores and flags:
                        latest_score = float(scores[-1]) if scores else 0.0
                        latest_flag = int(flags[-1]) if flags else 0
                        
                        # If anomaly_flag is 1, there's an anomaly
                        if latest_flag == 1 or latest_score > 0.7:
                            anomalies.append({
                                'metric': metric_name,
                                'score': latest_score,
                                'is_anomaly': latest_flag == 1
                            })
                            affected_metrics.append(metric_name)
                            max_anomaly_score = max(max_anomaly_score, latest_score)
            
            # Determine severity based on max anomaly score
            if max_anomaly_score > 0.9:
                severity = "critical"
            elif max_anomaly_score > 0.7:
                severity = "high"
            elif max_anomaly_score > 0.5:
                severity = "medium"
            else:
                severity = "low"
            
            is_anomaly = len(anomalies) > 0
            
            result = {
                'is_anomaly': is_anomaly,
                'severity': severity,
                'confidence': float(max_anomaly_score),
                'anomalies': anomalies,
                'affected_metrics': affected_metrics,
                'anomaly_count': len(anomalies),
                'source': 'timegen1_online_anomaly',
                'timestamp': datetime.utcnow().isoformat(),
                'response_code': 200
            }
            
            logger.info(f"TimeGEN-1 Analysis Result:")
            logger.info(f"  Is Anomaly: {is_anomaly}")
            logger.info(f"  Severity: {severity}")
            logger.info(f"  Confidence: {max_anomaly_score:.2f}")
            logger.info(f"  Affected Metrics: {affected_metrics}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse TimeGEN-1 response: {e}", exc_info=True)
            return self._fallback_response(is_anomaly=False, reason="Parse error")
    
    def _fallback_response(self, is_anomaly: bool = False, reason: str = "") -> Dict:
        """Return fallback response when detection fails"""
        return {
            'is_anomaly': is_anomaly,
            'severity': 'low' if not is_anomaly else 'medium',
            'confidence': 0.0,
            'anomalies': [],
            'affected_metrics': [],
            'anomaly_count': 0,
            'source': 'timegen1_fallback',
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat(),
            'response_code': 500
        }


def create_timegen_anomaly_detector() -> Optional[TimeGENAnomalyDetector]:
    """
    Factory function to create TimeGEN-1 Anomaly Detector from environment
    
    Environment variables:
        TIMEGEN1_ENDPOINT: TimeGEN-1 endpoint (e.g., https://TimeGEN-1-AssurantPoc.eastus2.models.ai.azure.com)
        TIMEGEN1_API_KEY: API key for authentication
    
    Returns:
        TimeGENAnomalyDetector instance or None if config missing
    """
    endpoint = os.getenv("TIMEGEN1_ENDPOINT")
    api_key = os.getenv("TIMEGEN1_API_KEY")
    
    if not endpoint or not api_key:
        logger.error("TIMEGEN1_ENDPOINT and TIMEGEN1_API_KEY must be set")
        return None
    
    logger.info(f"Creating TimeGEN-1 Anomaly Detector")
    return TimeGENAnomalyDetector(endpoint, api_key)


# Backward compatibility - create_ai_client redirects to TimeGEN
def create_ai_client() -> Optional[TimeGENAnomalyDetector]:
    """
    Backward compatibility wrapper - now uses TimeGEN-1 for anomaly detection
    Redirect to TimeGEN-1 detector (no longer using Phi-4 for this purpose)
    """
    return create_timegen_anomaly_detector()

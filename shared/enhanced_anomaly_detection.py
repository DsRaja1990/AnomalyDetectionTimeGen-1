"""
Enhanced Anomaly Detection Module
Provides advanced anomaly scoring and correlation detection
"""
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import statistics
import numpy as np

logger = logging.getLogger(__name__)


class EnhancedAnomalyDetector:
    """Advanced anomaly detection using statistical methods"""
    
    def __init__(self, correlation_threshold: float = 0.7):
        """
        Initialize enhanced detector
        
        Args:
            correlation_threshold: Minimum correlation coefficient to flag
        """
        self.correlation_threshold = correlation_threshold
    
    def advanced_anomaly_score(
        self,
        metric_name: str,
        values: List[float],
        historical_baseline: Optional[float] = None,
        current_time: Optional[datetime] = None
    ) -> Dict:
        """
        Calculate advanced anomaly score using multiple statistical methods
        
        Args:
            metric_name: Name of the metric
            values: List of metric values over time
            historical_baseline: Expected baseline value for the metric
            current_time: Current timestamp
            
        Returns:
            Dictionary with anomaly analysis results
        """
        if not values or len(values) == 0:
            return {
                "score": 0.0,
                "confidence": 0.0,
                "anomalies": [],
                "trend": "unknown"
            }
        
        try:
            # Calculate basic statistics
            values_array = np.array(values, dtype=float)
            mean = np.mean(values_array)
            stdev = np.std(values_array)
            median = np.median(values_array)
            latest = values[-1]
            
            # Calculate anomaly score components
            anomaly_score = 0.0
            confidence = 0.0
            anomalies = []
            
            # Component 1: Z-score for latest value
            if stdev > 0:
                zscore = abs((latest - mean) / stdev)
                zscore_component = min(zscore / 3.0, 1.0)  # Normalize to 0-1
                anomaly_score += zscore_component * 0.3
            
            # Component 2: Deviation from baseline
            if historical_baseline is not None and historical_baseline > 0:
                baseline_deviation = abs(latest - historical_baseline) / historical_baseline
                baseline_component = min(baseline_deviation, 1.0)
                anomaly_score += baseline_component * 0.3
            
            # Component 3: Spike detection (sudden jump)
            if len(values) >= 2:
                prev_value = values[-2]
                if prev_value > 0:
                    spike_ratio = abs(latest - prev_value) / prev_value
                    spike_component = min(spike_ratio / 2.0, 1.0)
                    anomaly_score += spike_component * 0.2
            
            # Component 4: Sustained high values
            if mean > 0:
                high_ratio = latest / mean
                sustained_component = min(max(high_ratio - 1.5, 0), 1.0)
                anomaly_score += sustained_component * 0.2
            
            # Normalize final score
            anomaly_score = min(anomaly_score, 1.0)
            
            # Calculate confidence based on data points and variability
            data_points_factor = min(len(values) / 100.0, 1.0)  # More data = more confident
            variability_factor = min(stdev / mean, 1.0) if mean > 0 else 0.5  # Less variability = more confident
            confidence = (data_points_factor + variability_factor) / 2.0
            
            # Detect anomalous points
            if stdev > 0:
                for i, value in enumerate(values):
                    zscore = abs((value - mean) / stdev)
                    if zscore > 2.5:  # More than 2.5 standard deviations
                        anomalies.append({
                            "index": i,
                            "value": value,
                            "zscore": zscore,
                            "deviation": abs(value - mean)
                        })
            
            # Determine trend
            if len(values) >= 3:
                recent_values = values[-3:]
                if recent_values[-1] > recent_values[0] * 1.1:
                    trend = "increasing"
                elif recent_values[-1] < recent_values[0] * 0.9:
                    trend = "decreasing"
                else:
                    trend = "stable"
            else:
                trend = "unknown"
            
            return {
                "score": anomaly_score,
                "confidence": confidence,
                "anomalies": anomalies,
                "trend": trend,
                "mean": mean,
                "stdev": stdev,
                "median": median,
                "latest": latest,
                "zscore": zscore if stdev > 0 else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error calculating anomaly score for {metric_name}: {e}")
            return {
                "score": 0.0,
                "confidence": 0.0,
                "anomalies": [],
                "trend": "unknown"
            }
    
    def detect_correlated_anomalies(
        self,
        metric_values: Dict[str, List[float]]
    ) -> List[Tuple[str, str, float, str]]:
        """
        Detect correlations between metrics that might indicate related anomalies
        
        Args:
            metric_values: Dictionary mapping metric names to their values
            
        Returns:
            List of tuples: (metric1, metric2, correlation, insight)
        """
        correlations = []
        
        if len(metric_values) < 2:
            return correlations
        
        try:
            metric_names = list(metric_values.keys())
            
            # Compare each pair of metrics
            for i in range(len(metric_names)):
                for j in range(i + 1, len(metric_names)):
                    metric1 = metric_names[i]
                    metric2 = metric_names[j]
                    
                    values1 = metric_values[metric1]
                    values2 = metric_values[metric2]
                    
                    # Both metrics must have data
                    if len(values1) < 2 or len(values2) < 2:
                        continue
                    
                    # Ensure same length for correlation
                    min_len = min(len(values1), len(values2))
                    values1 = values1[-min_len:]
                    values2 = values2[-min_len:]
                    
                    # Calculate Pearson correlation
                    try:
                        correlation = self._pearson_correlation(values1, values2)
                    except:
                        correlation = 0.0
                    
                    # Flag significant correlations (positive or negative)
                    if abs(correlation) > self.correlation_threshold:
                        if correlation > 0:
                            insight = f"Both metrics increasing together - possible cascading failure"
                        else:
                            insight = f"Inverse relationship - one compensating for the other"
                        
                        correlations.append((metric1, metric2, correlation, insight))
                        logger.info(f"Detected correlation: {metric1} <-> {metric2} (r={correlation:.2f}): {insight}")
            
            return correlations
            
        except Exception as e:
            logger.error(f"Error detecting correlations: {e}")
            return correlations
    
    def _pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """
        Calculate Pearson correlation coefficient
        
        Args:
            x: First data series
            y: Second data series
            
        Returns:
            Correlation coefficient (-1 to 1)
        """
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        x_array = np.array(x, dtype=float)
        y_array = np.array(y, dtype=float)
        
        x_mean = np.mean(x_array)
        y_mean = np.mean(y_array)
        
        numerator = np.sum((x_array - x_mean) * (y_array - y_mean))
        denominator = np.sqrt(
            np.sum((x_array - x_mean) ** 2) * np.sum((y_array - y_mean) ** 2)
        )
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def detect_seasonal_anomaly(
        self,
        current_value: float,
        historical_values: List[float],
        period: int = 4
    ) -> Tuple[bool, str]:
        """
        Detect if current value is anomalous compared to same period in history
        
        Args:
            current_value: Current metric value
            historical_values: Historical values (should include same period from previous cycles)
            period: Period length (e.g., 4 for hourly = 4 x 15-min intervals)
            
        Returns:
            (is_anomaly, reason)
        """
        if len(historical_values) < period:
            return False, "Insufficient historical data for seasonal analysis"
        
        try:
            # Get same period from historical data
            seasonal_values = historical_values[-period:]
            seasonal_mean = np.mean(seasonal_values)
            seasonal_stdev = np.std(seasonal_values)
            
            if seasonal_stdev == 0:
                return False, "No seasonal variability detected"
            
            zscore = abs((current_value - seasonal_mean) / seasonal_stdev)
            
            if zscore > 3.0:
                return True, f"Seasonal anomaly: {zscore:.1f} std devs from seasonal mean"
            elif zscore > 2.0:
                return True, f"Potential seasonal anomaly: {zscore:.1f} std devs from seasonal mean"
            else:
                return False, "Within expected seasonal range"
                
        except Exception as e:
            logger.error(f"Error in seasonal anomaly detection: {e}")
            return False, "Error in seasonal analysis"


def create_enhanced_detector(correlation_threshold: float = 0.7) -> EnhancedAnomalyDetector:
    """
    Factory function to create EnhancedAnomalyDetector
    
    Args:
        correlation_threshold: Correlation coefficient threshold for flagging
        
    Returns:
        EnhancedAnomalyDetector instance
    """
    logger.info(f"Creating enhanced anomaly detector with correlation_threshold={correlation_threshold}")
    return EnhancedAnomalyDetector(correlation_threshold=correlation_threshold)

"""
TimeGEN-1 Endpoint Testing Script
Tests all available endpoints to verify which ones work and validate payload formats
"""
import os
import json
import logging
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Dict, List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TimeGENEndpointTester:
    """Test all TimeGEN-1 endpoints systematically"""
    
    def __init__(self):
        self.endpoint = os.getenv("TIMEGEN1_ENDPOINT", "https://TimeGEN-1-AssurantPoc.eastus2.models.ai.azure.com")
        self.api_key = os.getenv("TIMEGEN1_API_KEY")
        
        if not self.api_key:
            raise ValueError("TIMEGEN1_API_KEY environment variable must be set")
        
        # All possible TimeGEN-1 endpoints to test
        self.endpoints_to_test = {
            "online_anomaly_detection": f"{self.endpoint}/v2/online_anomaly_detection",
            "detect_anomalies": f"{self.endpoint}/v2/detect_anomalies", 
            "forecast": f"{self.endpoint}/v1/forecast",
            "anomaly_detection_multi_series": f"{self.endpoint}/anomaly_detection_multi_series",
            "detect": f"{self.endpoint}/detect",
            "v1_anomaly_detection": f"{self.endpoint}/v1/anomaly_detection",
            "v2_anomaly_detection": f"{self.endpoint}/v2/anomaly_detection",
            "multi_series": f"{self.endpoint}/multi_series",
            "timeseries": f"{self.endpoint}/timeseries",
            "predict": f"{self.endpoint}/predict"
        }
        
        logger.info(f"TimeGEN-1 Base Endpoint: {self.endpoint}")
        logger.info(f"Testing {len(self.endpoints_to_test)} endpoints")
    
    def create_sample_multi_series_data(self) -> Dict:
        """Create sample multi-series data for testing (16 metrics)"""
        
        # Generate sample timestamps
        base_time = datetime.now() - timedelta(hours=2)
        timestamps = []
        for i in range(12):  # 12 data points (1 hour of 5-minute intervals)
            ts = base_time + timedelta(minutes=i * 5)
            timestamps.append(ts.strftime("%Y-%m-%dT%H:%M:%SZ"))
        
        # Sample 16 metrics with realistic patterns
        metrics_data = {
            "cpu_usage": [45.2, 47.1, 52.3, 48.9, 51.2, 46.8, 49.3, 53.1, 47.7, 50.4, 48.2, 45.9],
            "memory_available": [2.1, 2.0, 1.8, 1.9, 1.7, 2.0, 1.9, 1.6, 1.8, 1.7, 1.9, 2.1],
            "request_count": [1250, 1320, 1410, 1380, 1450, 1290, 1350, 1480, 1320, 1390, 1310, 1280],
            "response_time_avg": [145.2, 152.1, 168.3, 159.7, 171.2, 148.9, 155.4, 178.6, 151.3, 163.8, 149.7, 147.2],
            "http_2xx_success": [1190, 1250, 1320, 1290, 1350, 1210, 1280, 1380, 1240, 1310, 1230, 1200],
            "http_4xx_errors": [35, 42, 51, 48, 58, 41, 45, 62, 44, 52, 43, 38],
            "http_5xx_errors": [5, 8, 12, 15, 42, 18, 12, 38, 16, 28, 17, 12],  # Anomaly spike at index 4 and 7
            "exception_count": [2, 3, 5, 7, 18, 8, 5, 15, 6, 11, 7, 4],  # Correlates with 5xx errors
            "request_failed": [40, 50, 63, 63, 100, 59, 57, 100, 60, 80, 60, 50],
            "database_connections": [12, 14, 16, 18, 25, 19, 17, 28, 18, 22, 17, 15],
            "cache_hit_ratio": [0.85, 0.83, 0.79, 0.76, 0.62, 0.74, 0.78, 0.58, 0.75, 0.68, 0.77, 0.82],
            "disk_io_read": [245.6, 267.3, 298.1, 314.7, 456.2, 325.8, 289.4, 423.9, 301.5, 367.8, 278.3, 252.1],
            "disk_io_write": [156.3, 172.8, 189.4, 201.2, 298.7, 215.6, 183.9, 276.4, 194.8, 238.1, 179.2, 162.5],
            "network_bytes_in": [2048576, 2234567, 2456789, 2678901, 3987654, 2789012, 2345678, 3654321, 2567890, 3123456, 2456789, 2187654],
            "network_bytes_out": [1567890, 1789012, 1987654, 2156789, 3234567, 2267890, 1876543, 2987654, 1998765, 2456789, 1789012, 1678901],
            "active_users": [89, 95, 103, 108, 142, 115, 98, 134, 102, 119, 97, 91]
        }
        
        # Convert to timestamp->value format for TimeGEN-1
        y_data = {}
        for metric_name, values in metrics_data.items():
            y_data[metric_name] = {}
            for i, (timestamp, value) in enumerate(zip(timestamps, values)):
                y_data[metric_name][timestamp] = float(value)
        
        logger.info(f"Created sample data with {len(y_data)} metrics, {len(timestamps)} timestamps each")
        return y_data
    
    def create_test_payloads(self, y_data: Dict) -> Dict[str, Dict]:
        """Create different payload formats to test"""
        
        payloads = {
            # Format 1: Full multi-series payload (recommended format)
            "multi_series_full": {
                "freq": "5min",
                "fh": 3,
                "y": y_data,
                "clean_ex_first": True,
                "finetune_steps": 0,
                "finetune_loss": "default"
            },
            
            # Format 2: Simplified multi-series
            "multi_series_simple": {
                "y": y_data,
                "freq": "5min",
                "fh": 3
            },
            
            # Format 3: Single metric test (use first metric)
            "single_metric": {
                "y": list(y_data.values())[0],  # Just the first metric's data
                "freq": "5min",
                "fh": 3
            },
            
            # Format 4: Array format (values only)
            "array_format": {
                "y": [list(metric_data.values()) for metric_data in y_data.values()],
                "freq": "5min", 
                "fh": 3
            },
            
            # Format 5: Minimal payload
            "minimal": {
                "y": y_data
            }
        }
        
        return payloads
    
    def test_endpoint(self, name: str, url: str, payload: Dict, timeout: int = 60) -> Dict:
        """Test a specific endpoint with given payload"""
        
        result = {
            "endpoint_name": name,
            "url": url,
            "success": False,
            "status_code": None,
            "response": None,
            "error": None,
            "response_size": 0,
            "response_time": 0
        }
        
        try:
            start_time = datetime.now()
            
            body = json.dumps(payload).encode('utf-8')
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            logger.info(f"Testing {name}: {url}")
            logger.info(f"  Payload size: {len(body)} bytes")
            
            req = urllib.request.Request(url, data=body, headers=headers, method='POST')
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_data = response.read().decode('utf-8')
                result["status_code"] = response.getcode()
                result["response"] = json.loads(response_data)
                result["success"] = True
                result["response_size"] = len(response_data)
                result["response_time"] = (datetime.now() - start_time).total_seconds()
                
                logger.info(f"  ✅ SUCCESS - Status: {result['status_code']}, Size: {result['response_size']} bytes, Time: {result['response_time']:.2f}s")
                
        except urllib.error.HTTPError as e:
            result["status_code"] = e.code
            result["error"] = f"HTTP {e.code}: {e.reason}"
            try:
                error_body = e.read().decode('utf-8')
                result["error"] += f" - {error_body[:200]}"
            except:
                pass
            logger.warning(f"  ❌ HTTP ERROR - {result['error']}")
            
        except Exception as e:
            result["error"] = str(e)
            logger.warning(f"  ❌ ERROR - {result['error']}")
        
        return result
    
    def run_comprehensive_test(self) -> Dict:
        """Run comprehensive test of all endpoints and payload formats"""
        
        logger.info("=" * 80)
        logger.info("STARTING COMPREHENSIVE TIMEGEN-1 ENDPOINT TESTING")
        logger.info("=" * 80)
        
        # Create test data
        y_data = self.create_sample_multi_series_data()
        payloads = self.create_test_payloads(y_data)
        
        results = {
            "test_timestamp": datetime.now().isoformat(),
            "base_endpoint": self.endpoint,
            "total_endpoints_tested": 0,
            "successful_endpoints": [],
            "failed_endpoints": [],
            "endpoint_results": {},
            "payload_analysis": {},
            "recommendations": []
        }
        
        # Test each endpoint with each payload format
        for endpoint_name, endpoint_url in self.endpoints_to_test.items():
            logger.info(f"\n{'='*50}")
            logger.info(f"TESTING ENDPOINT: {endpoint_name}")
            logger.info(f"{'='*50}")
            
            endpoint_results = {}
            
            for payload_name, payload in payloads.items():
                logger.info(f"\n--- Testing with {payload_name} payload format ---")
                
                test_result = self.test_endpoint(endpoint_name, endpoint_url, payload, timeout=120)
                endpoint_results[payload_name] = test_result
                
                results["total_endpoints_tested"] += 1
                
                if test_result["success"]:
                    results["successful_endpoints"].append(f"{endpoint_name}_{payload_name}")
                    logger.info(f"✅ {endpoint_name} + {payload_name}: SUCCESS")
                else:
                    results["failed_endpoints"].append(f"{endpoint_name}_{payload_name}")
                    logger.info(f"❌ {endpoint_name} + {payload_name}: {test_result.get('error', 'FAILED')}")
            
            results["endpoint_results"][endpoint_name] = endpoint_results
        
        # Analyze results and create recommendations
        self._analyze_results(results)
        
        return results
    
    def _analyze_results(self, results: Dict):
        """Analyze test results and provide recommendations"""
        
        logger.info(f"\n{'='*80}")
        logger.info("TEST RESULTS ANALYSIS")
        logger.info(f"{'='*80}")
        
        successful = results["successful_endpoints"]
        failed = results["failed_endpoints"]
        
        logger.info(f"Total tests run: {results['total_endpoints_tested']}")
        logger.info(f"Successful: {len(successful)}")
        logger.info(f"Failed: {len(failed)}")
        
        if successful:
            logger.info(f"\n✅ WORKING ENDPOINTS:")
            for endpoint in successful:
                logger.info(f"  - {endpoint}")
        
        if failed:
            logger.info(f"\n❌ FAILED ENDPOINTS:")
            for endpoint in failed:
                logger.info(f"  - {endpoint}")
        
        # Generate recommendations
        recommendations = []
        
        # Find best working endpoint
        best_endpoint = None
        best_performance = float('inf')
        
        for endpoint_name, endpoint_data in results["endpoint_results"].items():
            for payload_name, test_result in endpoint_data.items():
                if test_result["success"]:
                    response_time = test_result.get("response_time", float('inf'))
                    if response_time < best_performance:
                        best_performance = response_time
                        best_endpoint = f"{endpoint_name} with {payload_name}"
        
        if best_endpoint:
            recommendations.append(f"RECOMMENDED: Use {best_endpoint} (fastest: {best_performance:.2f}s)")
        
        # Multi-series capability analysis
        multi_series_working = []
        for endpoint in successful:
            if "multi_series" in endpoint:
                multi_series_working.append(endpoint)
        
        if multi_series_working:
            recommendations.append(f"MULTI-SERIES SUPPORT: {len(multi_series_working)} working configurations found")
        else:
            recommendations.append("WARNING: No multi-series configurations working - use single-metric approach")
        
        results["recommendations"] = recommendations
        
        logger.info(f"\n📋 RECOMMENDATIONS:")
        for rec in recommendations:
            logger.info(f"  • {rec}")
    
    def save_results(self, results: Dict, filename: str = "timegen_endpoint_test_results.json"):
        """Save test results to file"""
        filepath = f"c:\\Users\\dsraja\\Documents\\PythonPoc\\{filename}"
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"\n💾 Results saved to: {filepath}")


def main():
    """Run the comprehensive endpoint testing"""
    try:
        tester = TimeGENEndpointTester()
        results = tester.run_comprehensive_test()
        tester.save_results(results)
        
        logger.info(f"\n{'='*80}")
        logger.info("TESTING COMPLETE!")
        logger.info(f"{'='*80}")
        
        # Print summary
        print(f"\nSUMMARY:")
        print(f"Total tests: {results['total_endpoints_tested']}")
        print(f"Successful: {len(results['successful_endpoints'])}")
        print(f"Failed: {len(results['failed_endpoints'])}")
        
        if results.get("recommendations"):
            print(f"\nRECOMMENDATIONS:")
            for rec in results["recommendations"]:
                print(f"  • {rec}")
        
        return results
        
    except Exception as e:
        logger.error(f"Testing failed: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    main()

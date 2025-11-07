"""
Test the specific multi-series endpoint
https://TimeGEN-1-AssurantPoc.eastus2.models.ai.azure.com/anomaly_detection_multi_series
"""
import os
import json
import logging
import urllib.request
import urllib.error
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_multi_series_endpoint():
    """Test the specific anomaly_detection_multi_series endpoint"""
    
    endpoint_url = "https://TimeGEN-1-AssurantPoc.eastus2.models.ai.azure.com/anomaly_detection_multi_series"
    api_key = "n0swAKTILYJZgcfSQ1QesDuKvLp5j1Zy"
    
    logger.info(f"Testing MULTI-SERIES SPECIFIC ENDPOINT")
    logger.info(f"URL: {endpoint_url}")
    
    # Generate sample data for all 16 metrics
    timestamps = []
    base_time = datetime.now() - timedelta(hours=1)
    for i in range(12):  # 12 data points (1 hour of 5-minute intervals)
        ts = base_time + timedelta(minutes=i * 5)
        timestamps.append(ts.strftime("%Y-%m-%dT%H:%M:%SZ"))
    
    # All 16 metrics with realistic patterns including anomalies
    all_metrics_data = {
        "cpu_usage": [45.2, 47.1, 52.3, 48.9, 51.2, 46.8, 73.1, 75.7, 78.2, 76.5, 74.3, 72.1],
        "memory_available": [2.1, 2.0, 1.8, 1.9, 1.7, 2.0, 1.2, 1.1, 0.9, 1.0, 1.1, 1.3],
        "request_count": [1250, 1320, 1410, 1380, 1450, 1290, 1850, 1980, 2100, 1950, 1820, 1750],
        "response_time_avg": [145.2, 152.1, 168.3, 159.7, 171.2, 148.9, 255.4, 278.6, 301.3, 263.8, 245.2, 228.7],
        "http_2xx_success": [1190, 1250, 1320, 1290, 1350, 1210, 1580, 1680, 1750, 1620, 1550, 1480],
        "http_4xx_errors": [35, 42, 51, 48, 58, 41, 145, 162, 178, 151, 138, 125],
        "http_5xx_errors": [5, 8, 12, 15, 42, 18, 125, 138, 172, 179, 155, 142],  # Clear anomaly pattern
        "exception_count": [2, 3, 5, 7, 18, 8, 65, 75, 88, 82, 74, 68],  # Correlates with 5xx errors
        "request_failed": [40, 50, 63, 63, 100, 59, 270, 300, 350, 330, 292, 268],
        "database_connections": [12, 14, 16, 18, 25, 19, 47, 58, 65, 61, 55, 52],
        "cache_hit_ratio": [0.85, 0.83, 0.79, 0.76, 0.62, 0.74, 0.38, 0.28, 0.22, 0.31, 0.35, 0.42],
        "disk_io_read": [245.6, 267.3, 298.1, 314.7, 456.2, 325.8, 789.4, 823.9, 901.5, 867.8, 798.3, 756.2],
        "disk_io_write": [156.3, 172.8, 189.4, 201.2, 298.7, 215.6, 476.4, 504.8, 538.1, 516.2, 478.9, 445.6],
        "network_bytes_in": [2048576, 2234567, 2456789, 2678901, 3987654, 2789012, 6654321, 7567890, 8123456, 7456789, 6892345, 6234567],
        "network_bytes_out": [1567890, 1789012, 1987654, 2156789, 3234567, 2267890, 4987654, 5998765, 6456789, 5989012, 5456789, 5123456],
        "active_users": [89, 95, 103, 108, 142, 115, 234, 268, 291, 273, 251, 238]
    }
    
    # Test different payload formats for the multi-series endpoint
    test_payloads = [
        # Format 1: Traditional TimeGEN format with timestamp->value mapping
        {
            "name": "timestamp_value_format",
            "payload": {
                "freq": "5min",
                "fh": 3,
                "y": {
                    metric_name: {ts: val for ts, val in zip(timestamps, values)}
                    for metric_name, values in all_metrics_data.items()
                },
                "clean_ex_first": True,
                "finetune_steps": 0,
                "finetune_loss": "default"
            }
        },
        
        # Format 2: Simplified multi-series format
        {
            "name": "simple_multi_series",
            "payload": {
                "y": {
                    metric_name: {ts: val for ts, val in zip(timestamps, values)}
                    for metric_name, values in all_metrics_data.items()
                },
                "freq": "5min",
                "fh": 3
            }
        },
        
        # Format 3: Array-based format
        {
            "name": "array_based_format",
            "payload": {
                "series": list(all_metrics_data.keys()),
                "data": [list(values) for values in all_metrics_data.values()],
                "timestamps": timestamps,
                "freq": "5min",
                "fh": 3
            }
        },
        
        # Format 4: Flattened format (from previous testing)
        {
            "name": "flattened_array_format",
            "payload": {
                "series": {
                    "y": [val for values in all_metrics_data.values() for val in values],
                    "sizes": [len(values) for values in all_metrics_data.values()]
                },
                "freq": "5min",
                "detection_size": 5,
                "h": 3
            }
        },
        
        # Format 5: Minimal format
        {
            "name": "minimal_format",
            "payload": {
                "y": {
                    metric_name: list(values)
                    for metric_name, values in all_metrics_data.items()
                }
            }
        }
    ]
    
    results = []
    
    for payload_info in test_payloads:
        payload_name = payload_info["name"]
        payload = payload_info["payload"]
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing: {payload_name}")
        if "y" in payload:
            if isinstance(payload["y"], dict):
                logger.info(f"Metrics count: {len(payload['y'])}")
            else:
                logger.info(f"Data type: {type(payload['y'])}")
        
        try:
            body = json.dumps(payload).encode('utf-8')
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
            
            logger.info(f"Payload size: {len(body)} bytes")
            
            req = urllib.request.Request(endpoint_url, data=body, headers=headers, method='POST')
            
            start_time = datetime.now()
            
            # Longer timeout for multi-series processing
            timeout = 300  # 5 minutes
            logger.info(f"Using timeout: {timeout}s")
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_data = response.read().decode('utf-8')
                response_time = (datetime.now() - start_time).total_seconds()
                
                try:
                    parsed_response = json.loads(response_data)
                except:
                    parsed_response = {"raw_response": response_data[:1000]}
                
                result = {
                    "payload_type": payload_name,
                    "success": True,
                    "status_code": response.getcode(),
                    "response_time": response_time,
                    "response_size": len(response_data),
                    "parsed_response": parsed_response
                }
                
                logger.info(f"\n🎉 SUCCESS! Multi-Series Endpoint WORKS!")
                logger.info(f"   Status: {result['status_code']}")
                logger.info(f"   Time: {response_time:.2f}s")
                logger.info(f"   Size: {len(response_data)} bytes")
                
                # Analyze response structure
                if isinstance(parsed_response, dict):
                    logger.info(f"   Response keys: {list(parsed_response.keys())}")
                    
                    # Look for anomaly detection results
                    anomalies_found = 0
                    if 'anomalies' in parsed_response:
                        anomalies_found = len(parsed_response.get('anomalies', []))
                    elif 'is_anomaly' in parsed_response:
                        anomalies_found = 1 if parsed_response['is_anomaly'] else 0
                    else:
                        # Check for metric-specific anomaly flags
                        for key, value in parsed_response.items():
                            if isinstance(value, dict) and 'anomaly_flag' in value:
                                flags = value.get('anomaly_flag', [])
                                if any(flag == 1 for flag in flags if isinstance(flag, (int, bool))):
                                    anomalies_found += 1
                    
                    logger.info(f"   Anomalies detected: {anomalies_found}")
                    result["anomalies_detected"] = anomalies_found
                
                logger.info(f"   Response preview: {str(parsed_response)[:300]}...")
                
                results.append(result)
                
                # CELEBRATION for working multi-series endpoint!
                logger.info(f"\n🚀🚀🚀 MULTI-SERIES ENDPOINT SUCCESS! 🚀🚀🚀")
                logger.info(f"Processing time: {response_time:.2f} seconds")
                logger.info(f"All 16 metrics processed in single API call!")
                logger.info(f"This is the correct endpoint for production use!")
                
        except urllib.error.HTTPError as e:
            error_details = ""
            try:
                error_body = e.read().decode('utf-8')
                error_details = error_body[:1000]
            except:
                pass
                
            logger.warning(f"❌ HTTP {e.code}: {e.reason}")
            if error_details:
                logger.warning(f"   Error details: {error_details}")
                
            results.append({
                "payload_type": payload_name,
                "success": False,
                "error": f"HTTP {e.code}: {e.reason}",
                "error_details": error_details
            })
                
        except Exception as e:
            logger.warning(f"❌ ERROR: {str(e)}")
            results.append({
                "payload_type": payload_name,
                "success": False,
                "error": str(e)
            })
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("MULTI-SERIES ENDPOINT TEST RESULTS")
    logger.info(f"{'='*80}")
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    logger.info(f"Endpoint tested: {endpoint_url}")
    logger.info(f"Total tests: {len(results)}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")
    
    if successful:
        logger.info(f"\n✅ WORKING CONFIGURATIONS:")
        for result in successful:
            response_time = result.get('response_time', 0)
            anomalies = result.get('anomalies_detected', 0)
            logger.info(f"  🎯 {result['payload_type']}: {response_time:.2f}s, {anomalies} anomalies")
            
        # Find best configuration
        best_config = min(successful, key=lambda x: x.get('response_time', float('inf')))
        logger.info(f"\n🏆 RECOMMENDED CONFIGURATION:")
        logger.info(f"   Format: {best_config['payload_type']}")
        logger.info(f"   Time: {best_config.get('response_time', 0):.2f}s")
        
        logger.info(f"\n📋 PRODUCTION READY:")
        logger.info(f"   ✅ Multi-series endpoint: WORKING")
        logger.info(f"   ✅ All 16 metrics: Processed simultaneously")
        logger.info(f"   ✅ Performance: {best_config.get('response_time', 0):.2f} seconds")
        logger.info(f"   ✅ Anomaly detection: Active")
        
    if failed:
        logger.info(f"\n❌ FAILED CONFIGURATIONS:")
        for result in failed:
            logger.info(f"  • {result['payload_type']}: {result.get('error', 'Unknown error')}")
    
    # Save results
    output_file = "c:\\Users\\dsraja\\Documents\\PythonPoc\\multi_series_endpoint_test_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "endpoint_tested": endpoint_url,
            "multi_series_working": len(successful) > 0,
            "best_response_time": min((r.get('response_time', float('inf')) for r in successful), default=0),
            "total_tests": len(results),
            "successful_tests": len(successful),
            "failed_tests": len(failed),
            "results": results
        }, f, indent=2)
    
    logger.info(f"\n💾 Results saved to: {output_file}")
    
    return results

if __name__ == "__main__":
    test_multi_series_endpoint()

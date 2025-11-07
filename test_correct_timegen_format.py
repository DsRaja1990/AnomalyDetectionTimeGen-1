"""
TimeGEN-1 Correct Payload Format Test
Based on API error messages, testing with correct field names
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

def test_correct_payload_format():
    """Test TimeGEN-1 with the correct payload format based on API errors"""
    
    endpoint_url = "https://TimeGEN-1-AssurantPoc.eastus2.models.ai.azure.com/v2/online_anomaly_detection"
    api_key = "n0swAKTILYJZgcfSQ1QesDuKvLp5j1Zy"
    
    # Based on the 422 error, TimeGEN-1 expects these fields:
    # - "series" (instead of "y") 
    # - "detection_size"
    # - "h" (instead of "fh")
    
    # Sample data - realistic metrics
    timestamps = []
    base_time = datetime.now() - timedelta(hours=1)
    for i in range(10):  # 10 data points
        ts = base_time + timedelta(minutes=i * 5)
        timestamps.append(ts.strftime("%Y-%m-%dT%H:%M:%SZ"))
    
    # Test payloads with correct TimeGEN-1 format
    test_payloads = [
        # 1. Single series correct format
        {
            "name": "single_series_correct",
            "payload": {
                "series": {
                    "cpu_usage": {ts: val for ts, val in zip(timestamps, [45.2, 47.1, 52.3, 48.9, 51.2, 46.8, 73.1, 75.7, 78.2, 76.5])}
                },
                "detection_size": 5,
                "h": 1
            }
        },
        
        # 2. Multi-series correct format (3 metrics)  
        {
            "name": "multi_series_correct",
            "payload": {
                "series": {
                    "cpu_usage": {ts: val for ts, val in zip(timestamps, [45.2, 47.1, 52.3, 48.9, 51.2, 46.8, 73.1, 75.7, 78.2, 76.5])},
                    "memory_available": {ts: val for ts, val in zip(timestamps, [2.1, 2.0, 1.8, 1.9, 1.7, 2.0, 1.2, 1.1, 0.9, 1.0])},
                    "http_5xx_errors": {ts: val for ts, val in zip(timestamps, [5, 8, 12, 15, 18, 12, 42, 38, 45, 41])}
                },
                "detection_size": 5,
                "h": 1
            }
        },
        
        # 3. All 16 metrics - full multi-series
        {
            "name": "all_16_metrics_correct", 
            "payload": {
                "series": {
                    "cpu_usage": {ts: val for ts, val in zip(timestamps, [45.2, 47.1, 52.3, 48.9, 51.2, 46.8, 73.1, 75.7, 78.2, 76.5])},
                    "memory_available": {ts: val for ts, val in zip(timestamps, [2.1, 2.0, 1.8, 1.9, 1.7, 2.0, 1.2, 1.1, 0.9, 1.0])},
                    "request_count": {ts: val for ts, val in zip(timestamps, [1250, 1320, 1410, 1380, 1450, 1290, 1850, 1980, 2100, 1950])},
                    "response_time_avg": {ts: val for ts, val in zip(timestamps, [145.2, 152.1, 168.3, 159.7, 171.2, 148.9, 255.4, 278.6, 301.3, 263.8])},
                    "http_2xx_success": {ts: val for ts, val in zip(timestamps, [1190, 1250, 1320, 1290, 1350, 1210, 1580, 1680, 1750, 1620])},
                    "http_4xx_errors": {ts: val for ts, val in zip(timestamps, [35, 42, 51, 48, 58, 41, 145, 162, 178, 151])},
                    "http_5xx_errors": {ts: val for ts, val in zip(timestamps, [5, 8, 12, 15, 42, 18, 125, 138, 172, 179])},
                    "exception_count": {ts: val for ts, val in zip(timestamps, [2, 3, 5, 7, 18, 8, 65, 75, 88, 82])},
                    "request_failed": {ts: val for ts, val in zip(timestamps, [40, 50, 63, 63, 100, 59, 270, 300, 350, 330])},
                    "database_connections": {ts: val for ts, val in zip(timestamps, [12, 14, 16, 18, 25, 19, 47, 58, 65, 61])},
                    "cache_hit_ratio": {ts: val for ts, val in zip(timestamps, [0.85, 0.83, 0.79, 0.76, 0.62, 0.74, 0.38, 0.28, 0.22, 0.31])},
                    "disk_io_read": {ts: val for ts, val in zip(timestamps, [245.6, 267.3, 298.1, 314.7, 456.2, 325.8, 789.4, 823.9, 901.5, 867.8])},
                    "disk_io_write": {ts: val for ts, val in zip(timestamps, [156.3, 172.8, 189.4, 201.2, 298.7, 215.6, 476.4, 504.8, 538.1, 516.2])},
                    "network_bytes_in": {ts: val for ts, val in zip(timestamps, [2048576, 2234567, 2456789, 2678901, 3987654, 2789012, 6654321, 7567890, 8123456, 7456789])},
                    "network_bytes_out": {ts: val for ts, val in zip(timestamps, [1567890, 1789012, 1987654, 2156789, 3234567, 2267890, 4987654, 5998765, 6456789, 5989012])},
                    "active_users": {ts: val for ts, val in zip(timestamps, [89, 95, 103, 108, 142, 115, 234, 268, 291, 273])}
                },
                "detection_size": 5,
                "h": 1
            }
        },
        
        # 4. Different detection_size values
        {
            "name": "detection_size_3",
            "payload": {
                "series": {
                    "cpu_usage": {ts: val for ts, val in zip(timestamps, [45.2, 47.1, 52.3, 48.9, 51.2, 46.8, 73.1, 75.7, 78.2, 76.5])},
                    "http_5xx_errors": {ts: val for ts, val in zip(timestamps, [5, 8, 12, 15, 18, 12, 42, 38, 45, 41])}
                },
                "detection_size": 3,
                "h": 1
            }
        }
    ]
    
    results = []
    
    logger.info(f"Testing TimeGEN-1 with CORRECT payload format")
    logger.info(f"URL: {endpoint_url}")
    
    for payload_info in test_payloads:
        payload_name = payload_info["name"]
        payload = payload_info["payload"]
        
        logger.info(f"\n{'='*50}")
        logger.info(f"Testing: {payload_name}")
        logger.info(f"Metrics count: {len(payload['series'])}")
        logger.info(f"Detection size: {payload['detection_size']}")
        
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
            
            # Timeout based on complexity
            timeout = 30 if len(payload['series']) <= 3 else 120
            logger.info(f"Using timeout: {timeout}s")
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_data = response.read().decode('utf-8')
                response_time = (datetime.now() - start_time).total_seconds()
                
                try:
                    parsed_response = json.loads(response_data)
                except:
                    parsed_response = {"raw": response_data[:300]}
                
                result = {
                    "payload_type": payload_name,
                    "success": True,
                    "status_code": response.getcode(),
                    "response_time": response_time,
                    "response_size": len(response_data),
                    "metrics_count": len(payload['series']),
                    "detection_size": payload['detection_size'],
                    "response_preview": str(parsed_response)[:500]
                }
                
                logger.info(f"✅ SUCCESS!")
                logger.info(f"   Status: {result['status_code']}")
                logger.info(f"   Time: {response_time:.2f}s") 
                logger.info(f"   Size: {len(response_data)} bytes")
                logger.info(f"   Response preview: {str(parsed_response)[:150]}...")
                
                # Check for anomaly results
                if isinstance(parsed_response, dict):
                    # Count metrics with anomalies detected
                    anomaly_metrics = []
                    for metric, data in parsed_response.items():
                        if isinstance(data, dict) and 'anomaly_flag' in data:
                            flags = data['anomaly_flag']
                            if any(flag == 1 for flag in flags):
                                anomaly_metrics.append(metric)
                    
                    if anomaly_metrics:
                        logger.info(f"   🚨 Anomalies detected in: {anomaly_metrics}")
                        result["anomalies_detected"] = anomaly_metrics
                
                results.append(result)
                
                # If this is the full 16-metric test and it works, we're golden!
                if payload_name == "all_16_metrics_correct" and response.getcode() == 200:
                    logger.info(f"🎉 MULTI-SERIES SUCCESS! All 16 metrics processed in {response_time:.2f}s")
                
        except urllib.error.HTTPError as e:
            error_details = ""
            try:
                error_body = e.read().decode('utf-8')
                error_details = error_body[:300]
            except:
                pass
                
            logger.warning(f"❌ HTTP {e.code}: {e.reason}")
            if error_details:
                logger.warning(f"   Error details: {error_details}")
                
            results.append({
                "payload_type": payload_name,
                "success": False,
                "error": f"HTTP {e.code}: {e.reason}",
                "error_details": error_details,
                "metrics_count": len(payload['series']),
                "detection_size": payload['detection_size']
            })
                
        except Exception as e:
            logger.warning(f"❌ ERROR: {str(e)}")
            results.append({
                "payload_type": payload_name,
                "success": False,
                "error": str(e),
                "metrics_count": len(payload['series']),
                "detection_size": payload['detection_size']
            })
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("TEST RESULTS SUMMARY")
    logger.info(f"{'='*80}")
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    logger.info(f"Total tests: {len(results)}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")
    
    if successful:
        logger.info(f"\n✅ WORKING CONFIGURATIONS:")
        for result in successful:
            metrics_count = result.get('metrics_count', 0)
            response_time = result.get('response_time', 0)
            anomalies = len(result.get('anomalies_detected', []))
            logger.info(f"  • {result['payload_type']}: {metrics_count} metrics, {response_time:.2f}s, {anomalies} anomalies")
    
    if failed:
        logger.info(f"\n❌ FAILED CONFIGURATIONS:")
        for result in failed:
            logger.info(f"  • {result['payload_type']}: {result.get('error', 'Unknown error')}")
    
    # Recommendations
    logger.info(f"\n📋 RECOMMENDATIONS:")
    if successful:
        # Find best performing config
        best_config = max(successful, key=lambda x: x.get('metrics_count', 0))
        logger.info(f"  🎯 RECOMMENDED: {best_config['payload_type']} - {best_config.get('metrics_count')} metrics in {best_config.get('response_time', 0):.2f}s")
        
        if any('16_metrics' in r['payload_type'] for r in successful):
            logger.info(f"  🎉 MULTI-SERIES FULLY WORKING: All 16 metrics can be processed simultaneously!")
        else:
            max_metrics = max(r.get('metrics_count', 0) for r in successful)
            logger.info(f"  ⚠️  MULTI-SERIES PARTIAL: Up to {max_metrics} metrics supported")
    else:
        logger.info(f"  ❌ NO WORKING CONFIGURATIONS - Check API key and endpoint")
    
    # Save results  
    with open("c:\\Users\\dsraja\\Documents\\PythonPoc\\timegen_correct_format_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "endpoint_tested": endpoint_url,
            "total_tests": len(results),
            "successful_tests": len(successful),
            "failed_tests": len(failed),
            "results": results,
            "multi_series_supported": any('16_metrics' in r['payload_type'] for r in successful),
            "max_metrics_supported": max((r.get('metrics_count', 0) for r in successful), default=0)
        }, f, indent=2)
    
    return results

if __name__ == "__main__":
    test_correct_payload_format()

"""
Quick TimeGEN-1 Endpoint Test
Test endpoints with shorter timeout and focused payload formats
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

def test_timegen_endpoint_quick():
    """Quick test of TimeGEN-1 endpoints with realistic payloads"""
    
    endpoint_base = "https://TimeGEN-1-AssurantPoc.eastus2.models.ai.azure.com"
    api_key = "n0swAKTILYJZgcfSQ1QesDuKvLp5j1Zy"
    
    # Test endpoints in order of likelihood to work
    endpoints_to_test = [
        ("online_anomaly_v2", f"{endpoint_base}/v2/online_anomaly_detection"),
        ("detect_anomalies_v2", f"{endpoint_base}/v2/detect_anomalies"), 
        ("forecast_v1", f"{endpoint_base}/v1/forecast"),
        ("anomaly_detection", f"{endpoint_base}/anomaly_detection"),
        ("detect", f"{endpoint_base}/detect"),
        ("timeseries", f"{endpoint_base}/timeseries")
    ]
    
    # Sample data - single metric first (CPU usage)
    timestamps = []
    base_time = datetime.now() - timedelta(hours=1)
    for i in range(8):  # 8 data points (40 minutes)
        ts = base_time + timedelta(minutes=i * 5)
        timestamps.append(ts.strftime("%Y-%m-%dT%H:%M:%SZ"))
    
    cpu_values = [45.2, 47.1, 52.3, 48.9, 51.2, 46.8, 73.1, 75.7]  # Anomaly at end
    
    # Test payloads - start simple
    test_payloads = [
        # 1. Single metric - TimeGEN-1 standard format
        {
            "name": "single_metric_dict",
            "payload": {
                "y": {ts: val for ts, val in zip(timestamps, cpu_values)},
                "freq": "5min",
                "fh": 1
            }
        },
        
        # 2. Single metric - array format
        {
            "name": "single_metric_array", 
            "payload": {
                "y": cpu_values,
                "freq": "5min",
                "fh": 1
            }
        },
        
        # 3. Multi-series (only 3 metrics)
        {
            "name": "multi_series_small",
            "payload": {
                "y": {
                    "cpu_usage": {ts: val for ts, val in zip(timestamps, cpu_values)},
                    "memory_available": {ts: val for ts, val in zip(timestamps, [2.1, 2.0, 1.8, 1.9, 1.7, 2.0, 1.2, 1.1])},
                    "http_5xx_errors": {ts: val for ts, val in zip(timestamps, [5, 8, 12, 15, 18, 12, 42, 38])}
                },
                "freq": "5min",
                "fh": 1
            }
        }
    ]
    
    results = []
    
    for endpoint_name, endpoint_url in endpoints_to_test:
        logger.info(f"\n{'='*60}")
        logger.info(f"TESTING: {endpoint_name}")
        logger.info(f"URL: {endpoint_url}")
        
        for payload_info in test_payloads:
            payload_name = payload_info["name"]
            payload = payload_info["payload"]
            
            logger.info(f"\n--- Testing {payload_name} ---")
            
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
                
                # Shorter timeout for quick testing
                with urllib.request.urlopen(req, timeout=30) as response:
                    response_data = response.read().decode('utf-8')
                    response_time = (datetime.now() - start_time).total_seconds()
                    
                    try:
                        parsed_response = json.loads(response_data)
                    except:
                        parsed_response = {"raw": response_data[:200]}
                    
                    result = {
                        "endpoint": endpoint_name,
                        "payload_type": payload_name,
                        "success": True,
                        "status_code": response.getcode(),
                        "response_time": response_time,
                        "response_size": len(response_data),
                        "response_sample": str(parsed_response)[:300]
                    }
                    
                    logger.info(f"✅ SUCCESS - Status: {result['status_code']}, Time: {response_time:.2f}s, Size: {len(response_data)} bytes")
                    logger.info(f"Response preview: {str(parsed_response)[:100]}...")
                    
                    results.append(result)
                    
                    # If this works, we found a good combination!
                    if response.getcode() == 200:
                        logger.info(f"🎉 FOUND WORKING ENDPOINT: {endpoint_name} + {payload_name}")
                        
            except urllib.error.HTTPError as e:
                logger.warning(f"❌ HTTP {e.code}: {e.reason}")
                try:
                    error_body = e.read().decode('utf-8')
                    logger.warning(f"Error details: {error_body[:200]}")
                except:
                    pass
                    
                results.append({
                    "endpoint": endpoint_name,
                    "payload_type": payload_name,
                    "success": False,
                    "error": f"HTTP {e.code}: {e.reason}",
                    "error_details": error_body[:200] if 'error_body' in locals() else ""
                })
                
            except Exception as e:
                logger.warning(f"❌ ERROR: {str(e)}")
                results.append({
                    "endpoint": endpoint_name,
                    "payload_type": payload_name,
                    "success": False,
                    "error": str(e)
                })
    
    # Print summary
    logger.info(f"\n{'='*80}")
    logger.info("QUICK TEST SUMMARY")
    logger.info(f"{'='*80}")
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    logger.info(f"Total tests: {len(results)}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")
    
    if successful:
        logger.info(f"\n✅ WORKING COMBINATIONS:")
        for result in successful:
            logger.info(f"  • {result['endpoint']} + {result['payload_type']} ({result.get('response_time', 0):.2f}s)")
    
    if failed:
        logger.info(f"\n❌ FAILED COMBINATIONS:")
        for result in failed:
            logger.info(f"  • {result['endpoint']} + {result['payload_type']}: {result.get('error', 'Unknown error')}")
    
    # Save results
    with open("c:\\Users\\dsraja\\Documents\\PythonPoc\\quick_endpoint_test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(results),
            "successful_tests": len(successful),
            "failed_tests": len(failed),
            "results": results,
            "recommendations": []
        }, f, indent=2)
    
    return results

if __name__ == "__main__":
    test_timegen_endpoint_quick()

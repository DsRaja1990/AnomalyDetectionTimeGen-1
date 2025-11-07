"""
Test multi-series endpoint with smaller payload to avoid timeout
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

def test_small_multi_series():
    """Test with minimal data to avoid timeout and find correct format"""
    
    endpoint_url = "https://TimeGEN-1-AssurantPoc.eastus2.models.ai.azure.com/anomaly_detection_multi_series"
    api_key = "n0swAKTILYJZgcfSQ1QesDuKvLp5j1Zy"
    
    logger.info(f"Testing MULTI-SERIES with MINIMAL data to avoid timeout")
    logger.info(f"URL: {endpoint_url}")
    
    # SMALL dataset - only 6 data points, 3 key metrics
    timestamps = []
    base_time = datetime.now() - timedelta(minutes=30)
    for i in range(6):  # Only 6 data points
        ts = base_time + timedelta(minutes=i * 5)
        timestamps.append(ts.strftime("%Y-%m-%dT%H:%M:%SZ"))
    
    # Only 3 critical metrics with clear anomaly pattern
    small_metrics = {
        "cpu_usage": [45.2, 47.1, 52.3, 48.9, 75.1, 78.2],      # Anomaly at end
        "memory_available": [2.1, 2.0, 1.8, 1.9, 1.2, 1.0],      # Correlates with CPU
        "http_5xx_errors": [5, 8, 12, 15, 42, 38]                # Clear anomaly spike
    }
    
    # Test different payload formats - start very simple
    test_payloads = [
        # Format 1: Single metric first
        {
            "name": "single_metric_cpu",
            "payload": {
                "y": {
                    "cpu_usage": {ts: val for ts, val in zip(timestamps, small_metrics["cpu_usage"])}
                },
                "freq": "5min",
                "fh": 1
            }
        },
        
        # Format 2: Two metrics
        {
            "name": "two_metrics",
            "payload": {
                "y": {
                    "cpu_usage": {ts: val for ts, val in zip(timestamps, small_metrics["cpu_usage"])},
                    "http_5xx_errors": {ts: val for ts, val in zip(timestamps, small_metrics["http_5xx_errors"])}
                },
                "freq": "5min",
                "fh": 1
            }
        },
        
        # Format 3: All 3 metrics
        {
            "name": "three_metrics",
            "payload": {
                "y": {
                    metric_name: {ts: val for ts, val in zip(timestamps, values)}
                    for metric_name, values in small_metrics.items()
                },
                "freq": "5min",
                "fh": 1
            }
        },
        
        # Format 4: Array format
        {
            "name": "array_format_small",
            "payload": {
                "y": [list(values) for values in small_metrics.values()],
                "freq": "5min",
                "fh": 1
            }
        },
        
        # Format 5: Ultra minimal
        {
            "name": "ultra_minimal",
            "payload": {
                "y": small_metrics["cpu_usage"]  # Just one metric as array
            }
        }
    ]
    
    results = []
    
    for payload_info in test_payloads:
        payload_name = payload_info["name"]
        payload = payload_info["payload"]
        
        logger.info(f"\n{'='*50}")
        logger.info(f"Testing: {payload_name}")
        
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
            
            # Shorter timeout for small data
            timeout = 60  # 1 minute
            logger.info(f"Using timeout: {timeout}s")
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_data = response.read().decode('utf-8')
                response_time = (datetime.now() - start_time).total_seconds()
                
                try:
                    parsed_response = json.loads(response_data)
                except:
                    parsed_response = {"raw_response": response_data[:500]}
                
                result = {
                    "payload_type": payload_name,
                    "success": True,
                    "status_code": response.getcode(),
                    "response_time": response_time,
                    "response_size": len(response_data),
                    "payload_size": len(body),
                    "parsed_response": parsed_response
                }
                
                logger.info(f"\n🎉 SUCCESS! Multi-Series Endpoint WORKS!")
                logger.info(f"   Status: {result['status_code']}")
                logger.info(f"   Time: {response_time:.2f}s")
                logger.info(f"   Payload: {len(body)} bytes")
                logger.info(f"   Response: {len(response_data)} bytes")
                
                # Analyze response
                if isinstance(parsed_response, dict):
                    logger.info(f"   Response keys: {list(parsed_response.keys())}")
                    logger.info(f"   Response sample: {str(parsed_response)[:200]}...")
                    
                    # Look for anomaly indicators
                    anomaly_indicators = []
                    for key, value in parsed_response.items():
                        if 'anomaly' in key.lower():
                            anomaly_indicators.append(f"{key}: {value}")
                    
                    if anomaly_indicators:
                        logger.info(f"   🚨 Anomaly indicators: {anomaly_indicators}")
                
                results.append(result)
                
                # This is a breakthrough - we found the working format!
                logger.info(f"\n🚀 BREAKTHROUGH: Multi-series endpoint is working!")
                logger.info(f"Correct format identified for: {payload_name}")
                
        except urllib.error.HTTPError as e:
            error_details = ""
            try:
                error_body = e.read().decode('utf-8')
                error_details = error_body[:300]
            except:
                pass
                
            logger.warning(f"❌ HTTP {e.code}: {e.reason}")
            if error_details:
                logger.warning(f"   Error: {error_details}")
                
            results.append({
                "payload_type": payload_name,
                "success": False,
                "error": f"HTTP {e.code}: {e.reason}",
                "error_details": error_details,
                "payload_size": len(json.dumps(payload).encode('utf-8'))
            })
                
        except Exception as e:
            logger.warning(f"❌ ERROR: {str(e)}")
            results.append({
                "payload_type": payload_name,
                "success": False,
                "error": str(e),
                "payload_size": len(json.dumps(payload).encode('utf-8'))
            })
    
    # Analysis
    logger.info(f"\n{'='*70}")
    logger.info("SMALL MULTI-SERIES TEST RESULTS")
    logger.info(f"{'='*70}")
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    logger.info(f"Total tests: {len(results)}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")
    
    if successful:
        logger.info(f"\n✅ WORKING FORMATS:")
        for result in successful:
            logger.info(f"  🎯 {result['payload_type']}: {result.get('response_time', 0):.2f}s, {result.get('payload_size', 0)} bytes")
        
        best_format = min(successful, key=lambda x: x.get('response_time', float('inf')))
        logger.info(f"\n🏆 BEST FORMAT: {best_format['payload_type']}")
        logger.info(f"   Response time: {best_format.get('response_time', 0):.2f}s")
        logger.info(f"   Payload size: {best_format.get('payload_size', 0)} bytes")
        
        logger.info(f"\n📋 NEXT STEPS:")
        logger.info(f"   ✅ Scale up to more metrics using working format")
        logger.info(f"   ✅ Integrate into production system")
        logger.info(f"   ✅ Use for all 16 metrics simultaneously")
        
    else:
        logger.info(f"\n❌ ALL FORMATS FAILED:")
        for result in failed:
            logger.info(f"  • {result['payload_type']}: {result.get('error', 'Unknown')}")
        
        if any('timeout' in str(r.get('error', '')).lower() for r in failed):
            logger.info(f"\n💡 TIMEOUT PATTERN DETECTED:")
            logger.info(f"   - Endpoint exists and accepts requests")
            logger.info(f"   - Model may be cold or need smaller batches")
            logger.info(f"   - Try even smaller datasets or different format")
    
    # Save results
    with open("c:\\Users\\dsraja\\Documents\\PythonPoc\\small_multi_series_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "endpoint": endpoint_url,
            "working_formats": len(successful),
            "results": results
        }, f, indent=2)
    
    return results

if __name__ == "__main__":
    test_small_multi_series()

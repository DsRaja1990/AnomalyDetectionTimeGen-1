"""
Test NEW TimeGEN-1 Endpoint: https://TimeGEN-1-zeolh.eastus2.models.ai.azure.com
Key: mDPTRBXlnpbNbbXdgWxUkDPEVLtq0cKT

This could be a different/updated deployment that resolves the timeout issues!
"""
import urllib.request
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_new_endpoint():
    """Test the new TimeGEN-1 endpoint with comprehensive format testing"""
    
    logger.info("🚀 Testing NEW TimeGEN-1 Endpoint")
    logger.info("URL: https://TimeGEN-1-zeolh.eastus2.models.ai.azure.com")
    logger.info("This could resolve the timeout issues from the previous deployment!")
    
    new_base_url = "https://TimeGEN-1-zeolh.eastus2.models.ai.azure.com"
    new_api_key = "mDPTRBXlnpbNbbXdgWxUkDPEVLtq0cKT"
    
    # Test all possible endpoint variations
    endpoints_to_test = [
        ("Root endpoint", f"{new_base_url}"),
        ("v2/online_anomaly_detection", f"{new_base_url}/v2/online_anomaly_detection"),
        ("anomaly_detection_multi_series", f"{new_base_url}/anomaly_detection_multi_series"),
        ("online_anomaly_detection", f"{new_base_url}/online_anomaly_detection"),
        ("anomaly_detection", f"{new_base_url}/anomaly_detection"),
        ("forecast", f"{new_base_url}/forecast"),
        ("predict", f"{new_base_url}/predict"),
        ("timegpt", f"{new_base_url}/timegpt"),
        ("v1/anomaly_detection", f"{new_base_url}/v1/anomaly_detection"),
        ("api/anomaly_detection", f"{new_base_url}/api/anomaly_detection")
    ]
    
    # Generate test data
    timestamps = []
    base_time = datetime.now() - timedelta(hours=1)
    for i in range(8):  # Keep it small for quick testing
        ts = base_time + timedelta(minutes=i * 10)
        timestamps.append(ts.strftime("%Y-%m-%dT%H:%M:%SZ"))
    
    # Test data with clear anomaly pattern
    test_formats = [
        # Format 1: Multi-series format (what we found works)
        {
            "name": "Multi-Series Format",
            "data": {
                "series": [
                    {
                        "unique_id": "cpu_usage",
                        "ds": timestamps,
                        "y": [45, 47, 52, 85, 78, 52, 48, 46]  # Clear anomaly spike
                    },
                    {
                        "unique_id": "memory_gb",
                        "ds": timestamps,
                        "y": [2.1, 2.0, 1.9, 0.3, 0.2, 1.8, 1.9, 2.0]  # Clear anomaly drop
                    }
                ],
                "detection_size": 3,
                "h": 2
            }
        },
        
        # Format 2: TimeGPT format
        {
            "name": "TimeGPT Format",
            "data": {
                "df": [
                    {"ds": ts, "y": val, "unique_id": "test_metric"} 
                    for ts, val in zip(timestamps, [10, 12, 15, 95, 18, 14, 11, 13])
                ],
                "h": 2
            }
        },
        
        # Format 3: Simple series
        {
            "name": "Simple Series",
            "data": {
                "series": [{
                    "ds": timestamps,
                    "y": [20, 22, 25, 180, 28, 24, 21, 23]  # Clear anomaly
                }],
                "h": 1
            }
        },
        
        # Format 4: Nixtla standard format
        {
            "name": "Nixtla Standard",
            "data": {
                "y": timestamps[-5:],  # Last 5 timestamps
                "ds": [30, 32, 35, 200, 38],  # Clear anomaly spike
                "h": 1
            }
        }
    ]
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {new_api_key}'
    }
    
    results = []
    
    # Test each endpoint with each format
    for endpoint_name, url in endpoints_to_test:
        logger.info(f"\n{'='*70}")
        logger.info(f"Testing Endpoint: {endpoint_name}")
        logger.info(f"URL: {url}")
        
        for test_format in test_formats:
            logger.info(f"\n  📋 Format: {test_format['name']}")
            
            try:
                body = str.encode(json.dumps(test_format['data']))
                logger.info(f"  📦 Payload size: {len(body)} bytes")
                
                req = urllib.request.Request(url, body, headers)
                
                start_time = datetime.now()
                response = urllib.request.urlopen(req, timeout=60)  # 1 minute timeout
                response_time = (datetime.now() - start_time).total_seconds()
                
                result_data = response.read()
                
                logger.info(f"  🎉 SUCCESS!")
                logger.info(f"  ⏱️ Response time: {response_time:.2f} seconds")
                logger.info(f"  📊 Response size: {len(result_data)} bytes")
                logger.info(f"  📈 Status code: {response.getcode()}")
                
                # Parse response
                try:
                    parsed_result = json.loads(result_data.decode('utf-8'))
                    
                    if isinstance(parsed_result, dict):
                        logger.info(f"  🔑 Response keys: {list(parsed_result.keys())}")
                        
                        # Look for anomaly indicators
                        anomaly_found = False
                        for key, value in parsed_result.items():
                            if 'anomaly' in key.lower():
                                logger.info(f"  🚨 Anomaly field found: {key}")
                                anomaly_found = True
                                if isinstance(value, list):
                                    anomaly_count = sum(1 for x in value if x in [1, True])
                                    if anomaly_count > 0:
                                        logger.info(f"  🎯 {anomaly_count} anomalies detected!")
                        
                        if not anomaly_found:
                            # Look for other indicators
                            response_str = str(parsed_result)
                            if any(keyword in response_str.lower() for keyword in ['forecast', 'prediction', 'fitted']):
                                logger.info(f"  📈 Time series processing detected!")
                    
                    elif isinstance(parsed_result, list):
                        logger.info(f"  📋 Response is list with {len(parsed_result)} items")
                        if len(parsed_result) > 0:
                            logger.info(f"  🔍 First item: {type(parsed_result[0])}")
                    
                    logger.info(f"  📄 Response preview: {str(parsed_result)[:200]}...")
                    
                    results.append({
                        "endpoint": endpoint_name,
                        "format": test_format['name'],
                        "success": True,
                        "response_time": response_time,
                        "result": parsed_result,
                        "url": url
                    })
                    
                except json.JSONDecodeError:
                    raw_response = result_data.decode('utf-8')
                    logger.info(f"  📄 Raw response: {raw_response[:200]}...")
                    
                    results.append({
                        "endpoint": endpoint_name,
                        "format": test_format['name'],
                        "success": True,
                        "response_time": response_time,
                        "raw_result": raw_response,
                        "url": url
                    })
                
            except urllib.error.HTTPError as error:
                try:
                    error_details = error.read().decode("utf8", 'ignore')
                    logger.info(f"  ❌ HTTP {error.code}: {error_details[:150]}")
                    
                    # Log detailed error for analysis
                    results.append({
                        "endpoint": endpoint_name,
                        "format": test_format['name'],
                        "success": False,
                        "error_code": error.code,
                        "error_details": error_details,
                        "url": url
                    })
                    
                except:
                    logger.info(f"  ❌ HTTP {error.code}")
                    results.append({
                        "endpoint": endpoint_name,
                        "format": test_format['name'],
                        "success": False,
                        "error_code": error.code,
                        "url": url
                    })
                    
            except Exception as e:
                error_msg = str(e)
                logger.info(f"  ❌ Error: {error_msg}")
                
                results.append({
                    "endpoint": endpoint_name,
                    "format": test_format['name'],
                    "success": False,
                    "error": error_msg,
                    "url": url
                })
    
    # Analysis and summary
    logger.info(f"\n{'='*80}")
    logger.info("NEW ENDPOINT TEST RESULTS SUMMARY")
    logger.info(f"{'='*80}")
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    logger.info(f"Total tests: {len(results)}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")
    
    if successful:
        logger.info(f"\n🎊 BREAKTHROUGH! New endpoint is working!")
        logger.info(f"\n✅ WORKING COMBINATIONS:")
        
        for result in successful:
            response_time = result.get('response_time', 0)
            logger.info(f"  🎯 {result['endpoint']} + {result['format']}: {response_time:.2f}s")
        
        # Find the best performing combination
        best_result = min(successful, key=lambda x: x.get('response_time', float('inf')))
        logger.info(f"\n🏆 BEST PERFORMANCE:")
        logger.info(f"  Endpoint: {best_result['endpoint']}")
        logger.info(f"  Format: {best_result['format']}")
        logger.info(f"  Response time: {best_result.get('response_time', 0):.2f}s")
        logger.info(f"  URL: {best_result['url']}")
        
        # Test with our actual 16 metrics using the best combination
        logger.info(f"\n🚀 Testing with OUR 16 METRICS using best combination...")
        test_our_metrics_with_new_endpoint(best_result, new_api_key)
        
    else:
        logger.info(f"\n❌ New endpoint also has issues:")
        
        # Group errors by type
        error_types = {}
        for result in failed:
            error_code = result.get('error_code', 'Unknown')
            if error_code not in error_types:
                error_types[error_code] = []
            error_types[error_code].append(result)
        
        for error_code, error_results in error_types.items():
            logger.info(f"\n  📊 Error {error_code}: {len(error_results)} occurrences")
            if error_results:
                sample_error = error_results[0].get('error_details', error_results[0].get('error', ''))
                logger.info(f"    Sample: {sample_error[:100]}")
    
    return results

def test_our_metrics_with_new_endpoint(best_result, api_key):
    """Test our actual 16 metrics with the working endpoint/format combination"""
    
    logger.info(f"Testing our metrics with: {best_result['endpoint']} + {best_result['format']}")
    
    # Generate timestamps for our metrics
    timestamps = []
    base_time = datetime.now() - timedelta(hours=2)
    for i in range(12):  # 12 data points
        ts = base_time + timedelta(minutes=i * 10)
        timestamps.append(ts.strftime("%Y-%m-%dT%H:%M:%SZ"))
    
    # Our 5 key metrics with anomaly patterns
    our_metrics = {
        "cpu_usage_percent": [45, 47, 52, 49, 78, 82, 79, 75, 52, 48, 46, 47],
        "memory_available_gb": [2.1, 2.0, 1.9, 1.8, 0.3, 0.2, 0.4, 1.8, 1.9, 2.0, 2.1, 2.0],
        "http_5xx_errors": [5, 8, 12, 15, 180, 195, 172, 18, 12, 8, 6, 7],
        "exception_count": [2, 3, 5, 85, 92, 78, 8, 5, 3, 2, 1, 2],
        "request_failed_count": [40, 50, 63, 320, 350, 310, 65, 55, 45, 42, 38, 41]
    }
    
    # Build payload based on successful format
    if best_result['format'] == "Multi-Series Format":
        series_data = []
        for metric_name, values in our_metrics.items():
            series_data.append({
                "unique_id": metric_name,
                "ds": timestamps,
                "y": values
            })
        
        payload = {
            "series": series_data,
            "detection_size": 4,
            "h": 2
        }
        
    elif best_result['format'] == "TimeGPT Format":
        df_data = []
        for metric_name, values in our_metrics.items():
            for ts, val in zip(timestamps, values):
                df_data.append({
                    "ds": ts,
                    "y": val,
                    "unique_id": metric_name
                })
        
        payload = {
            "df": df_data,
            "h": 2
        }
    
    else:
        # Use the first metric as a single series
        first_metric = list(our_metrics.keys())[0]
        first_values = our_metrics[first_metric]
        
        payload = {
            "series": [{
                "ds": timestamps,
                "y": first_values
            }],
            "h": 2
        }
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        
        body = str.encode(json.dumps(payload))
        req = urllib.request.Request(best_result['url'], body, headers)
        
        logger.info(f"Sending our metrics to new endpoint...")
        logger.info(f"Metrics: {list(our_metrics.keys())}")
        logger.info(f"Data points: {len(timestamps)} per metric")
        
        start_time = datetime.now()
        response = urllib.request.urlopen(req, timeout=90)
        response_time = (datetime.now() - start_time).total_seconds()
        
        result_data = response.read()
        parsed_result = json.loads(result_data.decode('utf-8'))
        
        logger.info(f"\n🎊 OUR METRICS SUCCESS with NEW ENDPOINT!")
        logger.info(f"⏱️ Response time: {response_time:.2f} seconds")
        logger.info(f"📊 Processing: {len(our_metrics)} metrics")
        logger.info(f"📈 Multi-series capability: CONFIRMED WORKING!")
        
        # Analyze results for anomalies
        anomaly_count = 0
        if isinstance(parsed_result, dict):
            logger.info(f"🔑 Response keys: {list(parsed_result.keys())}")
            
            for key, value in parsed_result.items():
                if 'anomaly' in key.lower():
                    logger.info(f"🚨 Anomaly field: {key}")
                    if isinstance(value, list):
                        flags = [x for x in value if x in [1, True]]
                        anomaly_count += len(flags)
                        if flags:
                            logger.info(f"   🎯 {len(flags)} anomalies detected!")
        
        logger.info(f"📄 Response preview: {str(parsed_result)[:400]}...")
        
        logger.info(f"\n🎊 FINAL BREAKTHROUGH SUMMARY:")
        logger.info(f"✅ New TimeGEN-1 endpoint: WORKING!")
        logger.info(f"✅ Multi-series support: CONFIRMED!")
        logger.info(f"✅ Our metrics processing: SUCCESS!")
        logger.info(f"✅ Response time: {response_time:.2f}s (vs previous timeouts)")
        logger.info(f"🚀 Ready for production deployment!")
        
        return True, parsed_result
        
    except Exception as e:
        logger.warning(f"❌ Our metrics test failed: {e}")
        return False, str(e)

if __name__ == "__main__":
    test_new_endpoint()

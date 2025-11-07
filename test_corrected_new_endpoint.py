"""
Analyze NEW endpoint errors and create corrected payload formats
Based on 422 errors from new endpoint: https://TimeGEN-1-zeolh.eastus2.models.ai.azure.com
"""
import urllib.request
import json
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_and_test_corrected_formats():
    """Analyze the 422 errors and test corrected payload formats"""
    
    logger.info("🔍 Analyzing 422 Errors from New Endpoint")
    logger.info("Error 1: 'series' should be a valid dictionary or object")
    logger.info("Error 2: Missing required fields: 'series', 'freq'")
    logger.info("Error 3: Model 'timegpt-1' is not supported")
    
    logger.info("\nCreating corrected formats based on error analysis...")
    
    new_api_key = "mDPTRBXlnpbNbbXdgWxUkDPEVLtq0cKT"
    
    # Generate timestamps
    timestamps = []
    base_time = datetime.now() - timedelta(hours=1)
    for i in range(6):  # Small dataset for quick testing
        ts = base_time + timedelta(minutes=i * 15)
        timestamps.append(ts.strftime("%Y-%m-%dT%H:%M:%SZ"))
    
    # Test values with clear anomaly
    test_values = [10, 12, 15, 85, 18, 14]  # Anomaly spike at index 3
    
    # Corrected formats based on error analysis
    corrected_formats = [
        # Format 1: Series as dictionary (not array) + freq
        {
            "name": "Series as Dictionary + Freq",
            "data": {
                "series": {
                    "ds": timestamps,
                    "y": test_values,
                    "unique_id": "test_metric"
                },
                "freq": "15min",
                "h": 2
            }
        },
        
        # Format 2: Series with freq field
        {
            "name": "Series Array + Freq",
            "data": {
                "series": [{
                    "unique_id": "cpu_usage",
                    "ds": timestamps,
                    "y": test_values
                }],
                "freq": "15T",  # 15 minutes in pandas format
                "h": 2
            }
        },
        
        # Format 3: Standard TimeGPT format with freq
        {
            "name": "TimeGPT + Freq",
            "data": {
                "df": [{"ds": ts, "y": val} for ts, val in zip(timestamps, test_values)],
                "freq": "15min",
                "h": 2
            }
        },
        
        # Format 4: Series object format
        {
            "name": "Series Object Format",
            "data": {
                "series": {
                    "timestamps": timestamps,
                    "values": test_values,
                    "metric_name": "test_cpu"
                },
                "freq": "15min",
                "detection_size": 3,
                "h": 1
            }
        },
        
        # Format 5: Minimal format with required fields only
        {
            "name": "Minimal Required Fields",
            "data": {
                "series": {
                    "y": test_values,
                    "ds": timestamps
                },
                "freq": "15T"
            }
        },
        
        # Format 6: Dictionary format for series data
        {
            "name": "Dictionary Series Data",
            "data": {
                "series": {
                    timestamp: value for timestamp, value in zip(timestamps, test_values)
                },
                "freq": "15min",
                "h": 1
            }
        }
    ]
    
    # Test endpoints that returned 422 (these exist but need correct format)
    working_endpoints = [
        ("v2/online_anomaly_detection", "https://TimeGEN-1-zeolh.eastus2.models.ai.azure.com/v2/online_anomaly_detection"),
        ("anomaly_detection_multi_series", "https://TimeGEN-1-zeolh.eastus2.models.ai.azure.com/anomaly_detection_multi_series"),
        ("forecast", "https://TimeGEN-1-zeolh.eastus2.models.ai.azure.com/forecast")
    ]
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {new_api_key}'
    }
    
    results = []
    
    for endpoint_name, url in working_endpoints:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing Endpoint: {endpoint_name}")
        logger.info(f"URL: {url}")
        
        for format_test in corrected_formats:
            logger.info(f"\n  📋 Testing: {format_test['name']}")
            
            try:
                body = str.encode(json.dumps(format_test['data']))
                logger.info(f"  📦 Payload size: {len(body)} bytes")
                
                req = urllib.request.Request(url, body, headers)
                
                start_time = datetime.now()
                response = urllib.request.urlopen(req, timeout=45)  # 45 second timeout
                response_time = (datetime.now() - start_time).total_seconds()
                
                result_data = response.read()
                
                logger.info(f"  🎉 SUCCESS!")
                logger.info(f"  ⏱️ Response time: {response_time:.2f} seconds")
                logger.info(f"  📊 Response size: {len(result_data)} bytes")
                
                # Parse response
                try:
                    parsed_result = json.loads(result_data.decode('utf-8'))
                    logger.info(f"  🔑 Response type: {type(parsed_result)}")
                    
                    if isinstance(parsed_result, dict):
                        logger.info(f"  📋 Keys: {list(parsed_result.keys())}")
                        
                        # Look for anomaly detection results
                        anomaly_keywords = ['anomaly', 'outlier', 'abnormal', 'detection']
                        for key in parsed_result.keys():
                            if any(keyword in key.lower() for keyword in anomaly_keywords):
                                logger.info(f"  🚨 Anomaly field found: {key}")
                                value = parsed_result[key]
                                if isinstance(value, list):
                                    anomaly_flags = [x for x in value if x in [1, True]]
                                    if anomaly_flags:
                                        logger.info(f"  🎯 {len(anomaly_flags)} anomalies detected!")
                        
                        # Look for forecast results
                        forecast_keywords = ['forecast', 'prediction', 'fitted', 'yhat']
                        for key in parsed_result.keys():
                            if any(keyword in key.lower() for keyword in forecast_keywords):
                                logger.info(f"  📈 Forecast field found: {key}")
                    
                    elif isinstance(parsed_result, list):
                        logger.info(f"  📋 List with {len(parsed_result)} items")
                        if parsed_result:
                            logger.info(f"  🔍 First item type: {type(parsed_result[0])}")
                    
                    logger.info(f"  📄 Preview: {str(parsed_result)[:300]}...")
                    
                    results.append({
                        "endpoint": endpoint_name,
                        "format": format_test['name'],
                        "success": True,
                        "response_time": response_time,
                        "result": parsed_result,
                        "url": url,
                        "payload": format_test['data']
                    })
                    
                    # If this is working, test with multi-series immediately
                    logger.info(f"  🚀 SUCCESS! Testing multi-series with this format...")
                    test_multi_series_with_working_format(format_test, url, new_api_key)
                    
                except json.JSONDecodeError:
                    raw_response = result_data.decode('utf-8')
                    logger.info(f"  📄 Raw response: {raw_response[:300]}")
                    
                    results.append({
                        "endpoint": endpoint_name,
                        "format": format_test['name'],
                        "success": True,
                        "response_time": response_time,
                        "raw_result": raw_response,
                        "url": url
                    })
                
            except urllib.error.HTTPError as error:
                try:
                    error_details = error.read().decode("utf8", 'ignore')
                    
                    # Only log if it's a new/different error
                    if error.code != 422 or "Model 'timegpt-1' is not supported" not in error_details:
                        logger.info(f"  ❌ HTTP {error.code}: {error_details[:200]}")
                    else:
                        logger.info(f"  ❌ Same timegpt-1 model error")
                    
                    results.append({
                        "endpoint": endpoint_name,
                        "format": format_test['name'],
                        "success": False,
                        "error_code": error.code,
                        "error_details": error_details,
                        "url": url
                    })
                    
                except:
                    logger.info(f"  ❌ HTTP {error.code}")
                    
            except Exception as e:
                error_msg = str(e)
                
                # Don't log timeout errors as loudly since we expect some
                if "timed out" in error_msg.lower():
                    logger.info(f"  ⏱️ Timeout: {format_test['name']}")
                else:
                    logger.info(f"  ❌ Error: {error_msg[:150]}")
                
                results.append({
                    "endpoint": endpoint_name,
                    "format": format_test['name'],
                    "success": False,
                    "error": error_msg,
                    "url": url
                })
    
    # Final summary
    logger.info(f"\n{'='*70}")
    logger.info("CORRECTED FORMAT TEST RESULTS")
    logger.info(f"{'='*70}")
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    logger.info(f"Total corrected format tests: {len(results)}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")
    
    if successful:
        logger.info(f"\n🎊 BREAKTHROUGH! Found working format for new endpoint!")
        
        for result in successful:
            logger.info(f"  ✅ {result['endpoint']} + {result['format']}: {result.get('response_time', 0):.2f}s")
        
        # Best result
        best = min(successful, key=lambda x: x.get('response_time', float('inf')))
        logger.info(f"\n🏆 BEST COMBINATION:")
        logger.info(f"  Endpoint: {best['endpoint']}")
        logger.info(f"  Format: {best['format']}")
        logger.info(f"  URL: {best['url']}")
        logger.info(f"  Time: {best.get('response_time', 0):.2f}s")
        
        # Show the working payload structure
        logger.info(f"\n📋 WORKING PAYLOAD STRUCTURE:")
        logger.info(f"{json.dumps(best['payload'], indent=2)}")
        
    else:
        logger.info(f"\n❌ Still searching for correct format")
        
        # Analyze error patterns
        timeout_errors = [r for r in failed if 'error' in r and 'timeout' in r.get('error', '').lower()]
        model_errors = [r for r in failed if 'error_details' in r and 'timegpt-1' in r.get('error_details', '')]
        format_errors = [r for r in failed if r.get('error_code') == 422 and 'timegpt-1' not in r.get('error_details', '')]
        
        logger.info(f"  📊 Timeout errors: {len(timeout_errors)}")
        logger.info(f"  📊 Model not supported: {len(model_errors)}")
        logger.info(f"  📊 Format errors: {len(format_errors)}")
        
        if format_errors:
            logger.info(f"\n  🔍 Format error sample:")
            sample = format_errors[0]
            logger.info(f"    {sample.get('error_details', 'No details')[:200]}")
    
    return results

def test_multi_series_with_working_format(working_format, working_url, api_key):
    """Test our actual metrics with the working format"""
    
    logger.info(f"\n  🚀 TESTING MULTI-SERIES with working format")
    
    # Generate our metrics data
    timestamps = []
    base_time = datetime.now() - timedelta(hours=1)
    for i in range(8):
        ts = base_time + timedelta(minutes=i * 10)
        timestamps.append(ts.strftime("%Y-%m-%dT%H:%M:%SZ"))
    
    our_metrics = {
        "cpu_usage": [45, 47, 52, 78, 75, 52, 48, 46],
        "memory_gb": [2.1, 2.0, 1.9, 0.3, 0.4, 1.8, 1.9, 2.0],
        "http_5xx": [5, 8, 12, 180, 172, 18, 12, 8]
    }
    
    # Adapt the working format for our multi-series data
    if "Dictionary" in working_format['name']:
        # Dictionary format for each metric
        multi_payload = {
            "series": {
                metric_name: {ts: val for ts, val in zip(timestamps, values)}
                for metric_name, values in our_metrics.items()
            },
            "freq": "10min",
            "h": 2
        }
    elif "Series Object" in working_format['name']:
        # Object format adaptation
        multi_payload = {
            "series": [
                {
                    "timestamps": timestamps,
                    "values": values,
                    "metric_name": metric_name
                }
                for metric_name, values in our_metrics.items()
            ],
            "freq": "10min",
            "h": 2
        }
    else:
        # Default to array format
        multi_payload = {
            "series": [
                {
                    "unique_id": metric_name,
                    "ds": timestamps,
                    "y": values
                }
                for metric_name, values in our_metrics.items()
            ],
            "freq": "10min",
            "h": 2
        }
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        
        body = str.encode(json.dumps(multi_payload))
        req = urllib.request.Request(working_url, body, headers)
        
        logger.info(f"    📊 Testing {len(our_metrics)} metrics")
        
        start_time = datetime.now()
        response = urllib.request.urlopen(req, timeout=60)
        response_time = (datetime.now() - start_time).total_seconds()
        
        result_data = response.read()
        parsed_result = json.loads(result_data.decode('utf-8'))
        
        logger.info(f"    🎊 MULTI-SERIES SUCCESS!")
        logger.info(f"    ⏱️ Time: {response_time:.2f}s")
        logger.info(f"    📈 Metrics: {list(our_metrics.keys())}")
        logger.info(f"    📄 Preview: {str(parsed_result)[:200]}...")
        
        return True, parsed_result
        
    except Exception as e:
        logger.info(f"    ❌ Multi-series failed: {str(e)[:100]}")
        return False, str(e)

if __name__ == "__main__":
    analyze_and_test_corrected_formats()

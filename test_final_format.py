"""
Final attempt with EXACT required fields based on detailed error analysis
New endpoint requires: series.y, series.sizes, detection_size, h, freq
"""
import urllib.request
import json
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_final_correct_format():
    """Test with the EXACT format based on detailed error messages"""
    
    logger.info("🎯 Final Correct Format Test")
    logger.info("Required fields identified from errors:")
    logger.info("- series.y (required)")
    logger.info("- series.sizes (required)")
    logger.info("- detection_size (required)")
    logger.info("- h (required)")
    logger.info("- freq (required)")
    
    new_api_key = "mDPTRBXlnpbNbbXdgWxUkDPEVLtq0cKT"
    
    # Generate test data
    timestamps = []
    base_time = datetime.now() - timedelta(hours=1)
    for i in range(8):
        ts = base_time + timedelta(minutes=i * 10)
        timestamps.append(ts.strftime("%Y-%m-%dT%H:%M:%SZ"))
    
    test_values = [10, 12, 15, 85, 18, 14, 11, 13]  # Clear anomaly at index 3
    
    # Final corrected formats with ALL required fields
    final_formats = [
        # Format 1: Complete series object with all required fields
        {
            "name": "Complete Series Object",
            "data": {
                "series": {
                    "y": test_values,
                    "sizes": [len(test_values)],  # Array of series sizes
                    "ds": timestamps
                },
                "detection_size": 4,
                "h": 2,
                "freq": "10min"
            }
        },
        
        # Format 2: Series with individual metric sizes
        {
            "name": "Series with Metric Sizes",
            "data": {
                "series": {
                    "y": test_values,
                    "sizes": [1],  # Single series size
                    "timestamps": timestamps
                },
                "detection_size": 3,
                "h": 1,
                "freq": "10T"
            }
        },
        
        # Format 3: Multi-series format with sizes array
        {
            "name": "Multi-Series with Sizes",
            "data": {
                "series": {
                    "y": test_values + [20, 22, 25, 95, 28, 24, 21, 23],  # 2 series concatenated
                    "sizes": [8, 8],  # Two series of 8 points each
                    "ds": timestamps + timestamps  # Timestamps for both series
                },
                "detection_size": 3,
                "h": 2,
                "freq": "10min"
            }
        },
        
        # Format 4: Single series with proper structure
        {
            "name": "Single Series Proper",
            "data": {
                "series": {
                    "y": test_values,
                    "sizes": [len(test_values)],
                    "ds": timestamps,
                    "unique_id": ["cpu_usage"]
                },
                "detection_size": 4,
                "h": 2,
                "freq": "600S"  # 600 seconds = 10 minutes
            }
        },
        
        # Format 5: Minimal working format
        {
            "name": "Minimal Working",
            "data": {
                "series": {
                    "y": test_values,
                    "sizes": [len(test_values)]
                },
                "detection_size": 3,
                "h": 1,
                "freq": "10min"
            }
        }
    ]
    
    # Test the v2 endpoint that gave us the detailed errors
    test_url = "https://TimeGEN-1-zeolh.eastus2.models.ai.azure.com/v2/online_anomaly_detection"
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {new_api_key}'
    }
    
    results = []
    
    for format_test in final_formats:
        logger.info(f"\n{'='*50}")
        logger.info(f"Testing: {format_test['name']}")
        
        try:
            body = str.encode(json.dumps(format_test['data']))
            logger.info(f"📦 Payload size: {len(body)} bytes")
            logger.info(f"🔍 y values: {len(format_test['data']['series']['y'])}")
            logger.info(f"🔍 sizes: {format_test['data']['series']['sizes']}")
            logger.info(f"🔍 detection_size: {format_test['data']['detection_size']}")
            logger.info(f"🔍 h: {format_test['data']['h']}")
            logger.info(f"🔍 freq: {format_test['data']['freq']}")
            
            req = urllib.request.Request(test_url, body, headers)
            
            start_time = datetime.now()
            response = urllib.request.urlopen(req, timeout=60)
            response_time = (datetime.now() - start_time).total_seconds()
            
            result_data = response.read()
            
            logger.info(f"🎉 SUCCESS!")
            logger.info(f"⏱️ Response time: {response_time:.2f} seconds")
            logger.info(f"📊 Response size: {len(result_data)} bytes")
            logger.info(f"📈 Status: {response.getcode()}")
            
            # Parse response
            try:
                parsed_result = json.loads(result_data.decode('utf-8'))
                
                logger.info(f"🔑 Response type: {type(parsed_result)}")
                
                if isinstance(parsed_result, dict):
                    logger.info(f"📋 Keys: {list(parsed_result.keys())}")
                    
                    # Check for anomaly detection results
                    anomaly_found = False
                    forecast_found = False
                    
                    for key, value in parsed_result.items():
                        key_lower = key.lower()
                        
                        if 'anomaly' in key_lower or 'outlier' in key_lower:
                            logger.info(f"🚨 Anomaly field: {key}")
                            anomaly_found = True
                            if isinstance(value, list):
                                anomaly_count = sum(1 for x in value if x in [1, True, '1', 'true'])
                                if anomaly_count > 0:
                                    logger.info(f"🎯 {anomaly_count} anomalies detected!")
                        
                        elif 'forecast' in key_lower or 'prediction' in key_lower or 'yhat' in key_lower:
                            logger.info(f"📈 Forecast field: {key}")
                            forecast_found = True
                            if isinstance(value, list) and len(value) > 0:
                                logger.info(f"📊 {len(value)} forecast points")
                    
                    if anomaly_found or forecast_found:
                        logger.info(f"✅ TimeGEN-1 processing confirmed!")
                    
                elif isinstance(parsed_result, list):
                    logger.info(f"📋 List response with {len(parsed_result)} items")
                    if parsed_result:
                        logger.info(f"🔍 First item: {type(parsed_result[0])}")
                        if isinstance(parsed_result[0], dict):
                            logger.info(f"📋 First item keys: {list(parsed_result[0].keys())}")
                
                logger.info(f"📄 Response preview: {str(parsed_result)[:500]}...")
                
                # SUCCESS! Now test with our multi-series data
                logger.info(f"\n🚀 SUCCESS! Testing OUR METRICS with this format...")
                success = test_our_metrics_final(format_test, test_url, new_api_key)
                
                results.append({
                    "format": format_test['name'],
                    "success": True,
                    "response_time": response_time,
                    "result": parsed_result,
                    "multi_series_success": success
                })
                
            except json.JSONDecodeError:
                raw_response = result_data.decode('utf-8')
                logger.info(f"📄 Raw response: {raw_response[:500]}")
                
                results.append({
                    "format": format_test['name'],
                    "success": True,
                    "response_time": response_time,
                    "raw_result": raw_response
                })
            
        except urllib.error.HTTPError as error:
            try:
                error_details = error.read().decode("utf8", 'ignore')
                logger.warning(f"❌ HTTP {error.code}")
                logger.warning(f"Details: {error_details}")
                
                results.append({
                    "format": format_test['name'],
                    "success": False,
                    "error_code": error.code,
                    "error_details": error_details
                })
                
            except:
                logger.warning(f"❌ HTTP {error.code}")
                
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"❌ Error: {error_msg}")
            
            results.append({
                "format": format_test['name'],
                "success": False,
                "error": error_msg
            })
    
    # Final results
    logger.info(f"\n{'='*60}")
    logger.info("FINAL FORMAT TEST RESULTS")
    logger.info(f"{'='*60}")
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    logger.info(f"Total formats tested: {len(results)}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")
    
    if successful:
        logger.info(f"\n🎊 FINAL BREAKTHROUGH!")
        logger.info(f"Found working format for NEW TimeGEN-1 endpoint!")
        
        for result in successful:
            multi_status = "✅" if result.get("multi_series_success", False) else "❓"
            logger.info(f"  {multi_status} {result['format']}: {result.get('response_time', 0):.2f}s")
        
        best = min(successful, key=lambda x: x.get('response_time', float('inf')))
        logger.info(f"\n🏆 BEST FORMAT: {best['format']}")
        logger.info(f"⏱️ Response time: {best.get('response_time', 0):.2f}s")
        logger.info(f"🎯 Ready for production!")
        
    else:
        logger.info(f"\n❌ Need to continue investigating format requirements")
        if failed:
            logger.info(f"Latest error: {failed[-1].get('error_details', failed[-1].get('error', 'Unknown'))[:200]}")
    
    return results

def test_our_metrics_final(working_format, working_url, api_key):
    """Test our actual 16 metrics using the working format"""
    
    logger.info(f"  🚀 Testing OUR 5 KEY METRICS")
    
    # Our metrics with anomaly patterns
    timestamps = []
    base_time = datetime.now() - timedelta(hours=1)
    for i in range(10):
        ts = base_time + timedelta(minutes=i * 6)
        timestamps.append(ts.strftime("%Y-%m-%dT%H:%M:%SZ"))
    
    our_metrics = {
        "cpu_usage_percent": [45, 47, 52, 78, 82, 52, 48, 46, 44, 45],
        "memory_available_gb": [2.1, 2.0, 1.9, 0.3, 0.2, 1.8, 1.9, 2.0, 2.1, 2.0],
        "http_5xx_errors": [5, 8, 12, 180, 195, 18, 12, 8, 6, 7],
        "exception_count": [2, 3, 85, 92, 78, 8, 5, 3, 2, 1],
        "request_failed": [40, 50, 320, 350, 310, 65, 55, 45, 42, 40]
    }
    
    # Build multi-series payload using working format structure
    all_values = []
    all_timestamps = []
    sizes = []
    
    for metric_name, values in our_metrics.items():
        all_values.extend(values)
        all_timestamps.extend(timestamps)
        sizes.append(len(values))
    
    multi_payload = {
        "series": {
            "y": all_values,
            "sizes": sizes,
            "ds": all_timestamps
        },
        "detection_size": 4,
        "h": 2,
        "freq": "6min"
    }
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        
        body = str.encode(json.dumps(multi_payload))
        req = urllib.request.Request(working_url, body, headers)
        
        logger.info(f"    📊 Sending {len(our_metrics)} metrics ({sum(sizes)} total points)")
        logger.info(f"    📋 Metrics: {list(our_metrics.keys())}")
        
        start_time = datetime.now()
        response = urllib.request.urlopen(req, timeout=90)
        response_time = (datetime.now() - start_time).total_seconds()
        
        result_data = response.read()
        parsed_result = json.loads(result_data.decode('utf-8'))
        
        logger.info(f"    🎊 MULTI-SERIES SUCCESS!")
        logger.info(f"    ⏱️ Response time: {response_time:.2f}s")
        logger.info(f"    📈 All 5 metrics processed successfully!")
        logger.info(f"    🎯 TimeGEN-1 multi-series: WORKING!")
        
        # Look for anomalies in our data
        total_anomalies = 0
        if isinstance(parsed_result, dict):
            for key, value in parsed_result.items():
                if 'anomaly' in key.lower() and isinstance(value, list):
                    anomaly_count = sum(1 for x in value if x in [1, True])
                    total_anomalies += anomaly_count
        
        logger.info(f"    🚨 Anomalies detected: {total_anomalies}")
        logger.info(f"    📄 Preview: {str(parsed_result)[:300]}...")
        
        return True
        
    except Exception as e:
        logger.warning(f"    ❌ Multi-series test failed: {str(e)[:150]}")
        return False

if __name__ == "__main__":
    test_final_correct_format()

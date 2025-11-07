"""
Test with the CORRECT payload format based on API error analysis
The official Azure sample is incorrect - using actual endpoint requirements
"""
import urllib.request
import json
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_correct_payload_format():
    """Test with the correct payload format based on error analysis"""
    
    logger.info("Testing CORRECT payload format based on API errors")
    
    # Generate time series data in correct format
    timestamps = []
    base_time = datetime.now() - timedelta(hours=2)
    for i in range(20):  # 20 data points
        ts = base_time + timedelta(minutes=i * 5)
        timestamps.append(ts.strftime("%Y-%m-%dT%H:%M:%SZ"))
    
    # Create series data with anomaly patterns
    series_data = []
    
    # Series 1: CPU Usage with anomaly spike
    cpu_values = [45.2, 47.1, 52.3, 48.9, 51.2, 46.8, 49.5, 48.1, 47.9, 73.1, 75.7, 78.2, 76.5, 74.8, 52.3, 48.7, 49.2, 47.8, 46.9, 48.5]
    series_data.append({
        "unique_id": "cpu_usage", 
        "ds": timestamps,
        "y": cpu_values
    })
    
    # Series 2: Memory Available (GB) with anomaly drop
    memory_values = [2.1, 2.0, 1.8, 1.9, 1.7, 2.0, 1.9, 1.8, 2.1, 1.2, 1.1, 0.9, 1.0, 0.8, 1.9, 2.0, 1.8, 1.9, 2.1, 2.0]
    series_data.append({
        "unique_id": "memory_available_gb",
        "ds": timestamps, 
        "y": memory_values
    })
    
    # Series 3: HTTP 5xx Errors with anomaly spike
    error_values = [5, 8, 12, 15, 18, 22, 19, 16, 14, 125, 138, 172, 179, 165, 18, 15, 12, 8, 10, 7]
    series_data.append({
        "unique_id": "http_5xx_errors",
        "ds": timestamps,
        "y": error_values
    })
    
    # Correct payload format based on error analysis
    correct_data = {
        "series": series_data,
        "detection_size": 5,  # Number of points to use for anomaly detection
        "h": 3  # Forecast horizon
    }
    
    logger.info(f"Testing with CORRECTED format:")
    logger.info(f"Series count: {len(series_data)}")
    logger.info(f"Data points per series: {len(timestamps)}")
    logger.info(f"Detection size: {correct_data['detection_size']}")
    logger.info(f"Forecast horizon: {correct_data['h']}")
    
    body = str.encode(json.dumps(correct_data))
    logger.info(f"Payload size: {len(body)} bytes")
    
    # Test the working endpoint
    url = 'https://TimeGEN-1-AssurantPoc.eastus2.models.ai.azure.com/v2/online_anomaly_detection'
    api_key = "n0swAKTILYJZgcfSQ1QesDuKvLp5j1Zy"
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json', 
        'Authorization': ('Bearer ' + api_key)
    }

    req = urllib.request.Request(url, body, headers)

    try:
        logger.info("Sending request with CORRECT format...")
        start_time = datetime.now()
        response = urllib.request.urlopen(req, timeout=120)
        response_time = (datetime.now() - start_time).total_seconds()
        
        result = response.read()
        
        logger.info(f"🎉 SUCCESS with correct format!")
        logger.info(f"Response time: {response_time:.2f} seconds")
        logger.info(f"Response size: {len(result)} bytes")
        logger.info(f"Status code: {response.getcode()}")
        
        # Parse and analyze response
        try:
            parsed_result = json.loads(result.decode('utf-8'))
            logger.info(f"Response type: {type(parsed_result)}")
            
            if isinstance(parsed_result, list):
                logger.info(f"Response is a list with {len(parsed_result)} items")
                for i, item in enumerate(parsed_result):
                    logger.info(f"Item {i}: {type(item)} - {list(item.keys()) if isinstance(item, dict) else str(item)[:100]}")
                    
            elif isinstance(parsed_result, dict):
                logger.info(f"Response keys: {list(parsed_result.keys())}")
                
                # Look for anomaly detection results
                anomaly_found = False
                for key, value in parsed_result.items():
                    if 'anomaly' in key.lower():
                        logger.info(f"🚨 Anomaly field found: {key}")
                        anomaly_found = True
                    elif isinstance(value, list) and len(value) > 0:
                        # Check for binary anomaly flags
                        if all(isinstance(x, (int, bool)) for x in value[:5]):
                            anomaly_count = sum(1 for x in value if x)
                            if anomaly_count > 0:
                                logger.info(f"🚨 {anomaly_count} anomalies detected in {key}")
                                anomaly_found = True
                
                if not anomaly_found:
                    logger.info("No obvious anomaly flags found, checking all fields...")
                    
            # Print response preview
            logger.info(f"Response preview: {str(parsed_result)[:500]}...")
            
            # Check for our injected anomalies
            logger.info(f"\n🔍 Anomaly Detection Analysis:")
            logger.info(f"Expected anomalies around timestamps 9-13 (high CPU, low memory, high errors)")
            
            return True, parsed_result
            
        except json.JSONDecodeError:
            logger.info(f"Raw response: {result.decode('utf-8')}")
            return True, result.decode('utf-8')
            
    except urllib.error.HTTPError as error:
        logger.warning(f"❌ HTTP Error: {error.code}")
        logger.warning(f"Error info: {error.info()}")
        
        error_details = ""
        try:
            error_details = error.read().decode("utf8", 'ignore')
            logger.warning(f"Error details: {error_details}")
        except:
            pass
            
        return False, {"error_code": error.code, "error_details": error_details}
        
    except Exception as e:
        logger.warning(f"❌ Exception: {str(e)}")
        return False, {"error": str(e)}

def test_multi_series_endpoint_corrected():
    """Test the multi-series endpoint with potential format corrections"""
    
    logger.info("\n" + "="*60)
    logger.info("Testing multi-series endpoint with corrected format")
    
    # Try different format variations for multi-series
    timestamps = []
    base_time = datetime.now() - timedelta(hours=1)
    for i in range(15):
        ts = base_time + timedelta(minutes=i * 5)
        timestamps.append(ts.strftime("%Y-%m-%dT%H:%M:%SZ"))
    
    # Format variation 1: Multiple series with individual timestamps
    multi_series_data_v1 = {
        "series": [
            {
                "unique_id": "cpu_usage",
                "ds": timestamps,
                "y": [45, 47, 52, 49, 51, 47, 73, 76, 78, 77, 52, 49, 48, 47, 46]
            },
            {
                "unique_id": "memory_gb", 
                "ds": timestamps,
                "y": [2.1, 2.0, 1.8, 1.9, 1.7, 2.0, 1.2, 1.1, 0.9, 1.0, 1.9, 2.0, 1.8, 1.9, 2.1]
            }
        ],
        "detection_size": 5,
        "h": 2
    }
    
    # Format variation 2: Dictionary format
    multi_series_data_v2 = {
        "data": {
            "cpu_usage": {ts: val for ts, val in zip(timestamps, [45, 47, 52, 49, 51, 47, 73, 76, 78, 77, 52, 49, 48, 47, 46])},
            "memory_gb": {ts: val for ts, val in zip(timestamps, [2.1, 2.0, 1.8, 1.9, 1.7, 2.0, 1.2, 1.1, 0.9, 1.0, 1.9, 2.0, 1.8, 1.9, 2.1])}
        },
        "detection_size": 5,
        "forecast_horizon": 2
    }
    
    # Test both variations
    variations = [
        ("Multi-series Format V1", multi_series_data_v1),
        ("Multi-series Format V2", multi_series_data_v2)
    ]
    
    url = 'https://TimeGEN-1-AssurantPoc.eastus2.models.ai.azure.com/anomaly_detection_multi_series'
    api_key = "n0swAKTILYJZgcfSQ1QesDuKvLp5j1Zy"
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': ('Bearer ' + api_key)
    }
    
    results = []
    
    for variation_name, data in variations:
        logger.info(f"\nTesting {variation_name}:")
        
        body = str.encode(json.dumps(data))
        req = urllib.request.Request(url, body, headers)
        
        try:
            start_time = datetime.now()
            response = urllib.request.urlopen(req, timeout=90)
            response_time = (datetime.now() - start_time).total_seconds()
            
            result = response.read()
            parsed_result = json.loads(result.decode('utf-8'))
            
            logger.info(f"✅ {variation_name} SUCCESS!")
            logger.info(f"Response time: {response_time:.2f}s")
            logger.info(f"Response preview: {str(parsed_result)[:200]}...")
            
            results.append({"variation": variation_name, "success": True, "result": parsed_result})
            
        except Exception as e:
            logger.warning(f"❌ {variation_name} failed: {str(e)[:200]}")
            results.append({"variation": variation_name, "success": False, "error": str(e)})
    
    return results

if __name__ == "__main__":
    # Test correct format for main endpoint
    success, result = test_correct_payload_format()
    
    if success:
        logger.info(f"\n🎊 BREAKTHROUGH: Found working format for v2/online_anomaly_detection!")
        
        # Test multi-series endpoint
        multi_results = test_multi_series_endpoint_corrected()
        
        working_multi = [r for r in multi_results if r["success"]]
        if working_multi:
            logger.info(f"\n🎊 DOUBLE BREAKTHROUGH: Multi-series endpoint also working!")
        else:
            logger.info(f"\nMulti-series still has issues, but main endpoint works!")
            
    else:
        logger.info(f"\n❌ Still need to find correct format")
        logger.info(f"Error details: {result}")

"""
Simplified test with minimal data to avoid timeouts
Testing multiple format variations with very small datasets
"""
import urllib.request
import json
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_minimal_working_format():
    """Test with minimal data to find working format without timeouts"""
    
    logger.info("Testing MINIMAL data formats to identify working pattern")
    
    # Very simple timestamp format
    simple_timestamps = [
        "2024-01-01T10:00:00Z",
        "2024-01-01T10:05:00Z", 
        "2024-01-01T10:10:00Z",
        "2024-01-01T10:15:00Z",
        "2024-01-01T10:20:00Z"
    ]
    
    # Multiple format variations to test
    format_variations = [
        # Format 1: Series array format
        {
            "name": "Series Array Format",
            "data": {
                "series": [
                    {
                        "unique_id": "metric1",
                        "ds": simple_timestamps,
                        "y": [10, 12, 15, 98, 14]  # Obvious anomaly at position 3
                    }
                ],
                "detection_size": 2,
                "h": 1
            }
        },
        
        # Format 2: Simplified series format
        {
            "name": "Simplified Format", 
            "data": {
                "series": [
                    {
                        "unique_id": "test_metric",
                        "ds": simple_timestamps,
                        "y": [1, 2, 3, 100, 4]  # Clear anomaly
                    }
                ],
                "h": 1
            }
        },
        
        # Format 3: Basic time series
        {
            "name": "Basic Time Series",
            "data": {
                "series": [
                    {
                        "ds": simple_timestamps,
                        "y": [5, 6, 7, 500, 8]  # Anomaly spike
                    }
                ]
            }
        },
        
        # Format 4: Dictionary timestamps
        {
            "name": "Dictionary Timestamps",
            "data": {
                "data": {
                    "2024-01-01T10:00:00Z": 10,
                    "2024-01-01T10:05:00Z": 11, 
                    "2024-01-01T10:10:00Z": 12,
                    "2024-01-01T10:15:00Z": 200,  # Anomaly
                    "2024-01-01T10:20:00Z": 13
                }
            }
        },
        
        # Format 5: Nixtla TimeGPT format
        {
            "name": "TimeGPT Format",
            "data": {
                "df": [
                    {"ds": "2024-01-01T10:00:00Z", "y": 10},
                    {"ds": "2024-01-01T10:05:00Z", "y": 11},
                    {"ds": "2024-01-01T10:10:00Z", "y": 12},
                    {"ds": "2024-01-01T10:15:00Z", "y": 300},  # Anomaly
                    {"ds": "2024-01-01T10:20:00Z", "y": 13}
                ],
                "h": 1
            }
        }
    ]
    
    url = 'https://TimeGEN-1-AssurantPoc.eastus2.models.ai.azure.com/v2/online_anomaly_detection'
    api_key = "n0swAKTILYJZgcfSQ1QesDuKvLp5j1Zy"
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': ('Bearer ' + api_key)
    }
    
    results = []
    
    for variation in format_variations:
        logger.info(f"\n{'='*50}")
        logger.info(f"Testing: {variation['name']}")
        logger.info(f"Data structure: {list(variation['data'].keys())}")
        
        body = str.encode(json.dumps(variation['data']))
        logger.info(f"Payload size: {len(body)} bytes (minimal)")
        
        req = urllib.request.Request(url, body, headers)
        
        try:
            logger.info("Sending minimal request...")
            start_time = datetime.now()
            
            # Short timeout for quick feedback
            response = urllib.request.urlopen(req, timeout=30)
            response_time = (datetime.now() - start_time).total_seconds()
            
            result = response.read()
            logger.info(f"🎉 {variation['name']} SUCCESS!")
            logger.info(f"Response time: {response_time:.2f}s")
            logger.info(f"Response size: {len(result)} bytes")
            
            # Parse response
            try:
                parsed_result = json.loads(result.decode('utf-8'))
                logger.info(f"Response type: {type(parsed_result)}")
                
                if isinstance(parsed_result, dict):
                    logger.info(f"Keys: {list(parsed_result.keys())}")
                elif isinstance(parsed_result, list):
                    logger.info(f"List length: {len(parsed_result)}")
                    if len(parsed_result) > 0:
                        logger.info(f"First item type: {type(parsed_result[0])}")
                        if isinstance(parsed_result[0], dict):
                            logger.info(f"First item keys: {list(parsed_result[0].keys())}")
                
                # Look for anomaly indicators
                result_str = str(parsed_result)
                if any(keyword in result_str.lower() for keyword in ['anomaly', 'outlier', 'flag']):
                    logger.info(f"🚨 Anomaly detection keywords found!")
                
                logger.info(f"Response preview: {str(parsed_result)[:300]}...")
                
                results.append({
                    "format": variation['name'],
                    "success": True,
                    "response_time": response_time,
                    "result": parsed_result
                })
                
            except json.JSONDecodeError:
                raw_response = result.decode('utf-8')
                logger.info(f"Raw response: {raw_response}")
                results.append({
                    "format": variation['name'],
                    "success": True,
                    "response_time": response_time,
                    "raw_result": raw_response
                })
                
        except urllib.error.HTTPError as error:
            try:
                error_details = error.read().decode("utf8", 'ignore')
                logger.warning(f"❌ HTTP {error.code}: {error_details[:200]}")
                
                results.append({
                    "format": variation['name'],
                    "success": False,
                    "error_code": error.code,
                    "error_details": error_details
                })
                
            except Exception as e:
                logger.warning(f"❌ HTTP {error.code}: {str(e)}")
                results.append({
                    "format": variation['name'],
                    "success": False,
                    "error_code": error.code,
                    "error": str(e)
                })
                
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"❌ {variation['name']} failed: {error_msg}")
            
            results.append({
                "format": variation['name'],
                "success": False,
                "error": error_msg
            })
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("MINIMAL FORMAT TEST RESULTS")
    logger.info(f"{'='*60}")
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    logger.info(f"Total formats tested: {len(results)}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")
    
    if successful:
        logger.info(f"\n✅ WORKING FORMATS:")
        for result in successful:
            response_time = result.get('response_time', 0)
            logger.info(f"  🎯 {result['format']}: {response_time:.2f}s")
            
        # Use the best working format for larger test
        best_format = min(successful, key=lambda x: x.get('response_time', float('inf')))
        logger.info(f"\n🏆 Best format: {best_format['format']} ({best_format.get('response_time', 0):.2f}s)")
        
        # Now test with our actual metrics using the working format
        if best_format['format'] == "Series Array Format":
            test_our_metrics_with_working_format()
        
    else:
        logger.info(f"\n❌ NO FORMATS WORKING")
        for result in failed:
            logger.info(f"  • {result['format']}: {result.get('error_details', result.get('error', 'Unknown'))[:100]}")
    
    return results

def test_our_metrics_with_working_format():
    """Test our actual metrics using the format that worked"""
    
    logger.info(f"\n🚀 Testing OUR METRICS with working format...")
    
    # Generate realistic timestamps for our data
    timestamps = []
    base_time = datetime.now() - timedelta(hours=1)
    for i in range(10):  # Keep it small to avoid timeout
        ts = base_time + timedelta(minutes=i * 6)
        timestamps.append(ts.strftime("%Y-%m-%dT%H:%M:%SZ"))
    
    # Our key metrics with clear anomaly patterns
    our_data = {
        "series": [
            {
                "unique_id": "cpu_usage",
                "ds": timestamps,
                "y": [45, 47, 52, 49, 51, 78, 82, 79, 52, 48]  # Spike in middle
            },
            {
                "unique_id": "memory_available_gb", 
                "ds": timestamps,
                "y": [2.1, 2.0, 1.9, 1.8, 0.3, 0.2, 0.4, 1.8, 1.9, 2.0]  # Drop in middle
            },
            {
                "unique_id": "http_5xx_errors",
                "ds": timestamps,
                "y": [5, 8, 12, 15, 180, 195, 172, 18, 12, 8]  # Spike in middle
            }
        ],
        "detection_size": 3,
        "h": 2
    }
    
    url = 'https://TimeGEN-1-AssurantPoc.eastus2.models.ai.azure.com/v2/online_anomaly_detection'
    api_key = "n0swAKTILYJZgcfSQ1QesDuKvLp5j1Zy"
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': ('Bearer ' + api_key)
    }
    
    body = str.encode(json.dumps(our_data))
    req = urllib.request.Request(url, body, headers)
    
    try:
        logger.info("Testing our 3 key metrics with working format...")
        start_time = datetime.now()
        response = urllib.request.urlopen(req, timeout=60)
        response_time = (datetime.now() - start_time).total_seconds()
        
        result = response.read()
        parsed_result = json.loads(result.decode('utf-8'))
        
        logger.info(f"🎉 OUR METRICS SUCCESS!")
        logger.info(f"Response time: {response_time:.2f}s")
        logger.info(f"Multi-series: 3 metrics processed")
        
        # Analyze results for our metrics
        anomaly_count = 0
        if isinstance(parsed_result, list):
            for i, item in enumerate(parsed_result):
                logger.info(f"Metric {i+1} result: {type(item)} - {str(item)[:100]}")
                
                # Look for anomaly flags
                if isinstance(item, dict):
                    for key, value in item.items():
                        if 'anomaly' in key.lower() and isinstance(value, list):
                            flags = [x for x in value if x == 1 or x == True]
                            if flags:
                                anomaly_count += len(flags)
                                logger.info(f"🚨 {len(flags)} anomalies detected in {key}")
        
        if anomaly_count > 0:
            logger.info(f"\n🎊 SUCCESS: Detected {anomaly_count} anomalies in our metrics!")
            logger.info(f"This confirms TimeGEN-1 multi-series capability is WORKING!")
        
        logger.info(f"Full response: {str(parsed_result)[:500]}...")
        return True, parsed_result
        
    except Exception as e:
        logger.warning(f"❌ Our metrics test failed: {e}")
        return False, str(e)

if __name__ == "__main__":
    test_minimal_working_format()

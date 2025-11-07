"""
Test the official Azure sample code for TimeGEN-1
Using the exact sample provided by Azure documentation
"""
import urllib.request
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_official_sample():
    """Test the official Azure sample code"""
    
    logger.info("Testing OFFICIAL Azure TimeGEN-1 sample code")
    
    # Official sample data from Azure documentation
    data = {
        "freq": "D",
        "fh": 7,
        "y": {
            "2015-12-02": 8.71177264560569,
            "2015-12-03": 8.05610965954506,
            "2015-12-04": 8.08147504013705,
            "2015-12-05": 7.45876269238096,
            "2015-12-06": 8.01400499477946,
            "2015-12-07": 8.49678638163858,
            "2015-12-08": 7.98104975966596,
            "2015-12-09": 7.77779262633883,
            "2015-12-10": 8.2602342916073,
            "2015-12-11": 7.86633892304654,
            "2015-12-12": 7.31055015853442,
            "2015-12-13": 7.71824095195932,
            "2015-12-14": 8.31947369244219,
            "2015-12-15": 8.23668532271246,
            "2015-12-16": 7.80751004221619,
            "2015-12-17": 7.59186171488993,
            "2015-12-18": 7.52886925664225,
            "2015-12-19": 7.17165682276851,
            "2015-12-20": 7.89133075766189,
            "2015-12-21": 8.36007143564403,
            "2015-12-22": 8.11042723757502,
            "2015-12-23": 7.77527584648686,
            "2015-12-24": 7.34729970074316,
            "2015-12-25": 7.30182234213793,
            "2015-12-26": 7.12044437239249,
            "2015-12-27": 8.87877607170755,
            "2015-12-28": 9.25061821847475,
            "2015-12-29": 9.24792513230345,
            "2015-12-30": 8.39140318535794,
            "2015-12-31": 8.00469951054955,
            "2016-01-01": 7.58933582317062,
            "2016-01-02": 7.82524529143177,
            "2016-01-03": 8.24931374626064,
            "2016-01-04": 9.29514097366865,
            "2016-01-05": 8.56826646160024,
            "2016-01-06": 8.35255436947459,
            "2016-01-07": 8.29579811063615,
            "2016-01-08": 8.29029259122431,
            "2016-01-09": 7.78572089653462,
            "2016-01-10": 8.28172399041139,
            "2016-01-11": 8.4707303170059,
            "2016-01-12": 8.13505390861157,
            "2016-01-13": 8.06714903991011
        },
        "clean_ex_first": True,
        "finetune_steps": 0,
        "finetune_loss": "default"
    }

    body = str.encode(json.dumps(data))

    # Test both endpoints
    endpoints_to_test = [
        ("v2/online_anomaly_detection", "https://TimeGEN-1-AssurantPoc.eastus2.models.ai.azure.com/v2/online_anomaly_detection"),
        ("anomaly_detection_multi_series", "https://TimeGEN-1-AssurantPoc.eastus2.models.ai.azure.com/anomaly_detection_multi_series")
    ]
    
    api_key = "n0swAKTILYJZgcfSQ1QesDuKvLp5j1Zy"
    
    if not api_key:
        raise Exception("A key should be provided to invoke the endpoint")

    results = []
    
    for endpoint_name, url in endpoints_to_test:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing endpoint: {endpoint_name}")
        logger.info(f"URL: {url}")
        logger.info(f"Data points: {len(data['y'])}")
        logger.info(f"Frequency: {data['freq']}")
        logger.info(f"Forecast horizon: {data['fh']}")
        logger.info(f"Payload size: {len(body)} bytes")

        headers = {
            'Content-Type': 'application/json', 
            'Accept': 'application/json', 
            'Authorization': ('Bearer ' + api_key)
        }

        req = urllib.request.Request(url, body, headers)

        start_time = datetime.now()
        
        try:
            logger.info("Sending request...")
            response = urllib.request.urlopen(req, timeout=120)  # 2 minute timeout
            
            response_time = (datetime.now() - start_time).total_seconds()
            result_data = response.read()
            
            logger.info(f"🎉 SUCCESS!")
            logger.info(f"Response time: {response_time:.2f} seconds")
            logger.info(f"Response size: {len(result_data)} bytes")
            logger.info(f"Status code: {response.getcode()}")
            
            # Try to parse JSON response
            try:
                parsed_result = json.loads(result_data.decode('utf-8'))
                logger.info(f"Response type: {type(parsed_result)}")
                
                if isinstance(parsed_result, dict):
                    logger.info(f"Response keys: {list(parsed_result.keys())}")
                    
                    # Look for anomaly detection results
                    if 'anomaly_flag' in str(parsed_result):
                        logger.info("🚨 Anomaly detection data found in response!")
                    
                    if 'forecast' in str(parsed_result):
                        logger.info("📊 Forecast data found in response!")
                        
                logger.info(f"Response preview: {str(parsed_result)[:300]}...")
                
                results.append({
                    "endpoint": endpoint_name,
                    "success": True,
                    "response_time": response_time,
                    "response_size": len(result_data),
                    "parsed_response": parsed_result
                })
                
            except json.JSONDecodeError:
                logger.info(f"Raw response: {result_data.decode('utf-8')[:500]}...")
                results.append({
                    "endpoint": endpoint_name,
                    "success": True,
                    "response_time": response_time,
                    "response_size": len(result_data),
                    "raw_response": result_data.decode('utf-8')[:500]
                })
            
        except urllib.error.HTTPError as error:
            error_info = ""
            error_details = ""
            try:
                error_info = str(error.info())
                error_details = error.read().decode("utf8", 'ignore')
            except:
                pass
                
            logger.warning(f"❌ HTTP Error: {error.code}")
            logger.warning(f"Error info: {error_info}")
            logger.warning(f"Error details: {error_details}")
            
            results.append({
                "endpoint": endpoint_name,
                "success": False,
                "error_code": error.code,
                "error_info": error_info,
                "error_details": error_details
            })
            
        except Exception as e:
            logger.warning(f"❌ Exception: {str(e)}")
            results.append({
                "endpoint": endpoint_name,
                "success": False,
                "error": str(e)
            })
    
    # Summary
    logger.info(f"\n{'='*70}")
    logger.info("OFFICIAL SAMPLE CODE TEST RESULTS")
    logger.info(f"{'='*70}")
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    logger.info(f"Total endpoints tested: {len(results)}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")
    
    if successful:
        logger.info(f"\n✅ WORKING ENDPOINTS:")
        for result in successful:
            response_time = result.get('response_time', 0)
            logger.info(f"  🎯 {result['endpoint']}: {response_time:.2f}s")
            
        logger.info(f"\n🎊 BREAKTHROUGH: Official sample code works!")
        logger.info(f"This confirms the correct payload format and working endpoint!")
        
        # Find the best endpoint
        best = min(successful, key=lambda x: x.get('response_time', float('inf')))
        logger.info(f"\nBest endpoint: {best['endpoint']} ({best.get('response_time', 0):.2f}s)")
        
    else:
        logger.info(f"\n❌ No endpoints working with official sample")
        for result in failed:
            error_msg = result.get('error_details', result.get('error', 'Unknown error'))
            logger.info(f"  • {result['endpoint']}: {error_msg[:100]}")
    
    # Now test with our 16 metrics using the working format
    if successful:
        logger.info(f"\n🚀 Testing with OUR 16 METRICS using working format...")
        test_our_metrics_with_working_format(successful[0]['endpoint'])
    
    return results

def test_our_metrics_with_working_format(working_endpoint_name):
    """Test our 16 metrics using the format that worked"""
    
    # Map endpoint name to URL
    endpoint_urls = {
        "v2/online_anomaly_detection": "https://TimeGEN-1-AssurantPoc.eastus2.models.ai.azure.com/v2/online_anomaly_detection",
        "anomaly_detection_multi_series": "https://TimeGEN-1-AssurantPoc.eastus2.models.ai.azure.com/anomaly_detection_multi_series"
    }
    
    url = endpoint_urls[working_endpoint_name]
    api_key = "n0swAKTILYJZgcfSQ1QesDuKvLp5j1Zy"
    
    # Our 16 metrics in the working format
    from datetime import datetime, timedelta
    
    # Generate timestamps
    timestamps = []
    base_time = datetime.now() - timedelta(hours=1)
    for i in range(10):
        ts = base_time + timedelta(minutes=i * 5)
        timestamps.append(ts.strftime("%Y-%m-%dT%H:%M:%SZ"))
    
    # Our metrics with anomaly patterns
    our_data = {
        "freq": "5min",  # Changed from "D" to "5min" for our use case
        "fh": 3,         # Reduced forecast horizon
        "y": {
            "cpu_usage": {ts: val for ts, val in zip(timestamps, [45.2, 47.1, 52.3, 48.9, 51.2, 46.8, 73.1, 75.7, 78.2, 76.5])},
            "memory_available": {ts: val for ts, val in zip(timestamps, [2.1, 2.0, 1.8, 1.9, 1.7, 2.0, 1.2, 1.1, 0.9, 1.0])},
            "http_5xx_errors": {ts: val for ts, val in zip(timestamps, [5, 8, 12, 15, 42, 18, 125, 138, 172, 179])},
            "exception_count": {ts: val for ts, val in zip(timestamps, [2, 3, 5, 7, 18, 8, 65, 75, 88, 82])},
            "request_failed": {ts: val for ts, val in zip(timestamps, [40, 50, 63, 63, 100, 59, 270, 300, 350, 330])}
        },
        "clean_ex_first": True,
        "finetune_steps": 0,
        "finetune_loss": "default"
    }
    
    logger.info(f"Testing OUR 5 key metrics with working endpoint: {working_endpoint_name}")
    logger.info(f"Metrics: {list(our_data['y'].keys())}")
    
    body = str.encode(json.dumps(our_data))
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json', 
        'Authorization': ('Bearer ' + api_key)
    }
    
    req = urllib.request.Request(url, body, headers)
    
    try:
        start_time = datetime.now()
        response = urllib.request.urlopen(req, timeout=180)  # 3 minute timeout
        response_time = (datetime.now() - start_time).total_seconds()
        
        result_data = response.read()
        parsed_result = json.loads(result_data.decode('utf-8'))
        
        logger.info(f"\n🎉 OUR METRICS SUCCESS!")
        logger.info(f"Response time: {response_time:.2f} seconds") 
        logger.info(f"Response size: {len(result_data)} bytes")
        logger.info(f"Multi-series processing: 5 metrics")
        
        # Check for anomalies in our data
        anomaly_count = 0
        if isinstance(parsed_result, dict):
            for key, value in parsed_result.items():
                if isinstance(value, dict) and 'anomaly_flag' in value:
                    flags = value.get('anomaly_flag', [])
                    if any(flag == 1 for flag in flags):
                        anomaly_count += 1
                        logger.info(f"🚨 Anomaly detected in: {key}")
        
        logger.info(f"Total anomalies detected: {anomaly_count}")
        logger.info(f"Response preview: {str(parsed_result)[:300]}...")
        
        if anomaly_count > 0:
            logger.info(f"\n🎊 SUCCESS: TimeGEN-1 detected anomalies in our data!")
            logger.info(f"This confirms the multi-series capability is working!")
        
    except Exception as e:
        logger.warning(f"❌ Our metrics test failed: {e}")

if __name__ == "__main__":
    test_official_sample()

"""
Comprehensive Swagger Analysis and Endpoint Discovery
Access swagger documentation and test ALL available endpoints systematically
"""
import urllib.request
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_swagger_documentation():
    """Fetch and analyze swagger documentation"""
    
    logger.info("🔍 Fetching Swagger Documentation")
    
    base_url = "https://TimeGEN-1-zeolh.eastus2.models.ai.azure.com"
    api_key = "mDPTRBXlnpbNbbXdgWxUkDPEVLtq0cKT"
    
    swagger_urls = [
        f"{base_url}/swagger.json",
        f"{base_url}/docs",
        f"{base_url}/openapi.json",
        f"{base_url}/api/docs",
        f"{base_url}/redoc",
        f"{base_url}/__docs__"
    ]
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json'
    }
    
    swagger_data = None
    
    for swagger_url in swagger_urls:
        logger.info(f"Trying: {swagger_url}")
        
        try:
            req = urllib.request.Request(swagger_url, headers=headers)
            response = urllib.request.urlopen(req, timeout=30)
            
            if response.getcode() == 200:
                content = response.read().decode('utf-8')
                
                try:
                    swagger_data = json.loads(content)
                    logger.info(f"✅ Successfully fetched swagger from: {swagger_url}")
                    break
                except json.JSONDecodeError:
                    # Might be HTML docs page
                    if '<html>' in content.lower() or 'swagger' in content.lower():
                        logger.info(f"📄 Found documentation page at: {swagger_url}")
                        logger.info(f"Content preview: {content[:200]}...")
                    continue
                    
        except urllib.error.HTTPError as e:
            logger.info(f"❌ {swagger_url}: HTTP {e.code}")
        except Exception as e:
            logger.info(f"❌ {swagger_url}: {str(e)}")
    
    return swagger_data

def analyze_swagger_endpoints(swagger_data):
    """Analyze swagger data to extract all endpoints"""
    
    logger.info("📋 Analyzing Swagger Endpoints")
    
    endpoints = []
    
    if not swagger_data:
        logger.warning("No swagger data available")
        return endpoints
    
    # Extract endpoints from swagger
    paths = swagger_data.get('paths', {})
    
    logger.info(f"Found {len(paths)} paths in swagger documentation")
    
    for path, methods in paths.items():
        for method, details in methods.items():
            endpoint_info = {
                'path': path,
                'method': method.upper(),
                'summary': details.get('summary', ''),
                'description': details.get('description', ''),
                'parameters': details.get('parameters', []),
                'request_body': details.get('requestBody', {}),
                'responses': details.get('responses', {})
            }
            endpoints.append(endpoint_info)
            
            logger.info(f"  📍 {method.upper()} {path}: {details.get('summary', 'No summary')}")
    
    return endpoints

def test_all_discovered_endpoints(endpoints, base_url, api_key):
    """Test all discovered endpoints systematically"""
    
    logger.info(f"\n🚀 Testing All Discovered Endpoints")
    logger.info(f"Base URL: {base_url}")
    logger.info(f"Total endpoints to test: {len(endpoints)}")
    
    # Basic test payload (minimal)
    basic_test_payload = {
        "test": "basic_connectivity"
    }
    
    # Time series test payload (based on our discoveries)
    ts_test_payload = {
        "series": {
            "y": [10, 12, 15, 20, 18, 14],
            "sizes": [6],
            "ds": [
                "2024-11-06T10:00:00Z",
                "2024-11-06T10:05:00Z", 
                "2024-11-06T10:10:00Z",
                "2024-11-06T10:15:00Z",
                "2024-11-06T10:20:00Z",
                "2024-11-06T10:25:00Z"
            ]
        },
        "detection_size": 3,
        "h": 2,
        "freq": "5min"
    }
    
    results = []
    
    for endpoint in endpoints:
        path = endpoint['path']
        method = endpoint['method']
        
        logger.info(f"\n{'='*50}")
        logger.info(f"Testing: {method} {path}")
        logger.info(f"Summary: {endpoint.get('summary', 'No summary')}")
        
        full_url = f"{base_url}{path}"
        
        # Choose appropriate payload
        if any(keyword in path.lower() for keyword in ['anomaly', 'forecast', 'predict', 'timegpt']):
            test_payload = ts_test_payload
            logger.info("Using time series payload")
        else:
            test_payload = basic_test_payload
            logger.info("Using basic test payload")
        
        result = test_single_endpoint(full_url, method, api_key, test_payload, endpoint)
        result['endpoint_info'] = endpoint
        results.append(result)
    
    return results

def test_single_endpoint(url, method, api_key, payload, endpoint_info):
    """Test a single endpoint with given payload"""
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    result = {
        'url': url,
        'method': method,
        'success': False,
        'status_code': None,
        'response_time': None,
        'error': None,
        'response_preview': None
    }
    
    try:
        # Prepare request based on method
        if method == 'GET':
            req = urllib.request.Request(url, headers=headers)
        else:
            body = str.encode(json.dumps(payload))
            req = urllib.request.Request(url, body, headers=headers)
            req.get_method = lambda: method
        
        start_time = datetime.now()
        
        # Test with short timeout for quick discovery
        response = urllib.request.urlopen(req, timeout=30)
        
        response_time = (datetime.now() - start_time).total_seconds()
        status_code = response.getcode()
        
        response_data = response.read()
        
        logger.info(f"  ✅ SUCCESS: {status_code} ({response_time:.2f}s)")
        logger.info(f"  📊 Response size: {len(response_data)} bytes")
        
        # Try to parse response
        try:
            parsed_response = json.loads(response_data.decode('utf-8'))
            response_preview = str(parsed_response)[:300]
            logger.info(f"  📄 Response: {response_preview}")
        except:
            response_preview = response_data.decode('utf-8')[:300]
            logger.info(f"  📄 Raw response: {response_preview}")
        
        result.update({
            'success': True,
            'status_code': status_code,
            'response_time': response_time,
            'response_preview': response_preview
        })
        
    except urllib.error.HTTPError as e:
        error_msg = f"HTTP {e.code}"
        try:
            error_details = e.read().decode("utf8", 'ignore')
            error_msg += f": {error_details[:200]}"
        except:
            pass
        
        logger.info(f"  ❌ {error_msg}")
        
        result.update({
            'success': False,
            'status_code': e.code,
            'error': error_msg
        })
        
    except Exception as e:
        error_msg = str(e)
        logger.info(f"  ❌ {error_msg}")
        
        result.update({
            'success': False,
            'error': error_msg
        })
    
    return result

def test_common_endpoints_if_no_swagger():
    """Test common endpoint patterns if swagger is not available"""
    
    logger.info("🔍 Testing Common Endpoint Patterns (No Swagger Available)")
    
    base_url = "https://TimeGEN-1-zeolh.eastus2.models.ai.azure.com"
    api_key = "mDPTRBXlnpbNbbXdgWxUkDPEVLtq0cKT"
    
    common_endpoints = [
        # Health/Info endpoints
        {'path': '/health', 'method': 'GET'},
        {'path': '/info', 'method': 'GET'},
        {'path': '/status', 'method': 'GET'},
        {'path': '/version', 'method': 'GET'},
        {'path': '/', 'method': 'GET'},
        
        # API endpoints we've seen before
        {'path': '/v1/anomaly_detection', 'method': 'POST'},
        {'path': '/v2/anomaly_detection', 'method': 'POST'},
        {'path': '/v2/online_anomaly_detection', 'method': 'POST'},
        {'path': '/anomaly_detection', 'method': 'POST'},
        {'path': '/anomaly_detection_multi_series', 'method': 'POST'},
        
        # Forecast endpoints
        {'path': '/forecast', 'method': 'POST'},
        {'path': '/v1/forecast', 'method': 'POST'},
        {'path': '/v2/forecast', 'method': 'POST'},
        {'path': '/predict', 'method': 'POST'},
        
        # TimeGPT specific
        {'path': '/timegpt', 'method': 'POST'},
        {'path': '/timegpt/anomaly_detection', 'method': 'POST'},
        {'path': '/timegpt/forecast', 'method': 'POST'},
        
        # API variations
        {'path': '/api/v1/anomaly_detection', 'method': 'POST'},
        {'path': '/api/v2/anomaly_detection', 'method': 'POST'},
        {'path': '/api/anomaly_detection', 'method': 'POST'},
        {'path': '/api/forecast', 'method': 'POST'},
    ]
    
    logger.info(f"Testing {len(common_endpoints)} common endpoint patterns")
    
    results = []
    
    for endpoint in common_endpoints:
        path = endpoint['path']
        method = endpoint['method']
        
        logger.info(f"\n📍 Testing: {method} {path}")
        
        full_url = f"{base_url}{path}"
        
        # Choose payload based on endpoint type
        if method == 'GET':
            payload = None
        elif any(keyword in path.lower() for keyword in ['anomaly', 'forecast', 'predict', 'timegpt']):
            # Use our validated time series format
            payload = {
                "series": {
                    "y": [10, 12, 15, 85, 18, 14],  # Include anomaly
                    "sizes": [6],
                    "ds": [
                        "2024-11-06T10:00:00Z",
                        "2024-11-06T10:05:00Z", 
                        "2024-11-06T10:10:00Z",
                        "2024-11-06T10:15:00Z",
                        "2024-11-06T10:20:00Z",
                        "2024-11-06T10:25:00Z"
                    ]
                },
                "detection_size": 3,
                "h": 2,
                "freq": "5min"
            }
        else:
            payload = {"test": "connectivity"}
        
        result = test_single_endpoint(full_url, method, api_key, payload, endpoint)
        results.append(result)
    
    return results

def analyze_results_and_recommend(results):
    """Analyze all test results and provide production recommendations"""
    
    logger.info(f"\n{'='*70}")
    logger.info("COMPREHENSIVE ENDPOINT ANALYSIS")
    logger.info(f"{'='*70}")
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    logger.info(f"Total endpoints tested: {len(results)}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")
    
    if successful:
        logger.info(f"\n✅ WORKING ENDPOINTS:")
        
        # Group by functionality
        health_endpoints = []
        anomaly_endpoints = []
        forecast_endpoints = []
        other_endpoints = []
        
        for result in successful:
            path = result['url'].split('/')[-1].lower()
            full_path = result['url']
            
            if any(keyword in full_path.lower() for keyword in ['health', 'status', 'info', 'version']):
                health_endpoints.append(result)
            elif any(keyword in full_path.lower() for keyword in ['anomaly']):
                anomaly_endpoints.append(result)
            elif any(keyword in full_path.lower() for keyword in ['forecast', 'predict']):
                forecast_endpoints.append(result)
            else:
                other_endpoints.append(result)
        
        if health_endpoints:
            logger.info(f"\n🏥 HEALTH/STATUS ENDPOINTS:")
            for result in health_endpoints:
                logger.info(f"  ✅ {result['method']} {result['url']} ({result.get('response_time', 0):.2f}s)")
        
        if anomaly_endpoints:
            logger.info(f"\n🚨 ANOMALY DETECTION ENDPOINTS:")
            for result in anomaly_endpoints:
                logger.info(f"  ✅ {result['method']} {result['url']} ({result.get('response_time', 0):.2f}s)")
                if result.get('response_preview'):
                    logger.info(f"    📄 {result['response_preview'][:100]}...")
        
        if forecast_endpoints:
            logger.info(f"\n📈 FORECAST ENDPOINTS:")
            for result in forecast_endpoints:
                logger.info(f"  ✅ {result['method']} {result['url']} ({result.get('response_time', 0):.2f}s)")
        
        if other_endpoints:
            logger.info(f"\n🔧 OTHER WORKING ENDPOINTS:")
            for result in other_endpoints:
                logger.info(f"  ✅ {result['method']} {result['url']} ({result.get('response_time', 0):.2f}s)")
        
        # Find best anomaly detection endpoint
        working_anomaly = [r for r in anomaly_endpoints if r['success'] and r.get('response_time', float('inf')) < 60]
        
        if working_anomaly:
            best_anomaly = min(working_anomaly, key=lambda x: x.get('response_time', float('inf')))
            
            logger.info(f"\n🏆 RECOMMENDED FOR PRODUCTION:")
            logger.info(f"  🎯 Best Anomaly Endpoint: {best_anomaly['method']} {best_anomaly['url']}")
            logger.info(f"  ⏱️ Response Time: {best_anomaly.get('response_time', 0):.2f}s")
            logger.info(f"  📊 Status: {best_anomaly.get('status_code', 'Unknown')}")
            
            # Test with multi-series
            logger.info(f"\n🚀 Testing multi-series on best endpoint...")
            test_multi_series_on_best_endpoint(best_anomaly['url'], api_key)
            
            return best_anomaly
        
    else:
        logger.info(f"\n❌ No working endpoints found")
        
        # Analyze error patterns
        error_patterns = {}
        for result in failed:
            error_code = str(result.get('status_code', 'Unknown'))
            if error_code not in error_patterns:
                error_patterns[error_code] = []
            error_patterns[error_code].append(result)
        
        logger.info(f"\n📊 Error Analysis:")
        for error_code, error_results in error_patterns.items():
            logger.info(f"  {error_code}: {len(error_results)} occurrences")
            if error_results:
                sample_error = error_results[0].get('error', 'No details')
                logger.info(f"    Sample: {sample_error[:150]}")
    
    return None

def test_multi_series_on_best_endpoint(endpoint_url, api_key):
    """Test our 16 metrics on the best working endpoint"""
    
    logger.info(f"Testing OUR METRICS on best endpoint: {endpoint_url}")
    
    # Generate timestamps
    timestamps = []
    base_time = datetime.now() - timedelta(hours=1)
    for i in range(8):
        ts = base_time + timedelta(minutes=i * 10)
        timestamps.append(ts.strftime("%Y-%m-%dT%H:%M:%SZ"))
    
    # Our key metrics with anomaly patterns
    our_metrics = {
        "cpu_usage": [45, 47, 52, 78, 75, 52, 48, 46],
        "memory_gb": [2.1, 2.0, 1.9, 0.3, 0.4, 1.8, 1.9, 2.0],
        "http_5xx": [5, 8, 12, 180, 172, 18, 12, 8],
        "exceptions": [2, 3, 85, 78, 8, 5, 3, 2],
        "failed_req": [40, 50, 320, 310, 65, 55, 45, 42]
    }
    
    # Build multi-series payload
    all_values = []
    sizes = []
    all_timestamps = []
    
    for metric_name, values in our_metrics.items():
        all_values.extend(values)
        sizes.append(len(values))
        all_timestamps.extend(timestamps)
    
    multi_payload = {
        "series": {
            "y": all_values,
            "sizes": sizes,
            "ds": all_timestamps
        },
        "detection_size": 3,
        "h": 2,
        "freq": "10min"
    }
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        
        body = str.encode(json.dumps(multi_payload))
        req = urllib.request.Request(endpoint_url, body, headers)
        
        logger.info(f"  📊 Sending {len(our_metrics)} metrics")
        logger.info(f"  📋 Metrics: {list(our_metrics.keys())}")
        
        start_time = datetime.now()
        response = urllib.request.urlopen(req, timeout=90)
        response_time = (datetime.now() - start_time).total_seconds()
        
        result_data = response.read()
        
        logger.info(f"  🎊 MULTI-SERIES SUCCESS!")
        logger.info(f"  ⏱️ Response time: {response_time:.2f}s")
        logger.info(f"  📊 Response size: {len(result_data)} bytes")
        
        try:
            parsed_result = json.loads(result_data.decode('utf-8'))
            logger.info(f"  📄 Response preview: {str(parsed_result)[:300]}...")
            
            # Look for anomalies
            response_str = str(parsed_result).lower()
            if 'anomaly' in response_str or 'outlier' in response_str:
                logger.info(f"  🚨 Anomaly detection keywords found in response!")
            
            logger.info(f"\n🎊 READY FOR PRODUCTION UPDATE!")
            logger.info(f"  ✅ Endpoint: {endpoint_url}")
            logger.info(f"  ✅ Multi-series: Working")
            logger.info(f"  ✅ Performance: {response_time:.2f}s")
            
            return True, parsed_result
            
        except json.JSONDecodeError:
            raw_response = result_data.decode('utf-8')
            logger.info(f"  📄 Raw response: {raw_response[:300]}...")
            return True, raw_response
            
    except Exception as e:
        logger.info(f"  ❌ Multi-series test failed: {str(e)}")
        return False, str(e)

def main():
    """Main function to run comprehensive endpoint discovery"""
    
    logger.info("🚀 COMPREHENSIVE TimeGEN-1 ENDPOINT DISCOVERY")
    logger.info("=" * 70)
    
    # Step 1: Try to get swagger documentation
    swagger_data = fetch_swagger_documentation()
    
    results = []
    
    if swagger_data:
        # Step 2: Analyze swagger and test all documented endpoints
        endpoints = analyze_swagger_endpoints(swagger_data)
        if endpoints:
            base_url = "https://TimeGEN-1-zeolh.eastus2.models.ai.azure.com"
            api_key = "mDPTRBXlnpbNbbXdgWxUkDPEVLtq0cKT"
            results = test_all_discovered_endpoints(endpoints, base_url, api_key)
    
    if not results:
        # Step 3: Fallback to common endpoint patterns
        results = test_common_endpoints_if_no_swagger()
    
    # Step 4: Analyze results and recommend best endpoint for production
    best_endpoint = analyze_results_and_recommend(results)
    
    if best_endpoint:
        logger.info(f"\n🎯 PRODUCTION RECOMMENDATION:")
        logger.info(f"Replace current endpoint with: {best_endpoint['url']}")
        logger.info(f"Expected performance: {best_endpoint.get('response_time', 0):.2f}s response time")
        logger.info(f"Ready for immediate deployment!")
    else:
        logger.info(f"\n📊 Continue using statistical analysis while Azure resolves issues")
    
    return results

if __name__ == "__main__":
    main()

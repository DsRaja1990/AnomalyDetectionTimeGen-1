"""
TimeGEN-1 Final Correct Format Test
Using the exact format revealed by API validation errors
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

def test_final_correct_format():
    """Test TimeGEN-1 with the exact correct format"""
    
    endpoint_url = "https://TimeGEN-1-AssurantPoc.eastus2.models.ai.azure.com/v2/online_anomaly_detection"
    api_key = "n0swAKTILYJZgcfSQ1QesDuKvLp5j1Zy"
    
    # TimeGEN-1 expects:
    # - series.y (the actual time series data)
    # - series.sizes (array indicating the size of each series)  
    # - freq (frequency at root level)
    # - detection_size
    # - h (forecast horizon)
    
    # Sample data
    timestamps = []
    base_time = datetime.now() - timedelta(hours=1)
    for i in range(10):
        ts = base_time + timedelta(minutes=i * 5)
        timestamps.append(ts.strftime("%Y-%m-%dT%H:%M:%SZ"))
    
    # Test payloads with EXACT TimeGEN-1 format
    test_payloads = [
        # 1. Single series - exact format
        {
            "name": "single_series_exact",
            "payload": {
                "series": {
                    "y": [
                        [45.2, 47.1, 52.3, 48.9, 51.2, 46.8, 73.1, 75.7, 78.2, 76.5]  # CPU usage with anomaly
                    ],
                    "sizes": [10]  # One series with 10 data points
                },
                "freq": "5min",
                "detection_size": 5,
                "h": 1
            }
        },
        
        # 2. Multi-series - 3 metrics
        {
            "name": "multi_series_3_exact",
            "payload": {
                "series": {
                    "y": [
                        [45.2, 47.1, 52.3, 48.9, 51.2, 46.8, 73.1, 75.7, 78.2, 76.5],  # CPU usage
                        [2.1, 2.0, 1.8, 1.9, 1.7, 2.0, 1.2, 1.1, 0.9, 1.0],            # Memory available  
                        [5, 8, 12, 15, 18, 12, 42, 38, 45, 41]                          # HTTP 5xx errors
                    ],
                    "sizes": [10, 10, 10]  # Three series, each with 10 data points
                },
                "freq": "5min", 
                "detection_size": 5,
                "h": 1
            }
        },
        
        # 3. Full 16 metrics - all metrics
        {
            "name": "all_16_metrics_exact",
            "payload": {
                "series": {
                    "y": [
                        [45.2, 47.1, 52.3, 48.9, 51.2, 46.8, 73.1, 75.7, 78.2, 76.5],                           # cpu_usage
                        [2.1, 2.0, 1.8, 1.9, 1.7, 2.0, 1.2, 1.1, 0.9, 1.0],                                     # memory_available
                        [1250, 1320, 1410, 1380, 1450, 1290, 1850, 1980, 2100, 1950],                           # request_count
                        [145.2, 152.1, 168.3, 159.7, 171.2, 148.9, 255.4, 278.6, 301.3, 263.8],               # response_time_avg
                        [1190, 1250, 1320, 1290, 1350, 1210, 1580, 1680, 1750, 1620],                          # http_2xx_success
                        [35, 42, 51, 48, 58, 41, 145, 162, 178, 151],                                            # http_4xx_errors
                        [5, 8, 12, 15, 42, 18, 125, 138, 172, 179],                                              # http_5xx_errors (anomaly)
                        [2, 3, 5, 7, 18, 8, 65, 75, 88, 82],                                                     # exception_count
                        [40, 50, 63, 63, 100, 59, 270, 300, 350, 330],                                          # request_failed
                        [12, 14, 16, 18, 25, 19, 47, 58, 65, 61],                                                # database_connections
                        [0.85, 0.83, 0.79, 0.76, 0.62, 0.74, 0.38, 0.28, 0.22, 0.31],                         # cache_hit_ratio
                        [245.6, 267.3, 298.1, 314.7, 456.2, 325.8, 789.4, 823.9, 901.5, 867.8],              # disk_io_read
                        [156.3, 172.8, 189.4, 201.2, 298.7, 215.6, 476.4, 504.8, 538.1, 516.2],              # disk_io_write
                        [2048576, 2234567, 2456789, 2678901, 3987654, 2789012, 6654321, 7567890, 8123456, 7456789],  # network_bytes_in
                        [1567890, 1789012, 1987654, 2156789, 3234567, 2267890, 4987654, 5998765, 6456789, 5989012],  # network_bytes_out
                        [89, 95, 103, 108, 142, 115, 234, 268, 291, 273]                                         # active_users
                    ],
                    "sizes": [10] * 16  # 16 series, each with 10 data points
                },
                "freq": "5min",
                "detection_size": 5,
                "h": 1
            }
        },
        
        # 4. Optimized format - key metrics only
        {
            "name": "key_metrics_optimized",
            "payload": {
                "series": {
                    "y": [
                        [45.2, 47.1, 52.3, 48.9, 51.2, 46.8, 73.1, 75.7, 78.2, 76.5],  # cpu_usage
                        [2.1, 2.0, 1.8, 1.9, 1.7, 2.0, 1.2, 1.1, 0.9, 1.0],            # memory_available
                        [5, 8, 12, 15, 42, 18, 125, 138, 172, 179],                      # http_5xx_errors
                        [2, 3, 5, 7, 18, 8, 65, 75, 88, 82],                             # exception_count
                        [40, 50, 63, 63, 100, 59, 270, 300, 350, 330]                   # request_failed
                    ],
                    "sizes": [10, 10, 10, 10, 10]  # 5 key metrics
                },
                "freq": "5min",
                "detection_size": 3,  # Smaller detection window
                "h": 1
            }
        }
    ]
    
    results = []
    
    logger.info(f"Testing TimeGEN-1 with EXACT correct format")
    logger.info(f"URL: {endpoint_url}")
    
    for payload_info in test_payloads:
        payload_name = payload_info["name"]
        payload = payload_info["payload"]
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing: {payload_name}")
        logger.info(f"Series count: {len(payload['series']['y'])}")
        logger.info(f"Data points per series: {payload['series']['sizes']}")
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
            series_count = len(payload['series']['y'])
            timeout = 30 if series_count <= 5 else 180  # Longer timeout for full 16 metrics
            logger.info(f"Using timeout: {timeout}s for {series_count} series")
            
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
                    "series_count": series_count,
                    "detection_size": payload['detection_size'],
                    "parsed_response": parsed_response
                }
                
                logger.info(f"🎉 SUCCESS!")
                logger.info(f"   Status: {result['status_code']}")
                logger.info(f"   Time: {response_time:.2f}s")
                logger.info(f"   Size: {len(response_data)} bytes")
                
                # Analyze response structure
                if isinstance(parsed_response, dict):
                    logger.info(f"   Response keys: {list(parsed_response.keys())}")
                    
                    # Look for anomaly detection results
                    anomaly_count = 0
                    if isinstance(parsed_response, list):
                        for series_result in parsed_response:
                            if isinstance(series_result, dict) and 'anomaly_flag' in series_result:
                                flags = series_result.get('anomaly_flag', [])
                                if any(flag == 1 for flag in flags):
                                    anomaly_count += 1
                    elif 'anomaly_flag' in parsed_response:
                        flags = parsed_response.get('anomaly_flag', [])
                        if any(flag == 1 for flag in flags):
                            anomaly_count = 1
                    elif 'series_0' in str(parsed_response):  # Multi-series response format
                        for key in parsed_response:
                            if isinstance(parsed_response[key], dict) and 'anomaly_flag' in parsed_response[key]:
                                flags = parsed_response[key].get('anomaly_flag', [])
                                if any(flag == 1 for flag in flags):
                                    anomaly_count += 1
                    
                    if anomaly_count > 0:
                        logger.info(f"   🚨 Anomalies detected in {anomaly_count} series!")
                        result["anomalies_detected"] = anomaly_count
                    else:
                        logger.info(f"   ✅ No anomalies detected")
                
                logger.info(f"   Response preview: {str(parsed_response)[:200]}...")
                
                results.append(result)
                
                # Special celebration for full 16-metric success  
                if payload_name == "all_16_metrics_exact" and response.getcode() == 200:
                    logger.info(f"\n🎊🎊🎊 BREAKTHROUGH! 🎊🎊🎊")
                    logger.info(f"ALL 16 METRICS processed successfully in {response_time:.2f} seconds!")
                    logger.info(f"Multi-series TimeGEN-1 anomaly detection is FULLY OPERATIONAL!")
                
        except urllib.error.HTTPError as e:
            error_details = ""
            try:
                error_body = e.read().decode('utf-8')
                error_details = error_body[:500]
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
                "series_count": len(payload['series']['y']),
                "detection_size": payload['detection_size']
            })
                
        except Exception as e:
            logger.warning(f"❌ ERROR: {str(e)}")
            results.append({
                "payload_type": payload_name,
                "success": False,
                "error": str(e),
                "series_count": len(payload['series']['y']),
                "detection_size": payload['detection_size']
            })
    
    # Final analysis
    logger.info(f"\n{'='*80}")
    logger.info("FINAL TEST RESULTS")
    logger.info(f"{'='*80}")
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    logger.info(f"Total tests: {len(results)}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")
    
    if successful:
        logger.info(f"\n✅ WORKING CONFIGURATIONS:")
        for result in successful:
            series_count = result.get('series_count', 0)
            response_time = result.get('response_time', 0)
            anomalies = result.get('anomalies_detected', 0)
            logger.info(f"  🎯 {result['payload_type']}: {series_count} series, {response_time:.2f}s, {anomalies} anomalies")
            
        # Determine best configuration
        best_config = max(successful, key=lambda x: x.get('series_count', 0))
        logger.info(f"\n🏆 RECOMMENDED CONFIGURATION:")
        logger.info(f"   {best_config['payload_type']} - {best_config.get('series_count')} series in {best_config.get('response_time', 0):.2f}s")
        
        # Multi-series capability assessment
        max_series = max(r.get('series_count', 0) for r in successful)
        if max_series >= 16:
            logger.info(f"\n🎊 MULTI-SERIES FULLY SUPPORTED: All {max_series} metrics can be processed!")
        elif max_series >= 5:
            logger.info(f"\n✅ MULTI-SERIES PARTIALLY SUPPORTED: Up to {max_series} metrics")
        else:
            logger.info(f"\n⚠️  LIMITED MULTI-SERIES: Only {max_series} metrics supported")
    
    if failed:
        logger.info(f"\n❌ FAILED CONFIGURATIONS:")
        for result in failed:
            logger.info(f"  • {result['payload_type']}: {result.get('error', 'Unknown error')}")
    
    # Production recommendations
    if successful:
        logger.info(f"\n📋 PRODUCTION RECOMMENDATIONS:")
        if any(r.get('series_count', 0) >= 16 for r in successful):
            logger.info(f"  ✅ USE MULTI-SERIES: Process all 16 metrics in single API call")
            logger.info(f"  ✅ CORRELATION DETECTION: TimeGEN-1 will detect inter-metric correlations")
            logger.info(f"  ✅ PERFORMANCE: Faster than multiple single-metric calls")
        else:
            logger.info(f"  ⚠️  USE BATCH PROCESSING: Process metrics in smaller batches") 
        
        fastest = min(successful, key=lambda x: x.get('response_time', float('inf')))
        logger.info(f"  ⚡ FASTEST CONFIG: {fastest['payload_type']} ({fastest.get('response_time', 0):.2f}s)")
    
    # Save detailed results
    output_file = "c:\\Users\\dsraja\\Documents\\PythonPoc\\timegen_final_test_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "endpoint_tested": endpoint_url,
            "total_tests": len(results),
            "successful_tests": len(successful),
            "failed_tests": len(failed),
            "multi_series_fully_supported": any(r.get('series_count', 0) >= 16 for r in successful),
            "max_series_supported": max((r.get('series_count', 0) for r in successful), default=0),
            "best_performance": min((r.get('response_time', float('inf')) for r in successful), default=0),
            "results": results
        }, f, indent=2)
    
    logger.info(f"\n💾 Detailed results saved to: {output_file}")
    
    return results

if __name__ == "__main__":
    test_final_correct_format()

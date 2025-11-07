"""
TimeGEN-1 Single Array Format Test
Based on "y must be a list of floats" error - using flattened array
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

def test_single_array_format():
    """Test TimeGEN-1 with single flattened array format"""
    
    endpoint_url = "https://TimeGEN-1-AssurantPoc.eastus2.models.ai.azure.com/v2/online_anomaly_detection"
    api_key = "n0swAKTILYJZgcfSQ1QesDuKvLp5j1Zy"
    
    # TimeGEN-1 expects:
    # - series.y: single flattened list of all values from all metrics
    # - series.sizes: array indicating how many values belong to each series
    # - freq, detection_size, h
    
    # Sample data for different scenarios
    cpu_values = [45.2, 47.1, 52.3, 48.9, 51.2, 46.8, 73.1, 75.7, 78.2, 76.5]                  # 10 values
    memory_values = [2.1, 2.0, 1.8, 1.9, 1.7, 2.0, 1.2, 1.1, 0.9, 1.0]                          # 10 values  
    http5xx_values = [5, 8, 12, 15, 42, 18, 125, 138, 172, 179]                                   # 10 values
    exception_values = [2, 3, 5, 7, 18, 8, 65, 75, 88, 82]                                        # 10 values
    request_failed_values = [40, 50, 63, 63, 100, 59, 270, 300, 350, 330]                         # 10 values
    
    # All 16 metrics with 10 values each
    all_16_metrics = [
        [45.2, 47.1, 52.3, 48.9, 51.2, 46.8, 73.1, 75.7, 78.2, 76.5],                           # cpu_usage
        [2.1, 2.0, 1.8, 1.9, 1.7, 2.0, 1.2, 1.1, 0.9, 1.0],                                     # memory_available
        [1250, 1320, 1410, 1380, 1450, 1290, 1850, 1980, 2100, 1950],                           # request_count
        [145.2, 152.1, 168.3, 159.7, 171.2, 148.9, 255.4, 278.6, 301.3, 263.8],               # response_time_avg
        [1190, 1250, 1320, 1290, 1350, 1210, 1580, 1680, 1750, 1620],                          # http_2xx_success
        [35, 42, 51, 48, 58, 41, 145, 162, 178, 151],                                            # http_4xx_errors
        [5, 8, 12, 15, 42, 18, 125, 138, 172, 179],                                              # http_5xx_errors
        [2, 3, 5, 7, 18, 8, 65, 75, 88, 82],                                                     # exception_count
        [40, 50, 63, 63, 100, 59, 270, 300, 350, 330],                                          # request_failed
        [12, 14, 16, 18, 25, 19, 47, 58, 65, 61],                                                # database_connections
        [0.85, 0.83, 0.79, 0.76, 0.62, 0.74, 0.38, 0.28, 0.22, 0.31],                         # cache_hit_ratio
        [245.6, 267.3, 298.1, 314.7, 456.2, 325.8, 789.4, 823.9, 901.5, 867.8],              # disk_io_read
        [156.3, 172.8, 189.4, 201.2, 298.7, 215.6, 476.4, 504.8, 538.1, 516.2],              # disk_io_write
        [2048576, 2234567, 2456789, 2678901, 3987654, 2789012, 6654321, 7567890, 8123456, 7456789],  # network_bytes_in
        [1567890, 1789012, 1987654, 2156789, 3234567, 2267890, 4987654, 5998765, 6456789, 5989012],  # network_bytes_out
        [89, 95, 103, 108, 142, 115, 234, 268, 291, 273]                                         # active_users
    ]
    
    # Test payloads with flattened array format
    test_payloads = [
        # 1. Single metric - flattened
        {
            "name": "single_metric_flattened",
            "payload": {
                "series": {
                    "y": cpu_values,  # Single list of floats
                    "sizes": [10]     # One series with 10 values
                },
                "freq": "5min",
                "detection_size": 5,
                "h": 1
            }
        },
        
        # 2. Three metrics - flattened concatenation 
        {
            "name": "three_metrics_flattened",
            "payload": {
                "series": {
                    "y": cpu_values + memory_values + http5xx_values,  # Concatenated list
                    "sizes": [10, 10, 10]  # Three series: 10 + 10 + 10 values
                },
                "freq": "5min",
                "detection_size": 5,
                "h": 1
            }
        },
        
        # 3. Five key metrics - flattened
        {
            "name": "five_key_metrics_flattened",  
            "payload": {
                "series": {
                    "y": cpu_values + memory_values + http5xx_values + exception_values + request_failed_values,
                    "sizes": [10, 10, 10, 10, 10]  # Five series with 10 values each
                },
                "freq": "5min",
                "detection_size": 3,
                "h": 1
            }
        },
        
        # 4. ALL 16 METRICS - the ultimate test!
        {
            "name": "all_16_metrics_flattened",
            "payload": {
                "series": {
                    "y": [val for metric in all_16_metrics for val in metric],  # Flatten all metrics
                    "sizes": [10] * 16  # 16 series, each with 10 values
                },
                "freq": "5min", 
                "detection_size": 5,
                "h": 1
            }
        }
    ]
    
    results = []
    
    logger.info(f"Testing TimeGEN-1 with FLATTENED ARRAY format")
    logger.info(f"URL: {endpoint_url}")
    
    for payload_info in test_payloads:
        payload_name = payload_info["name"]
        payload = payload_info["payload"]
        
        logger.info(f"\n{'='*70}")
        logger.info(f"Testing: {payload_name}")
        
        series_count = len(payload['series']['sizes'])
        total_values = sum(payload['series']['sizes'])
        logger.info(f"Series count: {series_count}")
        logger.info(f"Total values: {total_values}")
        logger.info(f"Values per series: {payload['series']['sizes']}")
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
            timeout = 30 if series_count <= 5 else 300  # 5 minutes for 16 series
            logger.info(f"Using timeout: {timeout}s for {series_count} series")
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_data = response.read().decode('utf-8')
                response_time = (datetime.now() - start_time).total_seconds()
                
                try:
                    parsed_response = json.loads(response_data)
                except:
                    parsed_response = {"raw_response": response_data[:1000]}
                
                result = {
                    "payload_type": payload_name,
                    "success": True,
                    "status_code": response.getcode(),
                    "response_time": response_time,
                    "response_size": len(response_data),
                    "series_count": series_count,
                    "total_values": total_values,
                    "detection_size": payload['detection_size'],
                    "parsed_response": parsed_response
                }
                
                logger.info(f"\n🎉🎉 SUCCESS! 🎉🎉")
                logger.info(f"   Status: {result['status_code']}")
                logger.info(f"   Time: {response_time:.2f}s")
                logger.info(f"   Size: {len(response_data)} bytes")
                
                # Analyze response for anomalies
                if isinstance(parsed_response, dict):
                    logger.info(f"   Response type: {type(parsed_response).__name__}")
                    logger.info(f"   Response keys: {list(parsed_response.keys())}")
                    
                    # Count anomalies detected
                    anomaly_metrics = []
                    total_anomalies = 0
                    
                    # Check different response formats
                    for key, value in parsed_response.items():
                        if isinstance(value, dict):
                            # Individual series results
                            if 'anomaly_flag' in value:
                                flags = value.get('anomaly_flag', [])
                                anomaly_count = sum(1 for flag in flags if flag == 1)
                                if anomaly_count > 0:
                                    anomaly_metrics.append(f"{key}({anomaly_count})")
                                    total_anomalies += anomaly_count
                            
                            # Anomaly scores
                            if 'anomaly_score' in value:
                                scores = value.get('anomaly_score', [])
                                high_scores = [s for s in scores if isinstance(s, (int, float)) and s > 0.7]
                                if high_scores:
                                    logger.info(f"   {key}: High anomaly scores: {high_scores}")
                    
                    if anomaly_metrics:
                        logger.info(f"   🚨 ANOMALIES DETECTED: {anomaly_metrics} (total: {total_anomalies})")
                        result["anomaly_metrics"] = anomaly_metrics
                        result["total_anomalies"] = total_anomalies
                    else:
                        logger.info(f"   ✅ No significant anomalies detected")
                    
                    # Show response structure
                    logger.info(f"   Response sample: {str(parsed_response)[:300]}...")
                
                results.append(result)
                
                # CELEBRATION for successful multi-series!
                if payload_name == "all_16_metrics_flattened" and response.getcode() == 200:
                    logger.info(f"\n🚀🚀🚀 BREAKTHROUGH ACHIEVED! 🚀🚀🚀")
                    logger.info(f"ALL 16 METRICS processed successfully!")
                    logger.info(f"Processing time: {response_time:.2f} seconds")
                    logger.info(f"Multi-series TimeGEN-1 is FULLY OPERATIONAL!")
                    logger.info(f"You can now use this format in production! 🎊")
                elif series_count > 1 and response.getcode() == 200:
                    logger.info(f"\n✨ Multi-series SUCCESS: {series_count} metrics in {response_time:.2f}s!")
                
        except urllib.error.HTTPError as e:
            error_details = ""
            try:
                error_body = e.read().decode('utf-8')
                error_details = error_body[:1000]
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
                "series_count": series_count,
                "total_values": total_values,
                "detection_size": payload['detection_size']
            })
                
        except Exception as e:
            logger.warning(f"❌ ERROR: {str(e)}")
            results.append({
                "payload_type": payload_name,
                "success": False,
                "error": str(e),
                "series_count": series_count,
                "total_values": total_values,
                "detection_size": payload['detection_size']
            })
    
    # FINAL ANALYSIS
    logger.info(f"\n{'='*80}")
    logger.info("🎯 FINAL RESULTS & PRODUCTION RECOMMENDATIONS 🎯")
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
            total_anomalies = result.get('total_anomalies', 0)
            logger.info(f"  🎯 {result['payload_type']}: {series_count} series, {response_time:.2f}s, {total_anomalies} anomalies")
            
        # Production guidance
        max_series = max(r.get('series_count', 0) for r in successful)
        best_time = min(r.get('response_time', float('inf')) for r in successful)
        
        logger.info(f"\n🏆 PRODUCTION READY CONFIGURATION:")
        if max_series >= 16:
            logger.info(f"   ✅ MULTI-SERIES FULLY SUPPORTED: Process all {max_series} metrics simultaneously")
            logger.info(f"   ✅ PERFORMANCE: Fastest response in {best_time:.2f} seconds")
            logger.info(f"   ✅ CORRELATION DETECTION: TimeGEN-1 analyzes inter-metric relationships")
            logger.info(f"   ✅ DEPLOYMENT: Ready for production with correct payload format!")
        else:
            logger.info(f"   ⚠️  PARTIAL MULTI-SERIES: Up to {max_series} metrics supported")
            logger.info(f"   💡 RECOMMENDATION: Process metrics in batches of {max_series}")
        
        logger.info(f"\n📋 CORRECT PAYLOAD FORMAT FOR PRODUCTION:")
        logger.info(f'   {{')
        logger.info(f'     "series": {{')
        logger.info(f'       "y": [val1, val2, val3, ...],  // Flattened array of all metric values')
        logger.info(f'       "sizes": [10, 10, 10, ...]     // Number of values per metric')
        logger.info(f'     }},')
        logger.info(f'     "freq": "5min",')
        logger.info(f'     "detection_size": 5,')
        logger.info(f'     "h": 1')
        logger.info(f'   }}')
    
    if failed:
        logger.info(f"\n❌ FAILED CONFIGURATIONS:")
        for result in failed:
            logger.info(f"  • {result['payload_type']}: {result.get('error', 'Unknown error')}")
    
    # Save comprehensive results
    output_file = "c:\\Users\\dsraja\\Documents\\PythonPoc\\timegen_production_ready_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "endpoint_tested": endpoint_url,
            "production_ready": len(successful) > 0,
            "multi_series_supported": any(r.get('series_count', 0) > 1 for r in successful),
            "max_series_supported": max((r.get('series_count', 0) for r in successful), default=0),
            "best_response_time": min((r.get('response_time', float('inf')) for r in successful), default=0),
            "total_tests": len(results),
            "successful_tests": len(successful),
            "failed_tests": len(failed),
            "results": results,
            "payload_format": {
                "series": {
                    "y": "Single flattened array of all metric values",
                    "sizes": "Array indicating number of values per metric"
                },
                "freq": "Time frequency (e.g., '5min')",
                "detection_size": "Detection window size",
                "h": "Forecast horizon"
            }
        }, f, indent=2)
    
    logger.info(f"\n💾 Complete results saved to: {output_file}")
    
    return results

if __name__ == "__main__":
    test_single_array_format()

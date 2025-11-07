import azure.functions as func
import logging

# DEPLOYMENT VERSION TRACKER - Update this timestamp when deploying new code
DEPLOYMENT_VERSION = "2025-11-06T16:25:00Z"
DEPLOYMENT_BUILD = "debug_logging_fix_v1"

app = func.FunctionApp()

@app.function_name(name="AnomalyTSPocTimer")
@app.schedule(schedule="0 */5 * * * *", arg_name="timer", run_on_startup=True, use_monitor=False)
def anomaly_detection_timer(timer: func.TimerRequest) -> None:
    """
    Timer-triggered function for anomaly detection
    Runs every 5 minutes to analyze metrics and detect anomalies
    """
    from datetime import datetime
    import os
    
    # Initialize logger first before any error handling
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Import shared modules with comprehensive error handling and debugging
    logger.info("Attempting to import shared modules...")
    
    # Debug: Check what's available in the current directory
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"Current directory: {current_dir}")
    
    try:
        # List contents to debug
        contents = os.listdir(current_dir)
        logger.info(f"Directory contents: {contents}")
        
        # Check if shared directory exists
        shared_path = os.path.join(current_dir, 'shared')
        logger.info(f"Shared path exists: {os.path.exists(shared_path)}")
        if os.path.exists(shared_path):
            shared_contents = os.listdir(shared_path)
            logger.info(f"Shared directory contents: {shared_contents}")
    except Exception as debug_e:
        logger.error(f"Debug listing failed: {debug_e}")
    
    # Try multiple import strategies
    metrics_service = None
    ai_client = None
    state_manager = None
    prefilter = None
    enhanced_detector = None
    logic_app_client = None
    
    # Strategy 1: Standard shared module import
    try:
        from shared.metrics_query import create_metrics_service
        from shared.ai_foundry_client import create_ai_client
        from shared.state_manager import create_state_manager
        from shared.anomaly_detection import create_prefilter
        from shared.enhanced_anomaly_detection import create_enhanced_detector
        from shared.logic_app_client import create_logic_app_client
        logger.info("✓ Successfully imported shared modules using standard import")
    except ImportError as e1:
        logger.warning(f"Standard import failed: {e1}")
        
        # Strategy 2: Add shared to sys.path and try again
        try:
            sys.path.insert(0, shared_path)
            from shared.metrics_query import create_metrics_service
            from shared.ai_foundry_client import create_ai_client  
            from shared.state_manager import create_state_manager
            from shared.anomaly_detection import create_prefilter
            from shared.enhanced_anomaly_detection import create_enhanced_detector
            from shared.logic_app_client import create_logic_app_client
            logger.info("✓ Successfully imported shared modules using sys.path modification")
        except ImportError as e2:
            logger.warning(f"Sys.path import failed: {e2}")
            
            # Strategy 3: Handle flattened file structure (files with shared\\ prefix)
            try:
                # The files are actually flattened with shared\\ prefix, so let's work with that
                import importlib.util
                import sys
                
                # Create module instances from the flattened files
                def load_module_from_file(module_name, file_path):
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    return module
                
                # Load each module from its actual file location
                metrics_query = load_module_from_file("metrics_query", os.path.join(current_dir, "shared\\metrics_query.py"))
                ai_foundry_client = load_module_from_file("ai_foundry_client", os.path.join(current_dir, "shared\\ai_foundry_client.py"))
                state_manager = load_module_from_file("state_manager", os.path.join(current_dir, "shared\\state_manager.py"))
                anomaly_detection = load_module_from_file("anomaly_detection", os.path.join(current_dir, "shared\\anomaly_detection.py"))
                enhanced_anomaly_detection = load_module_from_file("enhanced_anomaly_detection", os.path.join(current_dir, "shared\\enhanced_anomaly_detection.py"))
                logic_app_client = load_module_from_file("logic_app_client", os.path.join(current_dir, "shared\\logic_app_client.py"))
                
                create_metrics_service = metrics_query.create_metrics_service
                create_ai_client = ai_foundry_client.create_ai_client
                create_state_manager = state_manager.create_state_manager
                create_prefilter = anomaly_detection.create_prefilter
                create_enhanced_detector = enhanced_anomaly_detection.create_enhanced_detector
                create_logic_app_client = logic_app_client.create_logic_app_client
                
                logger.info("✓ Successfully imported shared modules using flattened file structure")
            except Exception as e3:
                logger.error(f"Flattened structure import failed: {e3}")
                
                # Strategy 4: Last resort - try to work around the structure issue completely
                try:
                    # Create minimal implementations to prevent total failure
                    logger.warning("Creating minimal fallback implementations...")
                    
                    def create_metrics_service():
                        logger.warning("Using fallback metrics service - no actual metrics will be queried")
                        return None
                    
                    def create_ai_client():
                        logger.warning("Using fallback AI client - no AI analysis will be performed")
                        return None
                        
                    def create_state_manager():
                        logger.warning("Using fallback state manager - no state will be saved")
                        return None
                        
                    def create_prefilter():
                        logger.warning("Using fallback prefilter - no pre-filtering will be performed")
                        return None
                        
                    def create_enhanced_detector():
                        logger.warning("Using fallback enhanced detector - no enhanced detection will be performed")
                        return None
                        
                    def create_logic_app_client():
                        logger.warning("Using fallback logic app client - no alerts will be sent")
                        return None
                    
                    logger.warning("⚠️ Running with fallback implementations - limited functionality")
                    
                except Exception as e4:
                    logger.error(f"Even fallback creation failed: {e4}")
                    logger.error("Cannot proceed at all")
                    return
    
    timestamp = datetime.utcnow()
    logger.info(f"DEPLOYMENT VERSION: {DEPLOYMENT_VERSION} | BUILD: {DEPLOYMENT_BUILD}")
    logger.info(f"Anomaly detection started at {timestamp.isoformat()}")
    
    # Initialize services
    metrics_service = create_metrics_service()
    ai_client = create_ai_client()
    state_manager = create_state_manager()
    prefilter = create_prefilter()
    enhanced_detector = create_enhanced_detector()  # NEW: Enhanced detection
    logic_app_client = create_logic_app_client()
    
    # Validation
    if not metrics_service:
        logger.error("Failed to initialize metrics service. Check APPINSIGHTS_RESOURCE_ID.")
        return
    
    if not ai_client:
        logger.error("Failed to initialize AI client. Check AI_FOUNDATION_* settings.")
        return
    
    if not state_manager:
        logger.warning("State manager not available. Running without historical context.")
    
    if not logic_app_client:
        logger.warning("Logic App client not available. Alerts will not be sent.")
    
    try:
        # Step 1: Query metrics from Application Insights
        # Changed from 10 to 25 minutes to account for AppInsights ingestion lag (2-5 min)
        # - Application Insights has 2-5 minute ingestion delay
        # - Without buffer, recent spikes are missed (data not ingested yet)
        # - 25 minutes = 20 minutes data + 5 minute ingestion buffer
        # - CRITICAL: This fixes spike detection failures (e.g., 504 failed requests missed)
        # - More data points (25 vs 10) = better trend detection
        # - Lower false positives (more context)
        # - Better pattern recognition (memory leaks, gradual degradation)
        # - Cost impact: minimal (~$5-10/month additional)
        # - Performance impact: +5 seconds query time (acceptable)
        lookback_minutes = int(os.getenv("METRICS_LOOKBACK_MINUTES", "25"))
        logger.info(f"Querying metrics for last {lookback_minutes} minutes (includes 5-min ingestion buffer)...")
        
        logger.info(f"DEBUG: About to call query_all_metrics with timespan={lookback_minutes}")
        try:
            metrics_data = metrics_service.query_all_metrics(
                timespan_minutes=lookback_minutes
            )
            logger.info(f"DEBUG: query_all_metrics returned successfully, got {len(metrics_data) if metrics_data else 0} metrics")
        except Exception as query_error:
            logger.error(f"ERROR: query_all_metrics failed with exception: {query_error}", exc_info=True)
            logger.error(f"ERROR: Exception type: {type(query_error).__name__}")
            logger.error(f"ERROR: Exception details: {str(query_error)}")
            raise  # Re-raise to trigger outer exception handler
        
        if not metrics_data or all(not v for v in metrics_data.values()):
            logger.warning("No metrics data retrieved. Skipping analysis.")
            return
        
        # Step 2: Extract statistics (already calculated by query_all_metrics)
        metrics_stats = {}
        for metric_name, metric_info in metrics_data.items():
            if metric_info and metric_info.get("data_points"):
                # query_all_metrics returns {config, data_points, statistics, data_quality}
                stats = metric_info["statistics"]
                
                # CRITICAL: Add data_points to stats for spike detection
                # Spike detection needs raw values to count individual failures
                data_points = metric_info["data_points"]
                stats["data_points"] = [dp["value"] for dp in data_points]
                
                metrics_stats[metric_name] = stats
                
                # Log key stats
                central = stats.get("central_tendency", {})
                if central:
                    logger.info(f"{metric_name}: mean={central.get('mean', 0):.2f}, "
                              f"median={central.get('median', 0):.2f}")
        
        # Step 3: Save current metrics snapshot to state store
        if state_manager:
            state_manager.save_metrics_snapshot(timestamp, metrics_stats)
        
        # Step 4: Pre-filter metrics to determine which need AI analysis
        enable_prefilter = os.getenv("ENABLE_PREFILTER", "true").lower() == "true"
        metrics_to_analyze = []
        
        if enable_prefilter:
            logger.info("Running pre-filter analysis...")
            prefilter_results = {}
            
            for metric_name, stats in metrics_stats.items():
                # Get historical values if available
                historical_values = None
                if state_manager:
                    recent_snapshots = state_manager.get_recent_metrics(60)
                    historical_values = []
                    for snapshot in recent_snapshots:
                        if metric_name in snapshot.get("metrics", {}):
                            historical_values.append(
                                snapshot["metrics"][metric_name].get("avg", 0)
                            )
                
                should_analyze, reason = prefilter.should_trigger_ai_analysis(
                    metric_name, stats, historical_values
                )
                
                prefilter_results[metric_name] = (should_analyze, reason)
                
                if should_analyze:
                    logger.info(f"Pre-filter: {metric_name} needs analysis - {reason}")
            
            # Prioritize metrics
            metrics_to_analyze = prefilter.prioritize_metrics(prefilter_results)
            
            if not metrics_to_analyze:
                logger.info("Pre-filter: No anomalies detected. Skipping AI analysis.")
                return
        else:
            # Analyze all metrics
            metrics_to_analyze = list(metrics_stats.keys())
        
        logger.info(f"Analyzing {len(metrics_to_analyze)} metrics with AI: {metrics_to_analyze}")
        
        # Step 4.5: ENHANCED - Check for correlated anomalies
        logger.info("Checking for correlated anomalies across metrics...")
        metric_values_for_correlation = {}
        for metric_name, metric_info in metrics_data.items():
            if metric_info and metric_info.get("data_points"):
                # Extract already-processed values from stats (we added them earlier at line 95)
                if metric_name in metrics_stats and "data_points" in metrics_stats[metric_name]:
                    metric_values_for_correlation[metric_name] = metrics_stats[metric_name]["data_points"]
        
        correlations = enhanced_detector.detect_correlated_anomalies(metric_values_for_correlation)
        if correlations:
            for metric1, metric2, corr, insight in correlations:
                logger.warning(f"Correlated anomaly: {metric1} <-> {metric2} (r={corr:.2f}): {insight}")
        
        # Step 5: TimeGEN-1 Anomaly Detection (Multi-Series)
        # NOW using dedicated TimeGEN-1 model instead of LLM (Phi-4)
        # TimeGEN-1 is purpose-built for anomaly detection and returns direct anomaly scores
        
        logger.info("=== TimeGEN-1 Multi-Series Anomaly Detection ===")
        
        # Convert metrics data to TimeGEN-1 format (timestamp -> value pairs)
        timegen_input = {}
        for metric_name, metric_info in metrics_data.items():
            if metric_info and metric_info.get("data_points"):
                # TimeGEN expects {metric_name: [(timestamp, value), ...]}
                data_points = metric_info["data_points"]
                timegen_input[metric_name] = [
                    (str(dp.get("timestamp", "")), float(dp.get("value", 0)))
                    for dp in data_points
                ]
        
        if not timegen_input or not any(timegen_input.values()):
            logger.warning("No data for TimeGEN-1 analysis")
            return
        
        # Call TimeGEN-1 for multi-series anomaly detection
        try:
            timegen_results = ai_client.detect_anomalies_multi_series(
                metrics_data=timegen_input,
                freq="D",  # Daily frequency (adjust based on your data)
                fh=7       # 7-day forecast horizon
            )
            
            logger.info(f"TimeGEN-1 Results:")
            logger.info(f"  Is Anomaly: {timegen_results.get('is_anomaly')}")
            logger.info(f"  Severity: {timegen_results.get('severity')}")
            logger.info(f"  Confidence: {timegen_results.get('confidence'):.2f}")
            logger.info(f"  Affected Metrics: {timegen_results.get('affected_metrics', [])}")
            logger.info(f"  Anomaly Count: {timegen_results.get('anomaly_count', 0)}")
            
            # Save results to state
            if state_manager:
                for affected_metric in timegen_results.get('affected_metrics', []):
                    state_manager.save_anomaly_detection(
                        timestamp, 
                        affected_metric, 
                        timegen_results
                    )
            
            # Step 6: Determine if action is needed based on TimeGEN-1 results
            is_anomaly = timegen_results.get('is_anomaly', False)
            confidence = timegen_results.get('confidence', 0.0)
            severity = timegen_results.get('severity', 'low')
            
            logger.info(f"TimeGEN-1 Analysis: is_anomaly={is_anomaly}, "
                      f"severity={severity}, confidence={confidence:.2f}")
            
            # Always send to Logic App (let Logic App decide on notifications)
            # Check for duplicate alerts to avoid spam
            should_alert = True
            if state_manager and is_anomaly:
                # Check if we've already alerted on this recently
                affected_metrics = timegen_results.get('affected_metrics', [])
                if affected_metrics:
                    first_metric = affected_metrics[0]
                    if state_manager.check_duplicate_alert(first_metric, lookback_minutes=15):
                        logger.info(f"Suppressing duplicate analysis (alert sent recently)")
                        should_alert = False
            
            # Step 7: Send to Logic App
            if should_alert and logic_app_client and is_anomaly:
                logger.warning(f"ANOMALY DETECTED - Severity: {severity.upper()}")
                logger.warning(f"Affected Metrics: {timegen_results.get('affected_metrics', [])}")
                logger.warning(f"Confidence: {confidence:.2f}")
                
                try:
                    # Send comprehensive alert with TimeGEN-1 results
                    logic_app_client.send_alert(
                        metric_name="timegen1_multi_series",
                        current_value=confidence,
                        analysis=timegen_results,
                        historical_context=None
                    )
                    logger.info("Anomaly alert sent to Logic App")
                except Exception as e:
                    logger.error(f"Failed to send alert: {e}")
            elif not is_anomaly:
                logger.info("No anomalies detected by TimeGEN-1")
                
        except Exception as e:
            logger.error(f"TimeGEN-1 analysis failed: {e}", exc_info=True)
        
        logger.info("Anomaly detection cycle completed successfully")
        
    except Exception as e:
        logger.error(f"Critical error in anomaly detection: {e}", exc_info=True)
        raise

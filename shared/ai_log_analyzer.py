"""
AI-Powered Log Analysis Module
Integrates Application Log Anomalies with Azure AI Foundry for intelligent root cause analysis.

This module:
1. Takes detected log anomalies
2. Sends them to Phi-4 model for analysis
3. Returns structured recommendations
4. Provides actionable insights for operations team
"""

import os
import json
import logging
from typing import Dict, List, Optional
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

logger = logging.getLogger(__name__)


class AILogAnalyzer:
    """
    Uses Azure AI Foundry (Phi-4) to analyze application log anomalies
    and provide intelligent root cause analysis and recommendations.
    """
    
    SYSTEM_PROMPT = """You are an expert DevOps and SRE specialist analyzing application logs.
Your task: Analyze detected log anomalies and provide root cause analysis.
Response format (JSON only):
{
  "rootCause": "brief explanation",
  "severity": "low|medium|high|critical",
  "immediateActions": ["action1", "action2"],
  "preventionStrategies": ["strategy1", "strategy2"],
  "estimatedImpact": "brief description of potential business impact",
  "confidenceScore": 0.0-1.0,
  "relatedSystems": ["system1", "system2"]
}"""
    
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        model_name: str = "Phi-4-reasoning-2",
        timeout: int = 30
    ):
        """Initialize AI Log Analyzer"""
        # Extract base endpoint
        if "/models/chat/completions" in endpoint:
            base_endpoint = endpoint.split("/chat/completions")[0]
        elif endpoint.endswith("/models"):
            base_endpoint = endpoint
        else:
            base_endpoint = f"{endpoint.rstrip('/')}/models"
        
        self.client = ChatCompletionsClient(
            endpoint=base_endpoint,
            credential=AzureKeyCredential(api_key),
            api_version="2024-05-01-preview"
        )
        self.model_name = model_name
        self.timeout = timeout
        
        logger.info(f"AILogAnalyzer initialized with endpoint: {base_endpoint}, model: {model_name}")
    
    def analyze_log_anomalies(
        self,
        anomalies: List[Dict],
        error_summary: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze log anomalies using AI Foundry
        
        Args:
            anomalies: List of detected log anomalies
            error_summary: Error statistics summary
            context: Additional context (metric anomalies, system state, etc.)
            
        Returns:
            Structured AI analysis with root causes and recommendations
        """
        if not anomalies:
            return {
                "status": "no_anomalies",
                "message": "No significant log anomalies detected"
            }
        
        try:
            # Build user prompt
            user_prompt = self._build_analysis_prompt(anomalies, error_summary, context)
            
            logger.info(f"Sending {len(anomalies)} log anomalies to AI for analysis")
            
            # Call AI model
            response = self.client.complete(
                messages=[
                    SystemMessage(content=self.SYSTEM_PROMPT),
                    UserMessage(content=user_prompt)
                ],
                model=self.model_name,
                temperature=0.3,
                max_tokens=500
            )
            
            # Extract response
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                
                # Extract JSON from response
                json_content = self._extract_json(content)
                
                if json_content:
                    analysis = json.loads(json_content)
                    
                    logger.info(f"AI Analysis complete: rootCause={analysis.get('rootCause', 'unknown')}, "
                              f"severity={analysis.get('severity', 'unknown')}")
                    
                    return {
                        "status": "success",
                        "analysis": analysis,
                        "anomaly_count": len(anomalies),
                        "timestamp": json.dumps({"datetime": str(__import__("datetime").datetime.utcnow())})
                    }
                else:
                    logger.error("Could not extract JSON from AI response")
                    return self._get_fallback_analysis(anomalies)
            else:
                logger.error("No response from AI model")
                return self._get_fallback_analysis(anomalies)
                
        except Exception as e:
            logger.error(f"Error analyzing log anomalies: {e}", exc_info=True)
            return self._get_fallback_analysis(anomalies)
    
    def _build_analysis_prompt(
        self,
        anomalies: List[Dict],
        error_summary: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> str:
        """Build compact analysis prompt for AI"""
        parts = ["Analyze these log anomalies:\n"]
        
        # Add top anomalies
        for i, anomaly in enumerate(anomalies[:5], 1):
            parts.append(f"{i}. {anomaly.get('error_type', 'Unknown')} "
                        f"(count={anomaly.get('count', 0)}, "
                        f"severity={anomaly.get('severity', 'low')}, "
                        f"confidence={anomaly.get('confidence', 0):.1%})")
            
            if anomaly.get("patterns"):
                parts.append(f"   Patterns: {', '.join(anomaly['patterns'][:2])}")
        
        # Add error summary if available
        if error_summary:
            parts.append(f"\nError Summary:")
            parts.append(f"- Total errors: {error_summary.get('total_errors', 0)}")
            parts.append(f"- Error rate: {error_summary.get('error_rate', 0):.1%}")
            
            if error_summary.get("by_category"):
                categories = error_summary["by_category"]
                parts.append(f"- Top categories: {', '.join(list(categories.keys())[:3])}")
        
        # Add context if available
        if context:
            if context.get("metric_anomalies"):
                parts.append(f"\nCorrelated metric anomalies: {', '.join(context['metric_anomalies'][:3])}")
            
            if context.get("recent_deployments"):
                parts.append(f"Recent deployments: {', '.join(context['recent_deployments'][:2])}")
        
        parts.append("\nProvide JSON analysis with root cause, actions, and prevention strategies.")
        
        return "\n".join(parts)
    
    def _extract_json(self, content: str) -> Optional[str]:
        """Extract JSON from AI response"""
        import re
        
        if not content:
            return None
        
        # Remove <think> tags if present
        cleaned = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        
        if cleaned and cleaned.startswith('{'):
            return cleaned
        
        # Find JSON by bracket matching
        start = content.find('{')
        if start != -1:
            brace_count = 0
            for i in range(start, len(content)):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        return content[start:i+1]
        
        return None
    
    def _get_fallback_analysis(self, anomalies: List[Dict]) -> Dict:
        """Return fallback analysis if AI fails"""
        # Auto-detect severity from anomalies
        severity = "low"
        if any(a.get("severity") == "critical" for a in anomalies):
            severity = "critical"
        elif any(a.get("severity") == "high" for a in anomalies):
            severity = "high"
        
        total_count = sum(a.get("count", 0) for a in anomalies)
        
        return {
            "status": "fallback",
            "analysis": {
                "rootCause": f"Multiple errors detected: {', '.join([a.get('error_type', 'Unknown')[:30] for a in anomalies[:3]])}",
                "severity": severity,
                "immediateActions": [
                    "Check application logs for error context",
                    "Verify application health metrics",
                    "Review recent deployments"
                ],
                "preventionStrategies": [
                    "Implement error rate monitoring",
                    "Add application-level health checks",
                    "Configure automatic alerts for error spikes"
                ],
                "estimatedImpact": f"Potential service degradation with {total_count} errors detected",
                "confidenceScore": 0.5,
                "relatedSystems": ["application-logs", "error-tracking", "monitoring"]
            },
            "anomaly_count": len(anomalies),
            "note": "AI analysis unavailable, using fallback analysis"
        }


class LogAnomalyContext:
    """
    Context manager for log anomaly analysis across multiple sources.
    Correlates log anomalies with metric anomalies and system state.
    """
    
    def __init__(self, ai_analyzer: Optional[AILogAnalyzer] = None):
        """Initialize context manager"""
        self.ai_analyzer = ai_analyzer
        self.log_anomalies = []
        self.metric_anomalies = []
        self.system_context = {}
    
    def add_log_anomalies(self, anomalies: List[Dict]) -> None:
        """Add detected log anomalies"""
        self.log_anomalies.extend(anomalies)
        logger.info(f"Added {len(anomalies)} log anomalies to context")
    
    def add_metric_anomalies(self, anomalies: List[str]) -> None:
        """Add metric anomalies for correlation"""
        self.metric_anomalies.extend(anomalies)
        logger.info(f"Added {len(anomalies)} metric anomalies to context")
    
    def add_system_context(self, context: Dict) -> None:
        """Add system context (deployments, config changes, etc.)"""
        self.system_context.update(context)
        logger.info(f"Updated system context: {', '.join(context.keys())}")
    
    def get_correlated_analysis(self, error_summary: Optional[Dict] = None) -> Dict:
        """
        Get full correlated analysis across logs and metrics
        
        Returns:
            Comprehensive analysis with correlations
        """
        if not self.log_anomalies:
            return {"status": "no_anomalies"}
        
        # Correlate with metrics
        context = {}
        if self.metric_anomalies:
            context["metric_anomalies"] = self.metric_anomalies
        
        if self.system_context:
            context.update(self.system_context)
        
        # Get AI analysis if available
        if self.ai_analyzer:
            return self.ai_analyzer.analyze_log_anomalies(
                self.log_anomalies,
                error_summary=error_summary,
                context=context if context else None
            )
        else:
            return {
                "status": "analysis_pending",
                "log_anomalies": self.log_anomalies,
                "context": context
            }
    
    def reset(self) -> None:
        """Reset context for next analysis cycle"""
        self.log_anomalies = []
        self.metric_anomalies = []
        self.system_context = {}


def create_ai_log_analyzer(
    endpoint: Optional[str] = None,
    api_key: Optional[str] = None
) -> Optional[AILogAnalyzer]:
    """Factory function to create AI Log Analyzer from environment"""
    endpoint = endpoint or os.getenv("AI_FOUNDATION_ENDPOINT")
    api_key = api_key or os.getenv("AI_FOUNDATION_KEY")
    model_name = os.getenv("AI_FOUNDATION_MODEL", "Phi-4-reasoning-2")
    
    if not endpoint or not api_key:
        logger.warning("AI_FOUNDATION_ENDPOINT or AI_FOUNDATION_KEY not set - log analysis disabled")
        return None
    
    logger.info("Creating AILogAnalyzer")
    return AILogAnalyzer(endpoint, api_key, model_name)

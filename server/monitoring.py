import logging
import time
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)

# Prometheus metrics
AUDIO_CHUNKS_PROCESSED = Counter('audio_chunks_total', 'Total audio chunks processed')
SCAM_DETECTIONS = Counter('scam_detections_total', 'Total scam detections', ['risk_level'])
VOICE_SPOOFING_DETECTIONS = Counter('voice_spoofing_total', 'Total voice spoofing detections')
PROCESSING_TIME = Histogram('processing_time_seconds', 'Audio processing time', ['component'])
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Number of active WebSocket connections')
TTS_ALERTS_GENERATED = Counter('tts_alerts_total', 'Total TTS alerts generated', ['language'])
API_REQUESTS = Counter('api_requests_total', 'Total API requests', ['endpoint', 'method'])
ERRORS = Counter('errors_total', 'Total errors', ['component', 'error_type'])

class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.connection_count = 0
        
        # Start Prometheus metrics server
        try:
            start_http_server(8001)  # Metrics available at http://localhost:8001/metrics
            logger.info("Prometheus metrics server started on port 8001")
        except Exception as e:
            logger.warning(f"Could not start metrics server: {e}")

    def track_connection(self, connected: bool):
        """Track WebSocket connections"""
        if connected:
            self.connection_count += 1
            ACTIVE_CONNECTIONS.set(self.connection_count)
        else:
            self.connection_count = max(0, self.connection_count - 1)
            ACTIVE_CONNECTIONS.set(self.connection_count)

    def track_audio_chunk(self):
        """Track processed audio chunk"""
        AUDIO_CHUNKS_PROCESSED.inc()

    def track_scam_detection(self, risk_level: str):
        """Track scam detection"""
        SCAM_DETECTIONS.labels(risk_level=risk_level).inc()

    def track_voice_spoofing(self):
        """Track voice spoofing detection"""
        VOICE_SPOOFING_DETECTIONS.inc()

    def track_tts_alert(self, language: str):
        """Track TTS alert generation"""
        TTS_ALERTS_GENERATED.labels(language=language).inc()

    def track_api_request(self, endpoint: str, method: str):
        """Track API request"""
        API_REQUESTS.labels(endpoint=endpoint, method=method).inc()

    def track_error(self, component: str, error_type: str):
        """Track error occurrence"""
        ERRORS.labels(component=component, error_type=error_type).inc()

def monitor_performance(component: str):
    """Decorator to monitor function performance"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                performance_monitor.track_error(component, type(e).__name__)
                raise
            finally:
                processing_time = time.time() - start_time
                PROCESSING_TIME.labels(component=component).observe(processing_time)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                performance_monitor.track_error(component, type(e).__name__)
                raise
            finally:
                processing_time = time.time() - start_time
                PROCESSING_TIME.labels(component=component).observe(processing_time)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

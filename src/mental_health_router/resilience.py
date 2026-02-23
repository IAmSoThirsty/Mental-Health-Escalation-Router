"""
Production operational resilience components.

Implements circuit breakers, bulkheads, health checks, and graceful degradation.
"""

import time
import threading
from typing import Optional, Callable, Any, Dict, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes before closing
    timeout_seconds: int = 60  # Time before trying half-open
    window_seconds: int = 30  # Rolling window for failures


class CircuitBreaker:
    """
    Circuit breaker pattern for fault isolation.

    Prevents cascading failures by failing fast when a service is down.
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.lock = threading.Lock()

    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to call
            *args, **kwargs: Function arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpen: If circuit is open
            Exception: If function raises
        """
        with self.lock:
            # Check if should attempt call
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit {self.name}: OPEN -> HALF_OPEN")
                else:
                    raise CircuitBreakerOpen(f"Circuit {self.name} is OPEN")

        # Attempt call
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call"""
        with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    logger.info(f"Circuit {self.name}: HALF_OPEN -> CLOSED")
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0

    def _on_failure(self):
        """Handle failed call"""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                # Single failure reopens circuit
                self.state = CircuitState.OPEN
                self.success_count = 0
                logger.warning(f"Circuit {self.name}: HALF_OPEN -> OPEN")
            elif self.state == CircuitState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    self.state = CircuitState.OPEN
                    logger.error(f"Circuit {self.name}: CLOSED -> OPEN ({self.failure_count} failures)")

    def _should_attempt_reset(self) -> bool:
        """Check if should attempt recovery"""
        if self.last_failure_time is None:
            return True

        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.config.timeout_seconds


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open"""
    pass


class Bulkhead:
    """
    Bulkhead pattern for resource isolation.

    Limits concurrent executions to prevent resource exhaustion.
    """

    def __init__(self, name: str, max_concurrent: int = 10):
        self.name = name
        self.max_concurrent = max_concurrent
        self.semaphore = threading.Semaphore(max_concurrent)
        self.active_count = 0
        self.lock = threading.Lock()

    def execute(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute function within bulkhead constraints.

        Args:
            func: Function to call
            *args, **kwargs: Function arguments

        Returns:
            Function result

        Raises:
            BulkheadFull: If bulkhead capacity exceeded
        """
        acquired = self.semaphore.acquire(blocking=False)
        if not acquired:
            raise BulkheadFull(f"Bulkhead {self.name} at capacity ({self.max_concurrent})")

        try:
            with self.lock:
                self.active_count += 1

            return func(*args, **kwargs)
        finally:
            with self.lock:
                self.active_count -= 1
            self.semaphore.release()

    def get_active_count(self) -> int:
        """Get current number of active executions"""
        with self.lock:
            return self.active_count


class BulkheadFull(Exception):
    """Raised when bulkhead is at capacity"""
    pass


class HealthStatus(Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheck:
    """Individual health check result"""
    name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    latency_ms: float


class HealthMonitor:
    """
    Health and readiness monitoring.

    Tracks component health for load balancer decisions.
    """

    def __init__(self):
        self.checks: Dict[str, Callable[[], HealthCheck]] = {}
        self.last_results: Dict[str, HealthCheck] = {}

    def register_check(self, name: str, check_func: Callable[[], bool]):
        """
        Register a health check.

        Args:
            name: Check name
            check_func: Function returning True if healthy
        """
        def wrapped_check() -> HealthCheck:
            start = time.time()
            try:
                is_healthy = check_func()
                latency = (time.time() - start) * 1000

                return HealthCheck(
                    name=name,
                    status=HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY,
                    message="OK" if is_healthy else "Check failed",
                    timestamp=datetime.now(),
                    latency_ms=latency
                )
            except Exception as e:
                latency = (time.time() - start) * 1000
                return HealthCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Error: {str(e)}",
                    timestamp=datetime.now(),
                    latency_ms=latency
                )

        self.checks[name] = wrapped_check

    def check_health(self) -> Dict[str, HealthCheck]:
        """
        Run all health checks.

        Returns:
            Dictionary of check results
        """
        results = {}
        for name, check_func in self.checks.items():
            result = check_func()
            results[name] = result
            self.last_results[name] = result

        return results

    def is_healthy(self) -> bool:
        """Check if system is healthy (all checks pass)"""
        results = self.check_health()
        return all(r.status == HealthStatus.HEALTHY for r in results.values())

    def is_ready(self) -> bool:
        """Check if system is ready (critical checks pass)"""
        # Same as healthy for now, can be customized
        return self.is_healthy()


class GracefulDegradation:
    """
    Graceful degradation manager.

    Allows system to continue operating with reduced functionality.
    """

    def __init__(self):
        self.degraded_features: Dict[str, str] = {}  # feature -> reason
        self.fallback_handlers: Dict[str, Callable] = {}

    def mark_degraded(self, feature: str, reason: str):
        """Mark a feature as degraded"""
        self.degraded_features[feature] = reason
        logger.warning(f"Feature degraded: {feature} - {reason}")

    def mark_restored(self, feature: str):
        """Mark a feature as restored"""
        if feature in self.degraded_features:
            del self.degraded_features[feature]
            logger.info(f"Feature restored: {feature}")

    def is_degraded(self, feature: str) -> bool:
        """Check if feature is degraded"""
        return feature in self.degraded_features

    def register_fallback(self, feature: str, handler: Callable):
        """Register fallback handler for a feature"""
        self.fallback_handlers[feature] = handler

    def execute_with_fallback(
        self,
        feature: str,
        primary: Callable,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """
        Execute primary function or fallback if degraded.

        Args:
            feature: Feature name
            primary: Primary function
            *args, **kwargs: Function arguments

        Returns:
            Result from primary or fallback
        """
        if self.is_degraded(feature) and feature in self.fallback_handlers:
            logger.info(f"Using fallback for degraded feature: {feature}")
            return self.fallback_handlers[feature](*args, **kwargs)

        return primary(*args, **kwargs)


class BackpressureManager:
    """
    Backpressure management for flow control.

    Prevents overwhelming downstream systems.
    """

    def __init__(self, max_queue_size: int = 1000):
        self.max_queue_size = max_queue_size
        self.queue_size = 0
        self.lock = threading.Lock()
        self.rejected_count = 0

    def try_acquire(self) -> bool:
        """
        Try to acquire capacity.

        Returns:
            True if capacity available, False if backpressure applied
        """
        with self.lock:
            if self.queue_size >= self.max_queue_size:
                self.rejected_count += 1
                logger.warning(f"Backpressure applied: queue full ({self.queue_size}/{self.max_queue_size})")
                return False

            self.queue_size += 1
            return True

    def release(self):
        """Release capacity"""
        with self.lock:
            self.queue_size = max(0, self.queue_size - 1)

    def get_load_factor(self) -> float:
        """Get current load factor (0.0 - 1.0)"""
        with self.lock:
            return self.queue_size / self.max_queue_size


class MetricsCollector:
    """
    Production metrics collection.

    Tracks operational metrics for monitoring and alerting.
    """

    def __init__(self):
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = {}
        self.lock = threading.Lock()

    def increment_counter(self, name: str, value: int = 1):
        """Increment a counter metric"""
        with self.lock:
            self.counters[name] = self.counters.get(name, 0) + value

    def set_gauge(self, name: str, value: float):
        """Set a gauge metric"""
        with self.lock:
            self.gauges[name] = value

    def record_histogram(self, name: str, value: float):
        """Record a histogram value"""
        with self.lock:
            if name not in self.histograms:
                self.histograms[name] = []
            self.histograms[name].append(value)

            # Keep only recent values (last 1000)
            if len(self.histograms[name]) > 1000:
                self.histograms[name] = self.histograms[name][-1000:]

    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        with self.lock:
            return {
                'counters': self.counters.copy(),
                'gauges': self.gauges.copy(),
                'histograms': {
                    name: self._compute_histogram_stats(values)
                    for name, values in self.histograms.items()
                }
            }

    def _compute_histogram_stats(self, values: List[float]) -> Dict[str, float]:
        """Compute histogram statistics"""
        if not values:
            return {'count': 0, 'min': 0, 'max': 0, 'avg': 0, 'p50': 0, 'p95': 0, 'p99': 0}

        sorted_values = sorted(values)
        n = len(sorted_values)

        return {
            'count': n,
            'min': sorted_values[0],
            'max': sorted_values[-1],
            'avg': sum(sorted_values) / n,
            'p50': sorted_values[int(n * 0.5)],
            'p95': sorted_values[int(n * 0.95)],
            'p99': sorted_values[int(n * 0.99)],
        }


# Global instances for singleton pattern
_health_monitor = HealthMonitor()
_metrics_collector = MetricsCollector()
_degradation_manager = GracefulDegradation()


def get_health_monitor() -> HealthMonitor:
    """Get global health monitor instance"""
    return _health_monitor


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance"""
    return _metrics_collector


def get_degradation_manager() -> GracefulDegradation:
    """Get global degradation manager instance"""
    return _degradation_manager

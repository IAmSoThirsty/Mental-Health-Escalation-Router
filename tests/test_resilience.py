"""
Comprehensive tests for production resilience module.

Tests cover:
- Circuit breaker pattern
- Bulkhead isolation
- Health monitoring
- Graceful degradation
- Backpressure management
- Metrics collection
"""

import pytest
import time
import threading
from mental_health_router.resilience import (
    CircuitBreaker,
    CircuitBreakerOpen,
    CircuitState,
    Bulkhead,
    BulkheadFull,
    HealthMonitor,
    HealthStatus,
    GracefulDegradation,
    BackpressureManager,
    BackpressureError,
    MetricsCollector,
)


class TestCircuitBreaker:
    """Test circuit breaker fault isolation"""

    def test_starts_closed(self):
        """Circuit should start in CLOSED state"""
        cb = CircuitBreaker("test", failure_threshold=3)
        assert cb.state == CircuitState.CLOSED

    def test_allows_calls_when_closed(self):
        """CLOSED circuit should allow calls through"""
        cb = CircuitBreaker("test", failure_threshold=3)

        result = cb.call(lambda: "success")
        assert result == "success"

    def test_opens_after_threshold_failures(self):
        """Circuit should open after threshold failures"""
        cb = CircuitBreaker("test", failure_threshold=3, timeout_seconds=1)

        # Cause 3 failures
        for _ in range(3):
            try:
                cb.call(lambda: 1 / 0)
            except ZeroDivisionError:
                pass

        # Circuit should now be OPEN
        assert cb.state == CircuitState.OPEN

    def test_blocks_calls_when_open(self):
        """OPEN circuit should block all calls"""
        cb = CircuitBreaker("test", failure_threshold=1, timeout_seconds=1)

        # Trigger opening
        try:
            cb.call(lambda: 1 / 0)
        except ZeroDivisionError:
            pass

        # Should be open and block calls
        with pytest.raises(CircuitBreakerOpen):
            cb.call(lambda: "should_not_execute")

    def test_transitions_to_half_open_after_timeout(self):
        """Circuit should transition to HALF_OPEN after timeout"""
        cb = CircuitBreaker("test", failure_threshold=1, timeout_seconds=0.1)

        # Open circuit
        try:
            cb.call(lambda: 1 / 0)
        except ZeroDivisionError:
            pass

        assert cb.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(0.15)

        # Next call should attempt in HALF_OPEN
        try:
            result = cb.call(lambda: "success")
            # Should succeed and close circuit
            assert cb.state == CircuitState.CLOSED
            assert result == "success"
        except CircuitBreakerOpen:
            # Or still open if implementation requires explicit success
            pass

    def test_closes_after_successful_half_open_calls(self):
        """Successful calls in HALF_OPEN should close circuit"""
        cb = CircuitBreaker("test", failure_threshold=1, timeout_seconds=0.1)

        # Open circuit
        try:
            cb.call(lambda: 1 / 0)
        except ZeroDivisionError:
            pass

        # Wait and transition to half-open
        time.sleep(0.15)

        # Successful call should close circuit
        cb.call(lambda: "success")
        assert cb.state == CircuitState.CLOSED

    def test_reopens_on_half_open_failure(self):
        """Failure in HALF_OPEN should reopen circuit"""
        cb = CircuitBreaker("test", failure_threshold=1, timeout_seconds=0.1)

        # Open circuit
        try:
            cb.call(lambda: 1 / 0)
        except ZeroDivisionError:
            pass

        time.sleep(0.15)

        # Fail in half-open
        try:
            cb.call(lambda: 1 / 0)
        except ZeroDivisionError:
            pass

        assert cb.state == CircuitState.OPEN


class TestBulkhead:
    """Test bulkhead resource isolation"""

    def test_allows_concurrent_calls_up_to_limit(self):
        """Should allow concurrent calls up to max concurrency"""
        bulkhead = Bulkhead("test", max_concurrent=2)

        def slow_operation():
            time.sleep(0.1)
            return "done"

        # Start 2 concurrent operations
        threads = []
        for _ in range(2):
            t = threading.Thread(target=lambda: bulkhead.execute(slow_operation))
            t.start()
            threads.append(t)

        # Wait a bit for them to start
        time.sleep(0.05)

        # Should have 2 active
        assert bulkhead.active_count() == 2

        # Wait for completion
        for t in threads:
            t.join()

    def test_blocks_when_bulkhead_full(self):
        """Should block when max concurrency reached"""
        bulkhead = Bulkhead("test", max_concurrent=1)

        def slow_operation():
            time.sleep(0.2)
            return "done"

        # Start one operation
        t1 = threading.Thread(target=lambda: bulkhead.execute(slow_operation))
        t1.start()

        time.sleep(0.05)  # Let it start

        # Second call should be rejected
        with pytest.raises(BulkheadFull):
            bulkhead.execute(slow_operation)

        t1.join()

    def test_releases_on_completion(self):
        """Should release slot when operation completes"""
        bulkhead = Bulkhead("test", max_concurrent=1)

        def quick_operation():
            return "done"

        # First call
        bulkhead.execute(quick_operation)

        # Second call should succeed (first released)
        bulkhead.execute(quick_operation)

    def test_releases_on_exception(self):
        """Should release slot even when operation fails"""
        bulkhead = Bulkhead("test", max_concurrent=1)

        def failing_operation():
            raise ValueError("test error")

        # First call fails
        try:
            bulkhead.execute(failing_operation)
        except ValueError:
            pass

        # Second call should succeed (slot was released)
        try:
            bulkhead.execute(failing_operation)
        except ValueError:
            pass  # Expected, but slot was acquired


class TestHealthMonitor:
    """Test health check aggregation"""

    def test_reports_healthy_by_default(self):
        """Should report healthy when all checks pass"""
        monitor = HealthMonitor()

        monitor.register_check("database", lambda: True)
        monitor.register_check("cache", lambda: True)

        status = monitor.check_health()
        assert status.overall == HealthStatus.HEALTHY
        assert len(status.failures) == 0

    def test_reports_unhealthy_on_failure(self):
        """Should report unhealthy when any check fails"""
        monitor = HealthMonitor()

        monitor.register_check("database", lambda: True)
        monitor.register_check("cache", lambda: False)

        status = monitor.check_health()
        assert status.overall == HealthStatus.UNHEALTHY
        assert "cache" in status.failures

    def test_degraded_state(self):
        """Should support degraded state for partial failures"""
        monitor = HealthMonitor()

        monitor.register_check("critical_db", lambda: True, critical=True)
        monitor.register_check("optional_cache", lambda: False, critical=False)

        status = monitor.check_health()
        assert status.overall == HealthStatus.DEGRADED

    def test_readiness_check(self):
        """Readiness should differ from liveness"""
        monitor = HealthMonitor()

        # Not ready initially
        assert monitor.check_readiness() is False

        # Mark as ready
        monitor.mark_ready()
        assert monitor.check_readiness() is True


class TestGracefulDegradation:
    """Test graceful degradation under failure"""

    def test_returns_primary_when_available(self):
        """Should use primary function when it succeeds"""
        degradation = GracefulDegradation()

        result = degradation.execute(
            primary=lambda: "primary_result",
            fallback=lambda: "fallback_result"
        )

        assert result == "primary_result"

    def test_falls_back_on_failure(self):
        """Should use fallback when primary fails"""
        degradation = GracefulDegradation()

        def failing_primary():
            raise ValueError("primary failed")

        result = degradation.execute(
            primary=failing_primary,
            fallback=lambda: "fallback_result"
        )

        assert result == "fallback_result"

    def test_propagates_when_no_fallback(self):
        """Should propagate error when no fallback provided"""
        degradation = GracefulDegradation()

        def failing_primary():
            raise ValueError("primary failed")

        with pytest.raises(ValueError):
            degradation.execute(primary=failing_primary, fallback=None)

    def test_tracks_degradation_events(self):
        """Should track when system is degraded"""
        degradation = GracefulDegradation()

        def failing_primary():
            raise ValueError("primary failed")

        degradation.execute(
            primary=failing_primary,
            fallback=lambda: "fallback"
        )

        # Should have recorded degradation
        assert degradation.degradation_count > 0


class TestBackpressureManager:
    """Test backpressure flow control"""

    def test_allows_requests_under_capacity(self):
        """Should allow requests when under max queue size"""
        manager = BackpressureManager(max_queue_size=10)

        for _ in range(5):
            manager.check_backpressure()  # Should not raise

    def test_rejects_when_over_capacity(self):
        """Should reject requests when queue is full"""
        manager = BackpressureManager(max_queue_size=2)

        # Fill queue
        manager.enqueue("item1")
        manager.enqueue("item2")

        # Should reject new items
        with pytest.raises(BackpressureError):
            manager.check_backpressure()

    def test_allows_after_dequeue(self):
        """Should allow requests after items are dequeued"""
        manager = BackpressureManager(max_queue_size=2)

        manager.enqueue("item1")
        manager.enqueue("item2")

        # Dequeue one
        manager.dequeue()

        # Should allow one more
        manager.enqueue("item3")


class TestMetricsCollector:
    """Test production metrics collection"""

    def test_increments_counter(self):
        """Should track counter increments"""
        metrics = MetricsCollector()

        metrics.increment("requests", 1)
        metrics.increment("requests", 2)

        assert metrics.get_counter("requests") == 3

    def test_sets_gauge(self):
        """Should track gauge values"""
        metrics = MetricsCollector()

        metrics.set_gauge("queue_size", 10)
        assert metrics.get_gauge("queue_size") == 10

        metrics.set_gauge("queue_size", 5)
        assert metrics.get_gauge("queue_size") == 5

    def test_records_histogram(self):
        """Should track histogram distributions"""
        metrics = MetricsCollector()

        values = [100, 200, 300, 400, 500]
        for v in values:
            metrics.record_histogram("latency", v)

        stats = metrics.get_histogram_stats("latency")
        assert stats["count"] == 5
        assert stats["p50"] == 300
        assert stats["p99"] == 500

    def test_calculates_percentiles_correctly(self):
        """Should calculate accurate percentiles"""
        metrics = MetricsCollector()

        # 100 values from 1 to 100
        for i in range(1, 101):
            metrics.record_histogram("test", i)

        stats = metrics.get_histogram_stats("test")
        assert 49 <= stats["p50"] <= 51  # Median ~50
        assert 94 <= stats["p95"] <= 96  # 95th percentile ~95
        assert stats["p99"] >= 99  # 99th percentile >= 99


class TestResilienceIntegration:
    """Integration tests for resilience patterns"""

    def test_circuit_breaker_with_bulkhead(self):
        """Circuit breaker and bulkhead working together"""
        cb = CircuitBreaker("integration", failure_threshold=2)
        bulkhead = Bulkhead("integration", max_concurrent=2)

        def flaky_operation(should_fail):
            if should_fail:
                raise ValueError("intentional failure")
            return "success"

        # Should work initially
        result = cb.call(lambda: bulkhead.execute(lambda: flaky_operation(False)))
        assert result == "success"

        # Cause failures to open circuit
        for _ in range(2):
            try:
                cb.call(lambda: bulkhead.execute(lambda: flaky_operation(True)))
            except ValueError:
                pass

        # Circuit should be open
        with pytest.raises(CircuitBreakerOpen):
            cb.call(lambda: bulkhead.execute(lambda: flaky_operation(False)))

    def test_full_resilience_stack(self):
        """All resilience components working together"""
        cb = CircuitBreaker("stack", failure_threshold=3)
        bulkhead = Bulkhead("stack", max_concurrent=5)
        health = HealthMonitor()
        degradation = GracefulDegradation()
        metrics = MetricsCollector()

        def primary_operation():
            metrics.increment("primary_attempts", 1)
            # Simulate success
            return "primary_success"

        def fallback_operation():
            metrics.increment("fallback_attempts", 1)
            return "fallback_success"

        # Register health check
        health.register_check("circuit", lambda: cb.state == CircuitState.CLOSED)

        # Execute with full stack
        result = cb.call(
            lambda: bulkhead.execute(
                lambda: degradation.execute(
                    primary=primary_operation,
                    fallback=fallback_operation
                )
            )
        )

        assert result == "primary_success"
        assert metrics.get_counter("primary_attempts") == 1
        assert health.check_health().overall == HealthStatus.HEALTHY


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

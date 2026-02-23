"""
Production configuration management with validation and hot-reload.
"""

import os
import json
import threading
from typing import Any, Dict, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Deployment environment"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class InferenceConfig:
    """Inference engine configuration"""
    max_latency_ms: float = 1000.0
    timeout_multiplier: float = 1.5
    fail_safe_on_timeout: bool = True
    enable_caching: bool = True
    cache_ttl_seconds: int = 300


@dataclass
class SecurityConfig:
    """Security configuration"""
    enable_rate_limiting: bool = True
    rate_limit_per_second: float = 10.0
    rate_limit_burst: int = 20
    enable_request_signing: bool = True
    enable_abuse_detection: bool = True
    max_input_length: int = 10000


@dataclass
class RiskConfig:
    """Risk classification configuration"""
    critical_threshold: float = 0.7
    high_threshold: float = 0.5
    moderate_threshold: float = 0.3
    always_human_for_critical: bool = True
    uncertainty_elevation_threshold: float = 0.5


@dataclass
class EscalationConfig:
    """Escalation policy configuration"""
    critical_timeout_seconds: int = 60
    high_timeout_seconds: int = 300
    moderate_timeout_seconds: int = 1800
    enable_critical_tier_validation: bool = True


@dataclass
class ResilienceConfig:
    """Operational resilience configuration"""
    enable_circuit_breakers: bool = True
    circuit_failure_threshold: int = 5
    circuit_timeout_seconds: int = 60
    enable_bulkheads: bool = True
    max_concurrent_requests: int = 100
    enable_backpressure: bool = True
    max_queue_size: int = 1000


@dataclass
class AuditConfig:
    """Audit and compliance configuration"""
    enable_audit_chain: bool = True
    enable_distributed_tracing: bool = True
    retention_days: int = 90
    auto_scrub_pii: bool = True


@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    enable_metrics: bool = True
    enable_health_checks: bool = True
    health_check_interval_seconds: int = 30
    metrics_export_interval_seconds: int = 60


@dataclass
class ProductionConfig:
    """Master production configuration"""
    environment: Environment = Environment.DEVELOPMENT
    version: str = "0.1.0"

    inference: InferenceConfig = field(default_factory=InferenceConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    escalation: EscalationConfig = field(default_factory=EscalationConfig)
    resilience: ResilienceConfig = field(default_factory=ResilienceConfig)
    audit: AuditConfig = field(default_factory=AuditConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    # Feature flags
    feature_flags: Dict[str, bool] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """
        Validate configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Inference validation
        if self.inference.max_latency_ms <= 0:
            errors.append("inference.max_latency_ms must be > 0")

        # Security validation
        if self.security.rate_limit_per_second <= 0:
            errors.append("security.rate_limit_per_second must be > 0")
        if self.security.max_input_length <= 0:
            errors.append("security.max_input_length must be > 0")

        # Risk validation
        if not (0 <= self.risk.critical_threshold <= 1):
            errors.append("risk.critical_threshold must be in [0, 1]")
        if not (0 <= self.risk.high_threshold <= 1):
            errors.append("risk.high_threshold must be in [0, 1]")
        if not (0 <= self.risk.moderate_threshold <= 1):
            errors.append("risk.moderate_threshold must be in [0, 1]")
        if self.risk.high_threshold > self.risk.critical_threshold:
            errors.append("risk.high_threshold must be <= critical_threshold")

        # Escalation validation
        if self.escalation.critical_timeout_seconds <= 0:
            errors.append("escalation.critical_timeout_seconds must be > 0")

        # Production-specific validations
        if self.environment == Environment.PRODUCTION:
            if not self.risk.always_human_for_critical:
                errors.append("CRITICAL: always_human_for_critical must be True in production")
            if not self.escalation.enable_critical_tier_validation:
                errors.append("CRITICAL: critical_tier_validation must be enabled in production")
            if not self.security.enable_rate_limiting:
                errors.append("WARNING: rate limiting should be enabled in production")
            if not self.audit.enable_audit_chain:
                errors.append("CRITICAL: audit chain must be enabled in production")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'environment': self.environment.value,
            'version': self.version,
            'inference': self.inference.__dict__,
            'security': self.security.__dict__,
            'risk': self.risk.__dict__,
            'escalation': self.escalation.__dict__,
            'resilience': self.resilience.__dict__,
            'audit': self.audit.__dict__,
            'monitoring': self.monitoring.__dict__,
            'feature_flags': self.feature_flags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProductionConfig':
        """Create from dictionary"""
        config = cls()
        config.environment = Environment(data.get('environment', 'development'))
        config.version = data.get('version', '0.1.0')

        if 'inference' in data:
            config.inference = InferenceConfig(**data['inference'])
        if 'security' in data:
            config.security = SecurityConfig(**data['security'])
        if 'risk' in data:
            config.risk = RiskConfig(**data['risk'])
        if 'escalation' in data:
            config.escalation = EscalationConfig(**data['escalation'])
        if 'resilience' in data:
            config.resilience = ResilienceConfig(**data['resilience'])
        if 'audit' in data:
            config.audit = AuditConfig(**data['audit'])
        if 'monitoring' in data:
            config.monitoring = MonitoringConfig(**data['monitoring'])
        if 'feature_flags' in data:
            config.feature_flags = data['feature_flags']

        return config


class ConfigManager:
    """
    Configuration manager with hot-reload and validation.
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config = ProductionConfig()
        self.lock = threading.Lock()
        self.change_listeners: List[Callable[[ProductionConfig], None]] = []

        # Load from file if provided
        if config_path and os.path.exists(config_path):
            self.reload()

    def reload(self):
        """
        Reload configuration from file.

        Raises:
            ValueError: If configuration is invalid
        """
        if not self.config_path or not os.path.exists(self.config_path):
            logger.warning("No config file found, using defaults")
            return

        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)

            new_config = ProductionConfig.from_dict(data)

            # Validate
            errors = new_config.validate()
            if errors:
                raise ValueError(f"Invalid configuration: {', '.join(errors)}")

            with self.lock:
                self.config = new_config

            # Notify listeners
            self._notify_listeners()

            logger.info(f"Configuration reloaded from {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            raise

    def save(self):
        """Save current configuration to file"""
        if not self.config_path:
            raise ValueError("No config path specified")

        with self.lock:
            data = self.config.to_dict()

        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Configuration saved to {self.config_path}")

    def get_config(self) -> ProductionConfig:
        """Get current configuration (thread-safe)"""
        with self.lock:
            return self.config

    def update_config(self, updates: Dict[str, Any]):
        """
        Update configuration dynamically.

        Args:
            updates: Configuration updates

        Raises:
            ValueError: If updated configuration is invalid
        """
        with self.lock:
            # Create updated config
            current_dict = self.config.to_dict()
            current_dict.update(updates)
            new_config = ProductionConfig.from_dict(current_dict)

            # Validate
            errors = new_config.validate()
            if errors:
                raise ValueError(f"Invalid configuration: {', '.join(errors)}")

            self.config = new_config

        # Notify listeners
        self._notify_listeners()
        logger.info(f"Configuration updated: {list(updates.keys())}")

    def register_change_listener(self, listener: Callable[[ProductionConfig], None]):
        """Register a callback for configuration changes"""
        self.change_listeners.append(listener)

    def _notify_listeners(self):
        """Notify all change listeners"""
        config = self.get_config()
        for listener in self.change_listeners:
            try:
                listener(config)
            except Exception as e:
                logger.error(f"Error in config change listener: {e}")


# Global configuration manager
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get global configuration manager"""
    global _config_manager
    if _config_manager is None:
        config_path = os.environ.get('MHER_CONFIG_PATH')
        _config_manager = ConfigManager(config_path)
    return _config_manager


def get_config() -> ProductionConfig:
    """Get current production configuration"""
    return get_config_manager().get_config()

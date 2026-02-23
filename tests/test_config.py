"""
Comprehensive tests for production configuration module.

Tests cover:
- Configuration validation
- Hot-reload capabilities
- Environment-specific constraints
- Change notification
"""

import pytest
import json
import tempfile
import os
from mental_health_router.config import (
    ProductionConfig,
    ConfigManager,
    Environment,
    InferenceConfig,
    SecurityConfig,
    RiskConfig,
    EscalationConfig,
)


class TestProductionConfig:
    """Test production configuration dataclass"""

    def test_default_config_is_valid(self):
        """Default configuration should be valid"""
        config = ProductionConfig()
        errors = config.validate()
        assert len(errors) == 0

    def test_development_config_allows_relaxed_settings(self):
        """Development environment can have relaxed settings"""
        config = ProductionConfig()
        config.environment = Environment.DEVELOPMENT
        config.risk.always_human_for_critical = False

        # Should be valid in development
        errors = config.validate()
        assert len(errors) == 0

    def test_production_enforces_critical_safety(self):
        """Production must enforce critical safety settings"""
        config = ProductionConfig()
        config.environment = Environment.PRODUCTION
        config.risk.always_human_for_critical = False

        errors = config.validate()
        assert any("always_human_for_critical" in err for err in errors)

    def test_production_requires_audit_chain(self):
        """Production must have audit chain enabled"""
        config = ProductionConfig()
        config.environment = Environment.PRODUCTION
        config.audit.enable_audit_chain = False

        errors = config.validate()
        assert any("audit chain" in err for err in errors)

    def test_production_requires_critical_tier_validation(self):
        """Production must validate critical tier escalations"""
        config = ProductionConfig()
        config.environment = Environment.PRODUCTION
        config.escalation.enable_critical_tier_validation = False

        errors = config.validate()
        assert any("critical_tier_validation" in err for err in errors)

    def test_validates_risk_threshold_order(self):
        """Risk thresholds must be properly ordered"""
        config = ProductionConfig()
        config.risk.high_threshold = 0.8
        config.risk.critical_threshold = 0.6  # Invalid: high > critical

        errors = config.validate()
        assert any("high_threshold must be <=" in err for err in errors)

    def test_validates_threshold_bounds(self):
        """Risk thresholds must be in [0, 1]"""
        config = ProductionConfig()
        config.risk.critical_threshold = 1.5  # Invalid

        errors = config.validate()
        assert any("critical_threshold must be in [0, 1]" in err for err in errors)

    def test_validates_positive_values(self):
        """Certain values must be positive"""
        config = ProductionConfig()
        config.inference.max_latency_ms = -100  # Invalid

        errors = config.validate()
        assert any("max_latency_ms must be > 0" in err for err in errors)

    def test_to_dict_serialization(self):
        """Should serialize to dictionary"""
        config = ProductionConfig()
        config.environment = Environment.PRODUCTION
        config.version = "1.0.0"

        data = config.to_dict()

        assert data["environment"] == "production"
        assert data["version"] == "1.0.0"
        assert "inference" in data
        assert "security" in data
        assert "risk" in data

    def test_from_dict_deserialization(self):
        """Should deserialize from dictionary"""
        data = {
            "environment": "staging",
            "version": "0.2.0",
            "inference": {
                "max_latency_ms": 1500.0,
                "timeout_multiplier": 2.0
            },
            "risk": {
                "critical_threshold": 0.8
            }
        }

        config = ProductionConfig.from_dict(data)

        assert config.environment == Environment.STAGING
        assert config.version == "0.2.0"
        assert config.inference.max_latency_ms == 1500.0
        assert config.risk.critical_threshold == 0.8

    def test_round_trip_serialization(self):
        """Should survive round-trip serialization"""
        original = ProductionConfig()
        original.environment = Environment.PRODUCTION
        original.inference.max_latency_ms = 2000.0
        original.security.rate_limit_per_second = 20.0

        # Serialize
        data = original.to_dict()

        # Deserialize
        restored = ProductionConfig.from_dict(data)

        assert restored.environment == original.environment
        assert restored.inference.max_latency_ms == original.inference.max_latency_ms
        assert restored.security.rate_limit_per_second == original.security.rate_limit_per_second


class TestConfigManager:
    """Test configuration manager with hot-reload"""

    def setup_method(self):
        """Create temporary config file for testing"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()

    def teardown_method(self):
        """Clean up temporary file"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_loads_from_file(self):
        """Should load configuration from file"""
        config_data = {
            "environment": "production",
            "version": "1.0.0",
            "inference": {"max_latency_ms": 1200.0}
        }

        with open(self.temp_file.name, 'w') as f:
            json.dump(config_data, f)

        manager = ConfigManager(self.temp_file.name)

        config = manager.get_config()
        assert config.environment == Environment.PRODUCTION
        assert config.inference.max_latency_ms == 1200.0

    def test_validates_on_load(self):
        """Should validate configuration when loading"""
        invalid_config = {
            "environment": "production",
            "risk": {
                "always_human_for_critical": False  # Invalid in production
            }
        }

        with open(self.temp_file.name, 'w') as f:
            json.dump(invalid_config, f)

        with pytest.raises(ValueError, match="Invalid configuration"):
            ConfigManager(self.temp_file.name)

    def test_hot_reload(self):
        """Should support hot-reload from file"""
        initial_config = {
            "environment": "development",
            "version": "0.1.0"
        }

        with open(self.temp_file.name, 'w') as f:
            json.dump(initial_config, f)

        manager = ConfigManager(self.temp_file.name)
        assert manager.get_config().version == "0.1.0"

        # Update file
        updated_config = {
            "environment": "development",
            "version": "0.2.0"
        }

        with open(self.temp_file.name, 'w') as f:
            json.dump(updated_config, f)

        # Reload
        manager.reload()

        assert manager.get_config().version == "0.2.0"

    def test_dynamic_update(self):
        """Should support dynamic configuration updates"""
        manager = ConfigManager()

        updates = {
            "version": "1.5.0",
            "inference": {"max_latency_ms": 1800.0}
        }

        manager.update_config(updates)

        config = manager.get_config()
        assert config.version == "1.5.0"
        assert config.inference.max_latency_ms == 1800.0

    def test_validates_dynamic_updates(self):
        """Should validate dynamic updates"""
        manager = ConfigManager()

        invalid_updates = {
            "environment": "production",
            "risk": {"always_human_for_critical": False}
        }

        with pytest.raises(ValueError, match="Invalid configuration"):
            manager.update_config(invalid_updates)

    def test_change_listeners(self):
        """Should notify listeners on configuration change"""
        manager = ConfigManager()

        notification_received = []

        def listener(config: ProductionConfig):
            notification_received.append(config.version)

        manager.register_change_listener(listener)

        # Update config
        manager.update_config({"version": "2.0.0"})

        assert "2.0.0" in notification_received

    def test_multiple_listeners(self):
        """Should notify multiple listeners"""
        manager = ConfigManager()

        listener1_calls = []
        listener2_calls = []

        manager.register_change_listener(lambda c: listener1_calls.append(c.version))
        manager.register_change_listener(lambda c: listener2_calls.append(c.version))

        manager.update_config({"version": "3.0.0"})

        assert "3.0.0" in listener1_calls
        assert "3.0.0" in listener2_calls

    def test_save_configuration(self):
        """Should save configuration to file"""
        manager = ConfigManager(self.temp_file.name)

        manager.update_config({
            "version": "4.0.0",
            "environment": "staging"
        })

        manager.save()

        # Load from file to verify
        with open(self.temp_file.name, 'r') as f:
            saved_data = json.load(f)

        assert saved_data["version"] == "4.0.0"
        assert saved_data["environment"] == "staging"

    def test_thread_safe_access(self):
        """Should provide thread-safe configuration access"""
        import threading

        manager = ConfigManager()

        results = []

        def read_config():
            for _ in range(100):
                config = manager.get_config()
                results.append(config.version)

        threads = [threading.Thread(target=read_config) for _ in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should complete without errors
        assert len(results) == 500


class TestEnvironmentSpecificValidation:
    """Test environment-specific validation rules"""

    def test_development_allows_disabled_security(self):
        """Development can disable security features"""
        config = ProductionConfig()
        config.environment = Environment.DEVELOPMENT
        config.security.enable_rate_limiting = False

        errors = config.validate()
        # Should not have errors (just warnings in production)
        critical_errors = [e for e in errors if "CRITICAL" in e]
        assert len(critical_errors) == 0

    def test_production_warns_about_disabled_rate_limiting(self):
        """Production should warn about disabled rate limiting"""
        config = ProductionConfig()
        config.environment = Environment.PRODUCTION
        config.security.enable_rate_limiting = False

        errors = config.validate()
        # Should have warning
        assert any("rate limiting" in err.lower() for err in errors)

    def test_staging_similar_to_production(self):
        """Staging should have similar constraints to production"""
        config = ProductionConfig()
        config.environment = Environment.STAGING
        config.risk.always_human_for_critical = True

        errors = config.validate()
        # Should be valid with proper settings
        assert len([e for e in errors if "CRITICAL" in e]) == 0


class TestFeatureFlags:
    """Test feature flag system"""

    def test_feature_flags_stored(self):
        """Should store feature flags"""
        config = ProductionConfig()
        config.feature_flags["experimental_routing"] = True
        config.feature_flags["new_inference_model"] = False

        assert config.feature_flags["experimental_routing"] is True
        assert config.feature_flags["new_inference_model"] is False

    def test_feature_flags_serialized(self):
        """Feature flags should be serialized"""
        config = ProductionConfig()
        config.feature_flags["test_feature"] = True

        data = config.to_dict()
        assert "feature_flags" in data
        assert data["feature_flags"]["test_feature"] is True

        # Round trip
        restored = ProductionConfig.from_dict(data)
        assert restored.feature_flags["test_feature"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

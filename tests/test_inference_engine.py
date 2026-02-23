"""
Tests for Inference Engine
"""

import pytest
from mental_health_router.inference_engine import (
    TextInferenceEngine,
    AudioInferenceEngine,
    InputType,
    InferenceResult
)


class TestTextInferenceEngine:
    """Tests for TextInferenceEngine"""

    def test_critical_distress_detection(self):
        """Test detection of critical distress signals"""
        engine = TextInferenceEngine(max_latency_ms=1000.0)

        result = engine.infer("I want to kill myself")

        assert result.input_type == InputType.TEXT
        assert "critical" in result.distress_signals
        assert result.confidence >= 0.5
        assert result.latency_ms < 1000.0

    def test_high_risk_detection(self):
        """Test detection of high-risk signals"""
        engine = TextInferenceEngine()

        result = engine.infer("I feel completely hopeless and worthless")

        assert "high_risk" in result.distress_signals
        assert result.confidence > 0.0

    def test_moderate_distress_detection(self):
        """Test detection of moderate distress"""
        engine = TextInferenceEngine()

        result = engine.infer("I'm feeling depressed and overwhelmed")

        assert "moderate" in result.distress_signals
        assert result.confidence > 0.0

    def test_no_distress_signals(self):
        """Test text with no distress signals"""
        engine = TextInferenceEngine()

        result = engine.infer("I'm having a great day!")

        assert len(result.distress_signals) == 0
        assert result.confidence == 0.0

    def test_latency_bound_enforcement(self):
        """Test that latency bounds are enforced"""
        engine = TextInferenceEngine(max_latency_ms=1000.0)

        result = engine.infer("Test message")

        assert result.latency_ms <= engine.max_latency_ms

    def test_metadata_tracking(self):
        """Test metadata is tracked"""
        engine = TextInferenceEngine()

        result = engine.infer("Test message")

        assert "text_length" in result.metadata
        assert result.metadata["text_length"] == len("Test message")


class TestAudioInferenceEngine:
    """Tests for AudioInferenceEngine"""

    def test_audio_inference_basic(self):
        """Test basic audio inference"""
        engine = AudioInferenceEngine(max_latency_ms=2000.0)

        audio_data = b"fake audio data"
        result = engine.infer(audio_data)

        assert result.input_type == InputType.AUDIO
        assert result.latency_ms < 2000.0

    def test_audio_metadata(self):
        """Test audio metadata tracking"""
        engine = AudioInferenceEngine()

        audio_data = b"test audio bytes"
        result = engine.infer(audio_data)

        assert "audio_bytes" in result.metadata
        assert result.metadata["audio_bytes"] == len(audio_data)

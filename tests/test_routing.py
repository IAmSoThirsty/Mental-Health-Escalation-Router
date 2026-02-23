"""
Tests for Geo-Aware Routing
"""

import pytest
from mental_health_router.routing import (
    GeoAwareRouter,
    HumanResource,
    GeoLocation,
    ResourceStatus,
    RoutingPreferences
)


class TestGeoLocation:
    """Tests for GeoLocation"""

    def test_distance_calculation(self):
        """Test distance calculation between locations"""
        loc1 = GeoLocation(latitude=37.7749, longitude=-122.4194)  # San Francisco
        loc2 = GeoLocation(latitude=40.7128, longitude=-74.0060)   # New York

        distance = loc1.distance_to(loc2)

        # Distance between SF and NY is approximately 4100 km
        assert 4000 < distance < 5000


class TestHumanResource:
    """Tests for HumanResource"""

    def test_is_available(self):
        """Test availability checking"""
        resource = HumanResource(
            id="hr_001",
            name="Test Counselor",
            location=GeoLocation(37.7749, -122.4194),
            status=ResourceStatus.AVAILABLE,
            specializations=["crisis"],
            max_concurrent_cases=3,
            current_cases=1
        )

        assert resource.is_available() is True

    def test_not_available_when_busy(self):
        """Test resource not available when status is busy"""
        resource = HumanResource(
            id="hr_001",
            name="Test Counselor",
            location=GeoLocation(37.7749, -122.4194),
            status=ResourceStatus.BUSY,
            specializations=["crisis"],
            max_concurrent_cases=3,
            current_cases=1
        )

        assert resource.is_available() is False

    def test_not_available_at_max_capacity(self):
        """Test resource not available at max capacity"""
        resource = HumanResource(
            id="hr_001",
            name="Test Counselor",
            location=GeoLocation(37.7749, -122.4194),
            status=ResourceStatus.AVAILABLE,
            specializations=["crisis"],
            max_concurrent_cases=3,
            current_cases=3
        )

        assert resource.is_available() is False

    def test_can_handle_language(self):
        """Test language capability checking"""
        resource = HumanResource(
            id="hr_001",
            name="Test Counselor",
            location=GeoLocation(37.7749, -122.4194),
            status=ResourceStatus.AVAILABLE,
            specializations=["crisis"],
            languages=["en", "es"]
        )

        assert resource.can_handle_language("en") is True
        assert resource.can_handle_language("es") is True
        assert resource.can_handle_language("fr") is False


class TestGeoAwareRouter:
    """Tests for GeoAwareRouter"""

    def test_add_resource(self):
        """Test adding resources"""
        router = GeoAwareRouter()
        resource = HumanResource(
            id="hr_001",
            name="Test Counselor",
            location=GeoLocation(37.7749, -122.4194),
            status=ResourceStatus.AVAILABLE,
            specializations=["crisis"]
        )

        router.add_resource(resource)
        assert len(router.resources) == 1

    def test_remove_resource(self):
        """Test removing resources"""
        router = GeoAwareRouter()
        resource = HumanResource(
            id="hr_001",
            name="Test Counselor",
            location=GeoLocation(37.7749, -122.4194),
            status=ResourceStatus.AVAILABLE,
            specializations=["crisis"]
        )

        router.add_resource(resource)
        removed = router.remove_resource("hr_001")

        assert removed is True
        assert len(router.resources) == 0

    def test_find_best_resource_by_distance(self):
        """Test finding closest resource"""
        router = GeoAwareRouter()

        # Add two resources
        resource1 = HumanResource(
            id="hr_001",
            name="Close Counselor",
            location=GeoLocation(37.7749, -122.4194),  # San Francisco
            status=ResourceStatus.AVAILABLE,
            specializations=["crisis"]
        )

        resource2 = HumanResource(
            id="hr_002",
            name="Far Counselor",
            location=GeoLocation(40.7128, -74.0060),  # New York
            status=ResourceStatus.AVAILABLE,
            specializations=["crisis"]
        )

        router.add_resource(resource1)
        router.add_resource(resource2)

        # Location near San Francisco
        user_location = GeoLocation(37.8, -122.4)

        best = router.find_best_resource(user_location)
        assert best.id == "hr_001"

    def test_find_best_resource_with_language_preference(self):
        """Test finding resource with language preference"""
        router = GeoAwareRouter()

        resource1 = HumanResource(
            id="hr_001",
            name="English Counselor",
            location=GeoLocation(37.7749, -122.4194),
            status=ResourceStatus.AVAILABLE,
            specializations=["crisis"],
            languages=["en"]
        )

        resource2 = HumanResource(
            id="hr_002",
            name="Spanish Counselor",
            location=GeoLocation(37.7750, -122.4195),
            status=ResourceStatus.AVAILABLE,
            specializations=["crisis"],
            languages=["es"]
        )

        router.add_resource(resource1)
        router.add_resource(resource2)

        user_location = GeoLocation(37.7749, -122.4194)
        preferences = RoutingPreferences(preferred_language="es")

        best = router.find_best_resource(user_location, preferences)
        assert best.id == "hr_002"

    def test_route_success(self):
        """Test successful routing"""
        router = GeoAwareRouter()

        resource = HumanResource(
            id="hr_001",
            name="Test Counselor",
            location=GeoLocation(37.7749, -122.4194),
            status=ResourceStatus.AVAILABLE,
            specializations=["crisis"]
        )

        router.add_resource(resource)

        user_location = GeoLocation(37.7750, -122.4195)
        result = router.route(user_location)

        assert result["success"] is True
        assert result["resource"].id == "hr_001"
        assert "distance_km" in result

    def test_route_no_available_resources(self):
        """Test routing when no resources available"""
        router = GeoAwareRouter()

        user_location = GeoLocation(37.7749, -122.4194)
        result = router.route(user_location)

        assert result["success"] is False
        assert result["resource"] is None

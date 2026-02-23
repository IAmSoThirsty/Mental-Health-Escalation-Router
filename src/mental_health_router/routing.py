"""
Geo-Aware Routing

Routes escalations to appropriate human resources based on geographical location
and resource availability.
"""

from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
import math


@dataclass
class GeoLocation:
    """Geographical coordinates"""
    latitude: float
    longitude: float
    timezone: Optional[str] = None

    def distance_to(self, other: "GeoLocation") -> float:
        """
        Calculate distance to another location using Haversine formula.

        Args:
            other: Other geographical location

        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth's radius in kilometers

        lat1_rad = math.radians(self.latitude)
        lat2_rad = math.radians(other.latitude)
        delta_lat = math.radians(other.latitude - self.latitude)
        delta_lon = math.radians(other.longitude - self.longitude)

        a = (
            math.sin(delta_lat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        return R * c


class ResourceStatus(Enum):
    """Status of human resource"""
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


@dataclass
class HumanResource:
    """
    Represents a human resource (counselor, therapist, crisis responder).

    Attributes:
        id: Unique identifier
        name: Resource name
        location: Geographical location
        status: Current availability status
        specializations: Areas of expertise
        max_concurrent_cases: Maximum concurrent cases this resource can handle
        current_cases: Number of current active cases
        languages: Languages spoken
    """
    id: str
    name: str
    location: GeoLocation
    status: ResourceStatus
    specializations: List[str]
    max_concurrent_cases: int = 3
    current_cases: int = 0
    languages: List[str] = None

    def __post_init__(self) -> None:
        if self.languages is None:
            self.languages = ["en"]

    def is_available(self) -> bool:
        """Check if resource is available for new cases"""
        return (
            self.status == ResourceStatus.AVAILABLE and
            self.current_cases < self.max_concurrent_cases
        )

    def can_handle_language(self, language: str) -> bool:
        """Check if resource can handle specified language"""
        return language in self.languages


class RoutingPreferences:
    """Preferences for routing decisions"""

    def __init__(
        self,
        max_distance_km: Optional[float] = None,
        preferred_language: str = "en",
        required_specializations: Optional[List[str]] = None
    ):
        self.max_distance_km = max_distance_km
        self.preferred_language = preferred_language
        self.required_specializations = required_specializations or []


class GeoAwareRouter:
    """
    Routes cases to appropriate human resources based on geography and availability.

    Ensures cases are routed to the closest available qualified resource.
    """

    def __init__(self, resources: Optional[List[HumanResource]] = None):
        """
        Initialize router.

        Args:
            resources: List of available human resources
        """
        self.resources = resources or []

    def add_resource(self, resource: HumanResource) -> None:
        """Add a human resource to the routing pool"""
        self.resources.append(resource)

    def remove_resource(self, resource_id: str) -> bool:
        """
        Remove a resource from the routing pool.

        Args:
            resource_id: ID of resource to remove

        Returns:
            True if resource was removed, False if not found
        """
        initial_count = len(self.resources)
        self.resources = [r for r in self.resources if r.id != resource_id]
        return len(self.resources) < initial_count

    def find_best_resource(
        self,
        location: GeoLocation,
        preferences: Optional[RoutingPreferences] = None
    ) -> Optional[HumanResource]:
        """
        Find the best available resource for a given location.

        Args:
            location: Location requiring assistance
            preferences: Routing preferences

        Returns:
            Best matching HumanResource, or None if no suitable resource available
        """
        if preferences is None:
            preferences = RoutingPreferences()

        # Filter available resources
        available_resources = [r for r in self.resources if r.is_available()]

        if not available_resources:
            return None

        # Filter by language
        if preferences.preferred_language:
            language_compatible = [
                r for r in available_resources
                if r.can_handle_language(preferences.preferred_language)
            ]
            if language_compatible:
                available_resources = language_compatible

        # Filter by required specializations
        if preferences.required_specializations:
            specialized = [
                r for r in available_resources
                if all(spec in r.specializations for spec in preferences.required_specializations)
            ]
            if specialized:
                available_resources = specialized

        # Calculate distances and filter by max distance
        resource_distances: List[Tuple[HumanResource, float]] = []
        for resource in available_resources:
            distance = location.distance_to(resource.location)
            if preferences.max_distance_km is None or distance <= preferences.max_distance_km:
                resource_distances.append((resource, distance))

        if not resource_distances:
            return None

        # Sort by distance and return closest
        resource_distances.sort(key=lambda x: x[1])
        return resource_distances[0][0]

    def route(
        self,
        location: GeoLocation,
        preferences: Optional[RoutingPreferences] = None
    ) -> Dict[str, any]:
        """
        Route a case to a resource.

        Args:
            location: Location requiring assistance
            preferences: Routing preferences

        Returns:
            Dictionary containing routing result
        """
        resource = self.find_best_resource(location, preferences)

        if resource is None:
            return {
                "success": False,
                "resource": None,
                "reason": "No available resources matching criteria"
            }

        # In a real implementation, this would update the resource's status
        # and create the assignment in a database

        return {
            "success": True,
            "resource": resource,
            "distance_km": location.distance_to(resource.location),
            "reason": "Successfully routed to nearest available resource"
        }

    def get_available_resources(self) -> List[HumanResource]:
        """Get all currently available resources"""
        return [r for r in self.resources if r.is_available()]

    def get_resource_by_id(self, resource_id: str) -> Optional[HumanResource]:
        """Get resource by ID"""
        for resource in self.resources:
            if resource.id == resource_id:
                return resource
        return None

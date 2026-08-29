from enum import Enum


class Role(str, Enum):
    SYSTEM_ADMIN = "system_admin"
    GOV_ADMIN = "gov_admin"
    FIELD_OFFICER = "field_officer"
    AGRI_OFFICER = "agri_officer"
    AUDITOR = "auditor"


class DisasterType(str, Enum):
    FLOOD = "flood"
    CYCLONE = "cyclone"
    LANDSLIDE = "landslide"
    DROUGHT = "drought"
    EARTHQUAKE = "earthquake"
    WILDFIRE = "wildfire"
    OTHER = "other"


class Severity(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    CATASTROPHIC = "catastrophic"


class LifecycleStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    MONITORING = "monitoring"
    CLOSED = "closed"


class DamageCategory(str, Enum):
    BUILDINGS = "buildings"
    ROADS = "roads"
    BRIDGES = "bridges"
    AGRICULTURAL_FIELDS = "agricultural_fields"
    INFRASTRUCTURE = "infrastructure"
    FLOODED_AREAS = "flooded_areas"
    VEGETATION = "vegetation"
    CRITICAL_FACILITIES = "critical_facilities"


class RecoveryPhase(str, Enum):
    PRE_DISASTER = "pre_disaster"
    POST_DISASTER = "post_disaster"
    MONTH_1 = "month_1"
    MONTH_3 = "month_3"
    MONTH_6 = "month_6"
    CURRENT = "current"


class ClaimStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    CONSISTENT = "consistent"
    MINOR_DISCREPANCY = "minor_discrepancy"
    REQUIRES_VERIFICATION = "requires_verification"
    HIGH_ANOMALY_RISK = "high_anomaly_risk"


class FundStatus(str, Enum):
    SUBMITTED = "submitted"
    CONSISTENT_WITH_EVIDENCE = "consistent_with_evidence"
    REQUIRES_ADDITIONAL_VERIFICATION = "requires_additional_verification"
    SIGNIFICANT_DISCREPANCY_DETECTED = "significant_discrepancy_detected"


class AllocationStatus(str, Enum):
    ALLOCATED = "allocated"
    IN_PROGRESS = "in_progress"
    DELAYED = "delayed"
    COMPLETED = "completed"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InspectionStatus(str, Enum):
    ASSIGNED = "assigned"
    EN_ROUTE = "en_route"
    ARRIVED = "arrived"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    NEEDS_FURTHER_INVESTIGATION = "needs_further_investigation"
    READY_FOR_REVIEW = "ready_for_review"


class RecoveryStatus(str, Enum):
    NOT_STARTED = "not_started"
    EARLY = "early"
    UNDERWAY = "underway"
    ADVANCED = "advanced"
    RESTORED = "restored"
    DELAYED = "delayed"


class DuplicateReviewStatus(str, Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    DISMISSED = "dismissed"
    CONFIRMED_RELATED = "confirmed_related"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class NotificationChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"

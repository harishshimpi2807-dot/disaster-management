from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    user_id: int


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=10, max_length=72)
    role: str
    agency: str = ""
    district: str = ""


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    agency: str | None = None
    district: str | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=10, max_length=72)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    agency: str
    district: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DisasterIn(BaseModel):
    name: str
    disaster_type: str
    start_date: date
    end_date: date | None = None
    state: str
    district: str
    locality: str = ""
    severity: str
    description: str = ""
    status: str = "active"
    boundary: dict[str, Any] | None = None


class DisasterOut(BaseModel):
    id: int
    public_id: str
    name: str
    disaster_type: str
    start_date: date
    end_date: date | None
    state: str
    district: str
    locality: str
    severity: str
    description: str
    status: str
    boundary: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AssessmentIn(BaseModel):
    disaster_id: int
    notes: str = ""
    before_image_id: int | None = None
    after_image_id: int | None = None
    aoi: dict[str, Any] | None = None


class AssessmentOut(BaseModel):
    id: int
    public_id: str
    disaster_id: int
    category: str
    severity: str
    estimated_area_ha: float
    confidence: float
    geometry: dict[str, Any] | None
    notes: str
    analyzed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ClaimIn(BaseModel):
    disaster_id: int
    farmer_reference: str
    crop_type: str
    incident_date: date
    reported_damage_pct: float = Field(ge=0, le=100)
    field_boundary: dict[str, Any] | None = None
    historical_condition: str = ""
    post_condition: str = ""


class ClaimOut(BaseModel):
    id: int
    public_id: str
    disaster_id: int
    farmer_reference: str
    crop_type: str
    incident_date: date
    reported_damage_pct: float
    estimated_damage_pct: float | None
    confidence: float | None
    difference_pct: float | None
    recommendation: str
    status: str
    field_boundary: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FundRequestIn(BaseModel):
    disaster_id: int
    department: str
    location_label: str
    damage_category: str
    reported_damage: str
    requested_amount: float = Field(gt=0)
    geometry: dict[str, Any] | None = None


class FundRequestOut(BaseModel):
    id: int
    public_id: str
    disaster_id: int
    department: str
    location_label: str
    damage_category: str
    reported_damage: str
    requested_amount: float
    evidence_consistency: float | None
    confidence: float | None
    recommendation: str
    status: str
    geometry: dict[str, Any] | None
    submitted_at: datetime

    model_config = {"from_attributes": True}


class AllocationIn(BaseModel):
    disaster_id: int
    fund_request_id: int | None = None
    purpose: str
    amount: float = Field(gt=0)
    allocating_authority: str
    implementing_agency: str
    location_label: str
    allocated_on: date
    expected_completion: date | None = None
    planned_progress_pct: float = 0
    observed_progress_pct: float = 0
    status: str = "allocated"
    geometry: dict[str, Any] | None = None


class AllocationOut(BaseModel):
    id: int
    public_id: str
    disaster_id: int
    purpose: str
    amount: float
    allocating_authority: str
    implementing_agency: str
    location_label: str
    allocated_on: date
    expected_completion: date | None
    status: str
    planned_progress_pct: float
    observed_progress_pct: float
    geometry: dict[str, Any] | None

    model_config = {"from_attributes": True}


class InspectionIn(BaseModel):
    disaster_id: int
    case_type: str
    case_id: int
    assigned_to_id: int
    required_actions: str = ""
    location: dict[str, Any] | None = None


class InspectionUpdate(BaseModel):
    status: str | None = None
    observations: str | None = None
    verified_damage: str | None = None
    location: dict[str, Any] | None = None


class InspectionOut(BaseModel):
    id: int
    public_id: str
    disaster_id: int
    case_type: str
    case_id: int
    assigned_to_id: int
    status: str
    required_actions: str
    observations: str
    verified_damage: str
    arrived_at: datetime | None
    submitted_at: datetime | None
    location: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RecoveryIn(BaseModel):
    disaster_id: int
    category: str
    state: str
    district: str
    locality: str = ""
    recovery_pct: float = Field(ge=0, le=100)
    status: str
    phase: str = "post_disaster"
    observed_on: date
    notes: str = ""
    geometry: dict[str, Any] | None = None


class RecoveryOut(BaseModel):
    id: int
    public_id: str
    disaster_id: int
    category: str
    state: str
    district: str
    locality: str
    recovery_pct: float
    recovery_score: float
    status: str
    phase: str
    observed_on: date
    notes: str
    geometry: dict[str, Any] | None

    model_config = {"from_attributes": True}


class SettingIn(BaseModel):
    key: str
    value: str


class RuleIn(BaseModel):
    name: str
    event_type: str
    min_risk: str = "medium"
    channel: str = "in_app"
    enabled: bool = True

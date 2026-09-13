"""
Pydantic v2 request/response schemas for FastAPI.
All fields explicitly typed and documented.
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


# ─────────────────────────────────────────────
#  REQUEST SCHEMAS
# ─────────────────────────────────────────────

class StartSessionRequest(BaseModel):
    patient_name: str = Field(default="Anonymous", description="Patient display name")
    case_id: Optional[str] = Field(default=None, description="Optional synthetic case ID for sandbox mode")

    model_config = {"json_schema_extra": {"example": {"patient_name": "Ramesh Kumar", "case_id": "C01"}}}


class ReplyRequest(BaseModel):
    session_id: str = Field(..., description="Session UUID from /api/session/start")
    text: str = Field(..., min_length=1, max_length=2000, description="Patient's free-text answer")
    answered_slot: Optional[str] = Field(default=None, description="Slot key that this reply addresses")

    model_config = {"json_schema_extra": {"example": {"session_id": "abc-123", "text": "Yes I have chest pain", "answered_slot": "chest_pain"}}}


class VitalsRequest(BaseModel):
    session_id: str = Field(..., description="Session UUID")
    heart_rate: Optional[float] = Field(default=None, ge=0, le=300, description="Heart rate in bpm")
    systolic_bp: Optional[float] = Field(default=None, ge=0, le=300, description="Systolic BP in mmHg")
    diastolic_bp: Optional[float] = Field(default=None, ge=0, le=200, description="Diastolic BP in mmHg")
    spo2: Optional[float] = Field(default=None, ge=0, le=100, description="Oxygen saturation in percent")
    resp_rate: Optional[float] = Field(default=None, ge=0, le=100, description="Respiratory rate per minute")
    temperature: Optional[float] = Field(default=None, ge=25.0, le=45.0, description="Temperature in Celsius")

    model_config = {"json_schema_extra": {"example": {"session_id": "abc-123", "heart_rate": 110, "systolic_bp": 90, "spo2": 92, "resp_rate": 26, "temperature": 39.1}}}


class WhatIfRequest(BaseModel):
    session_id: str = Field(..., description="Session UUID")
    slot: str = Field(..., description="Slot key to hypothetically change")
    value: Any = Field(..., description="Hypothetical value for the slot")

    model_config = {"json_schema_extra": {"example": {"session_id": "abc-123", "slot": "spo2", "value": 88}}}


class OverrideRequest(BaseModel):
    session_id: str = Field(..., description="Session UUID")
    new_routing_code: str = Field(..., description="One of: SELF_CARE, STANDARD, URGENT, EMERGENCY, CRITICAL, RESUS")
    clinician_id: str = Field(..., description="ID or name of overriding clinician")
    reason: str = Field(..., min_length=5, max_length=500, description="Clinical reason for override")

    model_config = {"json_schema_extra": {"example": {"session_id": "abc-123", "new_routing_code": "CRITICAL", "clinician_id": "DR-PATEL-001", "reason": "Patient deteriorating on reassessment, escalating to CRITICAL"}}}


class SOSRequest(BaseModel):
    session_id: str = Field(..., description="Session UUID")
    triggered_by: str = Field(default="UNKNOWN", description="Who triggered SOS: PATIENT, NURSE, BYSTANDER")


# ─────────────────────────────────────────────
#  RESPONSE SCHEMAS
# ─────────────────────────────────────────────

class RoutingOutcome(BaseModel):
    tier: int
    code: str
    label: str
    color: str
    target: str
    decision_basis: str
    explanation: str
    human_review_required: bool


class FiredRule(BaseModel):
    rule: str
    points: int
    citation: str


class PendingRule(BaseModel):
    rule: str
    missing: List[str]
    max_points: int


class RiskResult(BaseModel):
    rule_version: str
    score: int
    score_min: int
    score_max: int
    band_width_points: int
    tier_min: Dict[str, Any]
    tier_max: Dict[str, Any]
    band_spans_boundary: bool
    confidence_pct: float
    fired_rules: List[FiredRule]
    pending_rules: List[PendingRule]
    hard_override: Optional[Dict[str, Any]]


class BeliefEntry(BaseModel):
    key: str
    label: str
    p: float


class BeliefResult(BaseModel):
    distribution: List[BeliefEntry]
    top: BeliefEntry
    entropy_bits: float
    normalised_uncertainty: float
    evidence_used: List[str]
    disclaimer: str


class QuestionCandidate(BaseModel):
    slot: str
    question: str
    dtype: str
    choices: Optional[List[str]]
    red_flag: bool
    ask_cost_s: float
    evoi_band_pts: float
    evoi_entropy_bits: float
    p_changes_routing: float
    utility: float
    why_this_question: str


class NextQuestion(BaseModel):
    slot: str
    question: str
    dtype: str
    choices: Optional[List[str]]
    red_flag: bool
    why_this_question: str
    is_resolution: Optional[bool] = False
    contradiction_id: Optional[str] = None


class ContradictionEntry(BaseModel):
    id: str
    type: str
    slot: str
    message: str
    severity: str
    status: str
    ts: str


class ToolTraceEntry(BaseModel):
    ts: str
    tool: str
    args: str
    result: str
    ms: int


class EscalationResult(BaseModel):
    escalate: bool
    reasons: List[str]
    open_contradictions: List[Dict]
    red_flag_unknowns: List[str]


class CitationEntry(BaseModel):
    id: str
    source: str
    snippet: str
    relevance: float


class SBARHandoff(BaseModel):
    S: str
    B: str
    A: str
    R: str


class AgentStepResponse(BaseModel):
    phase: str
    risk: Optional[RiskResult] = None
    belief: Optional[BeliefResult] = None
    next_question: Optional[NextQuestion] = None
    question_candidates: Optional[List[QuestionCandidate]] = None
    routing: Optional[RoutingOutcome] = None
    escalation: Optional[EscalationResult] = None
    contradiction_alert: Optional[List[ContradictionEntry]] = None
    citations: Optional[List[CitationEntry]] = None
    handoff_sbar: Optional[SBARHandoff] = None
    completeness: float = 0.0
    questions_asked: int = 0
    question_budget: int = 9
    tool_trace: List[ToolTraceEntry] = []
    delta: Optional[Dict[str, Any]] = None
    audit_hash: Optional[str] = None
    rule_version: Optional[str] = None
    disclaimer: str = ""
    environment: str = "SIMULATED_SANDBOX"
    is_diagnosis: bool = False
    latency_ms: int = 0
    refusal: bool = False
    reassessment_triggered_by: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    patient_name: str
    facts: Dict[str, Any]
    denied: List[str]
    unknown_declared: List[str]
    asked: List[str]
    transcript: List[Dict]
    contradictions: List[Dict]
    risk_history: List[Dict]
    tool_trace: List[Dict]
    completeness: float
    audit_hash: str
    status: str
    disclaimer: str


class QueueEntry(BaseModel):
    session_id: str
    patient_name: str
    code: str
    label: str
    tier: int
    color: str
    target: str
    score_min: int
    score_max: int
    confidence: float
    human_review: bool
    top_consideration: str
    questions_asked: int
    created_at: str


class QueueResponse(BaseModel):
    queue: List[QueueEntry]
    total: int
    needs_human_review: int


class WhatIfResponse(BaseModel):
    slot: str
    value: Any
    before: Dict[str, Any]
    after: Dict[str, Any]
    routing_changed: bool
    newly_fired_rules: List[Dict]
    disclaimer: str


class AutoplayFrame(BaseModel):
    turn: int
    agent_question: Optional[str] = None
    why: Optional[str] = None
    patient: Optional[str] = None
    result: Dict[str, Any]


class AutoplayResponse(BaseModel):
    session_id: str
    case: str
    ground_truth: str
    predicted: Optional[str]
    match: bool
    questions_asked: int
    frames: List[AutoplayFrame]
    final: Dict[str, Any]


class SlotMeta(BaseModel):
    key: str
    question: str
    dtype: str
    red_flag: bool
    ask_cost_s: float
    max_points: int
    rationale: str


class MetaResponse(BaseModel):
    slots: List[SlotMeta]
    routing_outcomes: List[Dict]
    normal_ranges: Dict
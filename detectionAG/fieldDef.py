from typing import List, Optional, Union, Dict
# Use pydantic_v1 for compatibility with the current version of LangChain
from langchain_core.pydantic_v1 import BaseModel, Field

class MedicationSubjective(BaseModel):
    """Represents a medication reported by the patient."""
    name: str = Field(..., description="Name of the medication.")
    dose: Optional[str] = Field(None, description="Dosage of the medication, e.g., '10 mg'.")
    route: Optional[str] = Field(None, description="Route of administration, e.g., 'oral'.")
    frequency: Optional[str] = Field(None, description="How often the medication is taken, e.g., 'daily'.")
    duration: Optional[str] = Field(None, description="How long the patient has been taking the medication.")
    indication: Optional[str] = Field(None, description="The reason for taking the medication, e.g., 'for hypertension'.")

class Allergy(BaseModel):
    """Represents a patient's allergy."""
    substance: str = Field(..., description="The substance the patient is allergic to, e.g., 'Penicillin'.")
    reaction: Optional[str] = Field(None, description="The reaction to the substance, e.g., 'rash' or 'anaphylaxis'.")
    severity: Optional[str] = Field(None, description="Severity of the allergic reaction, e.g., 'mild', 'severe'.")

class VitalSigns(BaseModel):
    """Represents a single set of vital signs recorded at a specific time."""
    time: Optional[str] = Field(None, description="Time the vitals were taken (HH:MM).")
    bp: Optional[str] = Field(None, description="Blood pressure, e.g., '120/80 mmHg'.")
    hr: Optional[str] = Field(None, description="Heart rate, e.g., '70 bpm'.")
    rr: Optional[str] = Field(None, description="Respiratory rate, e.g., '16 breaths/min'.")
    temp: Optional[str] = Field(None, description="Temperature, e.g., '37.0 C'.")
    spo2: Optional[str] = Field(None, description="Oxygen saturation, e.g., '98%'.")
    weight: Optional[str] = Field(None, description="Patient's weight, e.g., '75 kg'.")
    height: Optional[str] = Field(None, description="Patient's height, e.g., '175 cm'.")

class PhysicalExam(BaseModel):
    """Represents findings from the physical examination, organized by system."""
    general: Optional[str] = None
    heent: Optional[str] = Field(None, description="Head, Eyes, Ears, Nose, Throat.")
    cv: Optional[str] = Field(None, description="Cardiovascular.")
    resp: Optional[str] = Field(None, description="Respiratory.")
    gi: Optional[str] = Field(None, description="Gastrointestinal.")
    gu: Optional[str] = Field(None, description="Genitourinary.")
    msk: Optional[str] = Field(None, description="Musculoskeletal.")
    skin: Optional[str] = None
    neuro: Optional[str] = Field(None, description="Neurological.")
    psych: Optional[str] = Field(None, description="Psychiatric.")

class LabResult(BaseModel):
    """Represents a single laboratory test result."""
    name: str = Field(..., description="Name of the lab test, e.g., 'Hemoglobin'.")
    value: str = Field(..., description="The result value, e.g., '14.1'.")
    unit: Optional[str] = Field(None, description="Unit of measurement, e.g., 'g/dL'.")
    ref_range: Optional[str] = Field(None, description="Reference range, e.g., '13.5-17.5'.")
    date: Optional[str] = Field(None, description="Date the lab was drawn (YYYY-MM-DD).")

class ImagingResult(BaseModel):
    """Represents a single imaging study result."""
    modality: str = Field(..., description="Type of imaging, e.g., 'CT Head'.")
    body_part: Optional[str] = Field(None, description="Specific body part imaged.")
    result: str = Field(..., description="The summary of the imaging findings.")
    date: Optional[str] = Field(None, description="Date the imaging was performed (YYYY-MM-DD).")

class ProcedureResult(BaseModel):
    """Represents a clinical procedure."""
    name: str = Field(..., description="Name of the procedure, e.g., 'EGD'.")
    details: Optional[str] = Field(None, description="Details or findings of the procedure.")
    date: Optional[str] = Field(None, description="Date the procedure was performed (YYYY-MM-DD).")

class Diagnostics(BaseModel):
    """Container for all diagnostic results."""
    labs: List[LabResult] = Field(default_factory=list)
    imaging: List[ImagingResult] = Field(default_factory=list)
    procedures: List[ProcedureResult] = Field(default_factory=list)

# =============================================================================
# Sub-models for Assessment, Plan, and Billing
# =============================================================================
class AssessmentItem(BaseModel):
    """Represents a single problem in the assessment list."""
    problem: str = Field(..., description="The clinical problem, e.g., 'Acute Migraine'.")
    summary: Optional[str] = Field(None, description="Brief clinical synthesis supporting the problem.")
    differential: List[str] = Field(default_factory=list, description="List of differential diagnoses for the problem.")

class MedicationPlan(BaseModel):
    """Represents a medication to be prescribed or adjusted in the plan."""
    name: str = Field(..., description="Name of the medication.")
    dose: Optional[str] = Field(None, description="Dosage of the medication, e.g., '500 mg'.")
    route: Optional[str] = Field(None, description="Route of administration, e.g., 'PO'.")
    frequency: Optional[str] = Field(None, description="How often to administer, e.g., 'BID'.")
    duration: Optional[str] = Field(None, description="Duration of the prescription, e.g., 'for 7 days'.")
    
class PlanItem(BaseModel):
    """Represents the plan for a single clinical problem."""
    problem: str = Field(..., description="The clinical problem this plan addresses (should match an AssessmentItem).")
    actions: List[str] = Field(default_factory=list, description="Diagnostic or therapeutic actions to be taken, e.g., 'Order CBC'.")
    medications: List[MedicationPlan] = Field(default_factory=list, description="Medications to prescribe or adjust.")
    monitoring: List[str] = Field(default_factory=list, description="Parameters to monitor, e.g., 'Monitor for symptom resolution'.")
    consults: List[str] = Field(default_factory=list, description="Consultations to request, e.g., 'Consult Cardiology'.")
    follow_up: Optional[str] = Field(None, description="Follow-up instructions, e.g., 'Follow up in 2 weeks'.")
    patient_instructions: Optional[str] = Field(None, description="Education or instructions provided to the patient.")
    disposition: Optional[str] = Field(None, description="Patient disposition, e.g., 'Discharge home'.")
    
class ICD10Suggestion(BaseModel):
    """A suggested ICD-10 code based on the assessment."""
    code: str
    label: str
    confidence: float

class CPTLevel(BaseModel):
    """A suggested CPT E/M code."""
    code: Optional[str]
    rationale: Optional[str]

class Billing(BaseModel):
    """Container for billing-related information."""
    icd10_suggestions: List[ICD10Suggestion] = Field(default_factory=list)
    cpt_em_level: Optional[CPTLevel] = None

class Header(BaseModel):
    """Header information for the clinical note."""
    patient_name: Optional[str] = None
    mrn: Optional[str] = Field(None, description="Medical Record Number.")
    dob: Optional[str] = Field(None, description="Date of Birth (YYYY-MM-DD).")
    encounter_date: Optional[str] = Field(None, description="Date of encounter (YYYY-MM-DD).")
    location: Optional[str] = None
    referring_clinician: Optional[str] = None
    consulting_service: Optional[str] = None
    author: Optional[str] = Field(None, description="The clinician writing the note.")

class Subjective(BaseModel):
    """The subjective portion of the SOAP note, containing patient-reported information."""
    chief_complaint: Optional[str] = None
    hpi: Optional[str] = Field(None, description="History of Present Illness.")
    ros: List[str] = Field(default_factory=list, description="Review of Systems.")
    pmh: List[str] = Field(default_factory=list, description="Past Medical History.")
    psh: List[str] = Field(default_factory=list, description="Past Surgical History.")
    medications: List[MedicationSubjective] = Field(default_factory=list)
    allergies: List[Allergy] = Field(default_factory=list)
    family_history: List[str] = Field(default_factory=list)
    social_history: List[str] = Field(default_factory=list)

class Objective(BaseModel):
    """The objective portion of the SOAP note, containing observed and measured data."""
    vitals: List[VitalSigns] = Field(default_factory=list)
    physical_exam: PhysicalExam
    diagnostics: Diagnostics

class DocumentQuality(BaseModel):
    """Metadata about the quality and completeness of the generated document."""
    missing_data: List[str] = Field(default_factory=list, description="Clinically expected elements that were not found in the transcript.")
    conflicts: List[str] = Field(default_factory=list, description="Contradictory statements found in the transcript.")
    transcript_quality_notes: Optional[str] = Field(None, description="Comments on the quality of the source transcript (e.g., noisy, inaudible).")

# =============================================================================
# The Main Pydantic Model for the Entire SOAP Note
# =============================================================================
class SOAPNote(BaseModel):
    """A complete clinical SOAP note generated from a patient-clinician transcript."""
    header: Header
    subjective: Subjective
    objective: Objective
    assessment: List[AssessmentItem] = Field(default_factory=list)
    plan: List[PlanItem] = Field(default_factory=list)
    billing: Optional[Billing] = None
    document_quality: DocumentQuality
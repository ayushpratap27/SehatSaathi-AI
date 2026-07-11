"""
Pydantic schemas for Phase 3 — structured medical report output.

These models are the "contract" between the extraction pipeline and the API.
Every field is Optional so partial extraction never raises validation errors.
"""

from __future__ import annotations

from typing import List, Optional, Union

from pydantic import BaseModel, Field


# ------------------------------------------------------------------ #
# Leaf schemas
# ------------------------------------------------------------------ #

class PatientInfo(BaseModel):
    """Demographic information extracted from the report header."""

    name: Optional[str] = Field(None, description="Full patient name")
    age: Optional[int] = Field(None, description="Age in years")
    gender: Optional[str] = Field(None, description="Normalised gender: Male | Female | Other")
    date_of_birth: Optional[str] = Field(None, description="DOB as found in the report")
    patient_id: Optional[str] = Field(None, description="PID / MRD / UHID")
    mobile: Optional[str] = Field(None, description="Contact number")
    hospital_number: Optional[str] = Field(None, description="Inpatient or OPD number")

    model_config = {"json_schema_extra": {
        "example": {"name": "John Doe", "age": 45, "gender": "Male"}
    }}


class DoctorInfo(BaseModel):
    """Referring or treating doctor information."""

    name: Optional[str] = Field(None, description="Doctor's full name")
    designation: Optional[str] = Field(None, description="Dr. / Prof. / etc.")
    registration_number: Optional[str] = Field(None, description="Medical council registration")


class HospitalInfo(BaseModel):
    """Facility information extracted from the report."""

    name: Optional[str] = Field(None, description="Hospital or lab name")
    address: Optional[str] = Field(None, description="Address text")
    department: Optional[str] = Field(None, description="Department or ward")
    registration_number: Optional[str] = Field(None, description="NABL / NABH accreditation number")


class LabTest(BaseModel):
    """A single laboratory test result."""

    test_name: str = Field(..., description="Normalised test name")
    value: Optional[Union[float, str]] = Field(
        None, description="Numeric or qualitative result value"
    )
    unit: Optional[str] = Field(None, description="Unit of measurement")
    reference_range: Optional[str] = Field(None, description="Normal range as found in report")
    method: Optional[str] = Field(None, description="Test method / analyser")
    status: Optional[str] = Field(
        None,
        description="Derived status: Normal | High | Low | Critical | Positive | Negative | Abnormal",
    )

    model_config = {"json_schema_extra": {
        "example": {
            "test_name": "Hemoglobin",
            "value": 12.4,
            "unit": "g/dL",
            "reference_range": "13.5-17.5",
            "status": "Low",
        }
    }}


class MedicineInfo(BaseModel):
    """A single prescribed or mentioned medicine."""

    name: str = Field(..., description="Medicine / drug name")
    dosage: Optional[str] = Field(None, description="Dose, e.g., '500 mg'")
    frequency: Optional[str] = Field(None, description="How often: OD | BD | TDS | etc.")
    duration: Optional[str] = Field(None, description="Course duration, e.g., '5 days'")
    route: Optional[str] = Field(None, description="Route: Oral | IV | Topical | etc.")


# ------------------------------------------------------------------ #
# Root response schema
# ------------------------------------------------------------------ #

class ParsedReport(BaseModel):
    """
    Fully structured representation of a medical report.

    Returned by ``POST /api/v1/report/parse``.
    """

    patient: PatientInfo = Field(default_factory=PatientInfo)
    hospital: HospitalInfo = Field(default_factory=HospitalInfo)
    doctor: DoctorInfo = Field(default_factory=DoctorInfo)
    tests: List[LabTest] = Field(default_factory=list)
    diagnosis: List[str] = Field(default_factory=list)
    medicines: List[MedicineInfo] = Field(default_factory=list)
    report_date: Optional[str] = Field(None, description="Date found on the report")
    sample_type: Optional[str] = Field(None, description="E.g. Blood, Urine, Serum")

    model_config = {"json_schema_extra": {
        "example": {
            "patient": {"name": "John Doe", "age": 45, "gender": "Male"},
            "hospital": {"name": "ABC Hospital"},
            "doctor": {"name": None},
            "tests": [
                {"test_name": "Hemoglobin", "value": 12.4, "unit": "g/dL",
                 "reference_range": "13.5-17.5", "status": "Low"},
                {"test_name": "WBC", "value": 11200, "unit": "/uL",
                 "reference_range": "4000-11000", "status": "High"},
            ],
            "diagnosis": ["Iron Deficiency Anemia"],
            "medicines": [{"name": "Ferrous Sulfate"}],
        }
    }}


# ------------------------------------------------------------------ #
# Request schema for text-only parse
# ------------------------------------------------------------------ #

class ParseTextRequest(BaseModel):
    """Request body for parsing already-extracted text."""

    text: str = Field(..., description="Cleaned medical report text from Phase 2 extraction")

from datetime import date, datetime, time, timezone, timedelta
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

def clinic_today(): return datetime.now(timezone(timedelta(hours=5,minutes=30))).date()
def utc_now(): return datetime.now(timezone.utc).replace(tzinfo=None)

class DTO(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class Login(DTO):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)

class PatientInput(DTO):
    first_name: str = Field(min_length=1,max_length=50)
    last_name: str = Field(min_length=1,max_length=50)
    date_of_birth: date
    gender: Literal['FEMALE','MALE','NON_BINARY','OTHER','UNDISCLOSED']
    blood_group: Literal['A+','A-','B+','B-','AB+','AB-','O+','O-'] | None = None
    phone: str = Field(pattern=r'^\+?[0-9 ()-]{7,20}$')
    email: EmailStr | None = None
    address: str | None = Field(default=None,max_length=255)
    city: str | None = Field(default=None,max_length=80)
    occupation: str | None = Field(default=None,max_length=100)
    marital_status: Literal['SINGLE','MARRIED','DIVORCED','WIDOWED','UNDISCLOSED'] | None = None
    emergency_contact_name: str | None = Field(default=None,max_length=100)
    emergency_contact_phone: str | None = Field(default=None,max_length=20)

    @field_validator('date_of_birth')
    @classmethod
    def valid_birth(cls, v):
        if v>clinic_today(): raise ValueError('Date of birth cannot be in the future')
        return v

    @field_validator('email', mode='before')
    @classmethod
    def normalize_email(cls,v): return v.strip().lower() if v else None

class SymptomInput(DTO):
    symptom_name: str = Field(min_length=1,max_length=100)
    description: str | None = None
    is_active: bool = True

class CaseSymptomInput(DTO):
    symptom_id: int = Field(gt=0)
    severity: Literal['MILD','MODERATE','SEVERE'] = 'MILD'
    duration: str | None = Field(default=None,max_length=80)
    frequency: str | None = Field(default=None,max_length=80)
    notes: str | None = None

class HistoryInput(DTO):
    history_id: int | None = Field(default=None,gt=0)
    condition_name: str = Field(min_length=1,max_length=150)
    diagnosed_date: date | None = None
    treatment: str | None = None
    notes: str | None = None
    @field_validator('diagnosed_date')
    @classmethod
    def not_future(cls,v):
        if v and v>clinic_today(): raise ValueError('History date cannot be in the future')
        return v

class AllergyInput(DTO):
    allergy_id: int | None = Field(default=None,gt=0)
    allergen: str = Field(min_length=1,max_length=150)
    allergy_type: Literal['MEDICATION','FOOD','ENVIRONMENTAL','OTHER'] = 'OTHER'
    reaction: str | None = Field(default=None,max_length=255)
    severity: Literal['MILD','MODERATE','SEVERE'] = 'MILD'
    notes: str | None = None

class LifestyleInput(DTO):
    smoking_status: Literal['NEVER','FORMER','CURRENT','UNDISCLOSED'] | None = None
    alcohol_status: Literal['NEVER','FORMER','CURRENT','UNDISCLOSED'] | None = None
    exercise_frequency: str | None = Field(default=None,max_length=30)
    sleep_hours: float | None = Field(default=None,ge=0,le=24)
    diet_type: str | None = Field(default=None,max_length=30)
    occupation_notes: str | None = None

class VitalInput(DTO):
    temperature: float | None = Field(default=None,gt=0,le=999.99)
    systolic_bp: int | None = Field(default=None,gt=0,le=32767)
    diastolic_bp: int | None = Field(default=None,gt=0,le=32767)
    heart_rate: int | None = Field(default=None,gt=0,le=32767)
    respiratory_rate: int | None = Field(default=None,gt=0,le=32767)
    oxygen_saturation: float | None = Field(default=None,ge=0,le=100)
    height_cm: float | None = Field(default=None,gt=0,le=9999.99)
    weight_kg: float | None = Field(default=None,gt=0,le=9999.99)

class ExaminationInput(DTO):
    general_appearance: str | None = None
    cardiovascular_findings: str | None = None
    respiratory_findings: str | None = None
    neurological_findings: str | None = None
    abdominal_findings: str | None = None
    skin_findings: str | None = None
    other_findings: str | None = None

class DiagnosisFields(DTO):
    diagnosis_name: str = Field(min_length=1,max_length=150)
    diagnosis_type: Literal['PRIMARY','SECONDARY','DIFFERENTIAL'] = 'PRIMARY'
    notes: str | None = None

class DiagnosisInput(DiagnosisFields):
    visit_id: int = Field(gt=0)

class MedicineInput(DTO):
    medicine_code: str = Field(min_length=1,max_length=40)
    medicine_name: str = Field(min_length=1,max_length=150)
    generic_name: str = Field(min_length=1,max_length=150)
    manufacturer: str = Field(min_length=1,max_length=150)
    medicine_type: Literal['TABLET','CAPSULE','SYRUP','INJECTION','CREAM','DROPS']
    strength: str = Field(min_length=1,max_length=50)
    form: str = Field(min_length=1,max_length=50)
    is_active: bool = True

class PrescriptionLine(DTO):
    medicine_id: int = Field(gt=0)
    dosage: str = Field(min_length=1,max_length=100)
    frequency: str = Field(min_length=1,max_length=100)
    route: str = Field(min_length=1,max_length=50)
    duration_days: int = Field(gt=0,le=32767)
    instructions: str | None = None

class PrescriptionFields(DTO):
    doctor_id: int = Field(gt=0)
    prescription_date: date = Field(default_factory=clinic_today)
    notes: str | None = None
    medicines: list[PrescriptionLine] = Field(min_length=1)
    @field_validator('prescription_date')
    @classmethod
    def not_future(cls,v):
        if v>clinic_today(): raise ValueError('A recorded prescription date cannot be in the future')
        return v

class PrescriptionInput(PrescriptionFields):
    visit_id: int = Field(gt=0)

class FollowupFields(DTO):
    scheduled_date: date
    reason: str = Field(min_length=1,max_length=255)
    instructions: str | None = None

class FollowupInput(FollowupFields):
    visit_id: int = Field(gt=0)

class FollowupUpdate(DTO):
    scheduled_date: date | None = None
    actual_date: date | None = None
    status: Literal['PENDING','COMPLETED','MISSED','CANCELLED'] | None = None
    reason: str | None = Field(default=None,min_length=1,max_length=255)
    instructions: str | None = None

class ClinicalSections(DTO):
    vitals: VitalInput | None = None
    examination: ExaminationInput | None = None
    diagnoses: list[DiagnosisFields] = []
    prescription: PrescriptionFields | None = None
    followup: FollowupFields | None = None

class CaseBundle(ClinicalSections):
    patient_id: int = Field(gt=0)
    doctor_id: int = Field(gt=0)
    case_date: date = Field(default_factory=clinic_today)
    chief_complaint: str = ''
    present_illness: str | None = None
    case_status: Literal['OPEN','UNDER_REVIEW','FOLLOW_UP','CLOSED'] = 'OPEN'
    priority: Literal['LOW','MEDIUM','HIGH','URGENT'] = 'MEDIUM'
    record_state: Literal['DRAFT','SUBMITTED'] = 'SUBMITTED'
    notes: str | None = None
    symptoms: list[CaseSymptomInput] = []
    history: list[HistoryInput] = []
    allergies: list[AllergyInput] = []
    lifestyle: LifestyleInput | None = None
    @model_validator(mode='after')
    def submission_valid(self):
        if self.case_date>clinic_today(): raise ValueError('Case date cannot be in the future')
        if self.record_state=='SUBMITTED' and not self.chief_complaint: raise ValueError('Chief complaint is required to submit')
        if self.record_state=='DRAFT' and self.case_status!='OPEN': raise ValueError('Drafts must remain open')
        return self

class CaseUpdate(DTO):
    doctor_id: int | None = Field(default=None,gt=0)
    chief_complaint: str | None = Field(default=None,min_length=1)
    present_illness: str | None = None
    case_status: Literal['OPEN','UNDER_REVIEW','FOLLOW_UP','CLOSED'] | None = None
    priority: Literal['LOW','MEDIUM','HIGH','URGENT'] | None = None
    notes: str | None = None

class VisitInput(ClinicalSections):
    case_id: int = Field(gt=0)
    doctor_id: int = Field(gt=0)
    visit_date: datetime = Field(default_factory=utc_now)
    visit_type: Literal['FOLLOW_UP','EMERGENCY','ROUTINE_CHECKUP'] = 'FOLLOW_UP'
    chief_complaint: str = Field(min_length=1)
    doctor_notes: str | None = None
    @field_validator('visit_date')
    @classmethod
    def not_future(cls,v):
        if v.tzinfo: v=v.astimezone(timezone.utc).replace(tzinfo=None)
        if v>utc_now()+timedelta(minutes=1): raise ValueError('A recorded visit cannot be in the future')
        return v

class AppointmentInput(DTO):
    patient_id: int = Field(gt=0)
    doctor_id: int = Field(gt=0)
    appointment_date: date
    start_time: time
    end_time: time
    appointment_type: Literal['CONSULTATION','FOLLOW_UP','ROUTINE_CHECKUP','EMERGENCY'] = 'CONSULTATION'
    status: Literal['SCHEDULED','CONFIRMED','COMPLETED','CANCELLED','NO_SHOW'] = 'SCHEDULED'
    notes: str | None = None
    @model_validator(mode='after')
    def valid_interval(self):
        if self.end_time<=self.start_time: raise ValueError('End time must be after start time on the same day')
        return self

class DoctorInput(DTO):
    username: str = Field(min_length=3,max_length=50)
    login_email: EmailStr
    password: str = Field(min_length=10,max_length=256)
    first_name: str = Field(min_length=1,max_length=50)
    last_name: str = Field(min_length=1,max_length=50)
    specialization: str = Field(min_length=1,max_length=100)
    license_number: str = Field(min_length=1,max_length=50)
    phone: str = Field(min_length=7,max_length=20)
    email: EmailStr

class DoctorUpdate(DTO):
    first_name: str | None = Field(default=None,min_length=1,max_length=50)
    last_name: str | None = Field(default=None,min_length=1,max_length=50)
    specialization: str | None = Field(default=None,min_length=1,max_length=100)
    license_number: str | None = Field(default=None,min_length=1,max_length=50)
    phone: str | None = Field(default=None,min_length=7,max_length=20)
    email: EmailStr | None = None
    is_active: bool | None = None

class UserInput(DTO):
    username: str = Field(min_length=3,max_length=50)
    email: EmailStr
    password: str = Field(min_length=10,max_length=256)
    role: Literal['ADMIN','RECEPTIONIST']

class UserUpdate(DTO):
    is_active: bool

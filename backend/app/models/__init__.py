from .user import User
from .doctor import Doctor
from .patient import Patient
from .case import MedicalCase
from .visit import Visit
from .symptom import Symptom
from .case import CaseSymptom
from .patient import MedicalHistory
from .patient import Allergy
from .patient import LifestyleHistory
from .visit import VitalSign
from .visit import Examination
from .diagnosis import Diagnosis
from .medicine import Medicine
from .prescription import Prescription
from .prescription import PrescriptionMedicine
from .appointment import Appointment
from .followup import FollowUp
from .audit import AuditLog
from .report import MonthlyCaseStatistic

MODELS = {'users': User, 'doctors': Doctor, 'patients': Patient, 'medical_cases': MedicalCase, 'visits': Visit, 'symptoms': Symptom, 'case_symptoms': CaseSymptom, 'medical_history': MedicalHistory, 'allergies': Allergy, 'lifestyle_history': LifestyleHistory, 'vital_signs': VitalSign, 'examinations': Examination, 'diagnoses': Diagnosis, 'medicines': Medicine, 'prescriptions': Prescription, 'prescription_medicines': PrescriptionMedicine, 'appointments': Appointment, 'follow_ups': FollowUp, 'audit_logs': AuditLog, 'monthly_case_statistics': MonthlyCaseStatistic}

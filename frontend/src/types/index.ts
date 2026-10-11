export type Role = "ADMIN" | "DOCTOR" | "RECEPTIONIST";
export interface User {
  user_id: number;
  username: string;
  email: string;
  role: Role;
  is_active: boolean;
}
export type Row = Record<string, unknown>;
export interface Page<T = Row> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
export interface Patient extends Row {
  patient_id: number;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  phone: string;
  email: string | null;
  city: string | null;
  age?: number;
  blood_group: string | null;
}
export interface Doctor extends Row {
  doctor_id: number;
  user_id: number;
  first_name: string;
  last_name: string;
  specialization: string;
}
export interface CatalogSymptom extends Row {
  symptom_id: number;
  symptom_name: string;
  is_active: boolean;
}
export interface CatalogMedicine extends Row {
  medicine_id: number;
  medicine_name: string;
  is_active: boolean;
}
export interface Prescription extends Row {
  prescription_id: number;
  visit_id: number;
  doctor_id: number;
  prescription_date: string;
  notes: string | null;
  medicines: Row[];
}
export interface Visit extends Row {
  visit_id: number;
  case_id: number;
  doctor_id: number;
  visit_date: string;
  visit_type: string;
  chief_complaint: string;
  doctor_notes: string | null;
  vitals: Row | null;
  examination: Row | null;
  diagnoses: Row[];
  prescription: Prescription | null;
  followups: Row[];
}
export interface CaseDetail extends Row {
  case_id: number;
  patient_id: number;
  doctor_id: number;
  case_date: string;
  chief_complaint: string;
  present_illness: string | null;
  case_status: string;
  priority: string;
  record_state: string;
  notes: string | null;
  patient: Patient;
  doctor: Doctor;
  symptoms: Row[];
  visits: Visit[];
}
export interface History {
  cases: CaseDetail[];
  case_total: number;
  medical_history_total: number;
  allergies_total: number;
  medical_history: Row[];
  allergies: Row[];
  lifestyle: Row | null;
  visit_count: number;
  page: number;
  page_size: number;
}
export interface ChartPoint {
  label: string;
  total: number;
}
export interface DashboardData {
  statistics: Record<string, number>;
  charts: Record<string, ChartPoint[]>;
  recent: {
    patients: Patient[];
    appointments: Row[];
    followups: Row[];
    cases?: Row[];
  };
  clinic_date: string;
}
export interface Field {
  key: string;
  label: string;
  type?:
    | "text"
    | "email"
    | "date"
    | "number"
    | "time"
    | "textarea"
    | "password"
    | "select";
  required?: boolean;
  options?: { value: string; label: string }[];
  placeholder?: string;
  step?: string;
  min?: number;
  max?: number;
}
export interface SymptomEntry {
  symptom_id: number;
  severity: string;
  duration: string;
  frequency: string;
  notes: string;
}
export interface MedicineEntry {
  medicine_id: number;
  dosage: string;
  frequency: string;
  route: string;
  duration_days: number;
  instructions: string;
}
export interface CaseFormState {
  patient_id: number;
  doctor_id: number;
  case_date: string;
  chief_complaint: string;
  present_illness: string;
  priority: string;
  notes: string;
  symptoms: SymptomEntry[];
  history: Row[];
  allergies: Row[];
  lifestyle: Row;
  vitals: Row;
  examination: Row;
  diagnoses: Row[];
  prescription: {
    doctor_id: number;
    prescription_date: string;
    notes: string;
    medicines: MedicineEntry[];
  };
  followup: Row;
}

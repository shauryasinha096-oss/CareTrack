import { useState, useEffect, useRef } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Save,
  Plus,
  X,
  FileHeart,
  Users,
  ClipboardList,
  Activity,
  History as HistoryIcon,
  ShieldPlus,
  HeartPulse,
  Stethoscope,
  Pill,
  CalendarDays,
  Leaf,
  LoaderCircle,
} from "lucide-react";
import { useAuth } from "../services/auth";
import { useApi } from "../hooks/useApi";
import { api, write } from "../services/api";
import {
  Fields,
  ErrorBox,
  Spinner,
  Badge,
  useToast,
  today,
  nice,
  DetailGrid,
} from "../components/ui";
import { PageHeading } from "../layouts/Workspace";
import PatientPicker from "../components/PatientPicker";
import { options } from "./Records";
import type {
  CaseFormState,
  Page,
  Doctor,
  CatalogSymptom,
  CatalogMedicine,
  Field,
  Row,
  CaseDetail,
  History,
  MedicineEntry,
} from "../types";
export const historyFields: Field[] = [
  {
    key: "condition_name",
    label: "Fictional condition / episode",
    required: true,
  },
  { key: "diagnosed_date", label: "Recorded diagnosis date", type: "date" },
  { key: "treatment", label: "Fictional previous treatment", type: "textarea" },
  { key: "notes", label: "History notes", type: "textarea" },
];
export const allergyFields: Field[] = [
  { key: "allergen", label: "Fictional allergen", required: true },
  {
    key: "allergy_type",
    label: "Allergy type",
    type: "select",
    required: true,
    options: options(["MEDICATION", "FOOD", "ENVIRONMENTAL", "OTHER"]),
  },
  { key: "reaction", label: "Fictional reaction" },
  {
    key: "severity",
    label: "Severity",
    type: "select",
    required: true,
    options: options(["MILD", "MODERATE", "SEVERE"]),
  },
  { key: "notes", label: "Notes", type: "textarea" },
];
export const lifestyleFields: Field[] = [
  {
    key: "smoking_status",
    label: "Smoking status",
    type: "select",
    options: options(["NEVER", "FORMER", "CURRENT", "UNDISCLOSED"]),
  },
  {
    key: "alcohol_status",
    label: "Alcohol status",
    type: "select",
    options: options(["NEVER", "FORMER", "CURRENT", "UNDISCLOSED"]),
  },
  { key: "exercise_frequency", label: "Exercise frequency" },
  {
    key: "sleep_hours",
    label: "Sleep hours",
    type: "number",
    min: 0,
    max: 24,
    step: "0.1",
  },
  { key: "diet_type", label: "Diet type" },
  { key: "occupation_notes", label: "Occupation notes", type: "textarea" },
];
export const vitalFields: Field[] = [
  {
    key: "temperature",
    label: "Temperature · °C",
    type: "number",
    step: "0.01",
    min: 0.01,
  },
  { key: "systolic_bp", label: "Systolic BP · mmHg", type: "number", min: 1 },
  { key: "diastolic_bp", label: "Diastolic BP · mmHg", type: "number", min: 1 },
  { key: "heart_rate", label: "Heart rate · /min", type: "number", min: 1 },
  {
    key: "respiratory_rate",
    label: "Respiratory rate · /min",
    type: "number",
    min: 1,
  },
  {
    key: "oxygen_saturation",
    label: "Oxygen saturation · %",
    type: "number",
    min: 0,
    max: 100,
    step: "0.01",
  },
  {
    key: "height_cm",
    label: "Height · cm",
    type: "number",
    min: 0.01,
    step: "0.01",
  },
  {
    key: "weight_kg",
    label: "Weight · kg",
    type: "number",
    min: 0.01,
    step: "0.01",
  },
];
export const examFields: Field[] = [
  "general_appearance",
  "cardiovascular_findings",
  "respiratory_findings",
  "neurological_findings",
  "abdominal_findings",
  "skin_findings",
  "other_findings",
].map((key) => ({ key, label: nice(key), type: "textarea" }));
export const diagnosisFields: Field[] = [
  { key: "diagnosis_name", label: "Fictional diagnosis label", required: true },
  {
    key: "diagnosis_type",
    label: "Type",
    type: "select",
    required: true,
    options: options(["PRIMARY", "SECONDARY", "DIFFERENTIAL"]),
  },
  { key: "notes", label: "Educational notes", type: "textarea" },
];
export const followFields: Field[] = [
  { key: "scheduled_date", label: "Follow-up date", type: "date" },
  { key: "reason", label: "Fictional reason" },
  { key: "instructions", label: "Educational instructions", type: "textarea" },
];
const steps = [
  { title: "Patient information", short: "Patient", icon: Users },
  { title: "Chief complaint", short: "Complaint", icon: ClipboardList },
  { title: "Symptoms", short: "Symptoms", icon: Activity },
  { title: "Medical history", short: "History", icon: HistoryIcon },
  { title: "Allergies", short: "Allergies", icon: ShieldPlus },
  { title: "Lifestyle history", short: "Lifestyle", icon: Leaf },
  { title: "Vital signs", short: "Vitals", icon: HeartPulse },
  { title: "Physical examination", short: "Examination", icon: Stethoscope },
  { title: "Diagnosis", short: "Diagnosis", icon: FileHeart },
  { title: "Prescription", short: "Prescription", icon: Pill },
  { title: "Follow-up & submit", short: "Follow-up", icon: CalendarDays },
];
const present = (r: Row) =>
  Object.values(r).some((v) => v !== "" && v !== null && v !== undefined);
const pick = (r: Row, keys: string[]): Row =>
  Object.fromEntries(
    keys
      .filter((k) => r[k] !== undefined)
      .map((k) => [k, r[k] === "" ? null : r[k]]),
  );
export function RepeatingSection({
  title,
  rows,
  fields,
  onChange,
  empty,
}: {
  title: string;
  rows: Row[];
  fields: Field[];
  onChange: (rows: Row[]) => void;
  empty: Row;
}) {
  return (
    <div className="repeat-section">
      {rows.length === 0 && (
        <div className="optional-note">
          No {title.toLowerCase()} entered. Add a fictional record if
          applicable.
        </div>
      )}
      {rows.map((row, index) => (
        <div className="repeat-card" key={index}>
          <div className="repeat-heading">
            <b>
              {title} {index + 1}
            </b>
            <button
              type="button"
              className="icon-button"
              aria-label={`Remove ${title}`}
              onClick={() => onChange(rows.filter((_, i) => i !== index))}
            >
              <X size={16} />
            </button>
          </div>
          <Fields
            fields={fields}
            value={row}
            onChange={(k, v) =>
              onChange(rows.map((r, i) => (i === index ? { ...r, [k]: v } : r)))
            }
          />
        </div>
      ))}
      <button
        type="button"
        className="button secondary"
        onClick={() => onChange([...rows, { ...empty }])}
      >
        <Plus size={16} />
        Add {title.toLowerCase()}
      </button>
    </div>
  );
}
export function PrescriptionEditor({
  lines,
  onChange,
}: {
  lines: MedicineEntry[];
  onChange: (lines: MedicineEntry[]) => void;
}) {
  const [chosen, setChosen] = useState("");
  const catalog = useApi<Page<CatalogMedicine>>(
    "/medicines?page_size=100&sort=medicine_name&direction=asc",
  );
  const lineFields: Field[] = [
    {
      key: "dosage",
      label: "Fictional demo amount",
      required: true,
      placeholder: "Non-actionable demo text",
    },
    { key: "frequency", label: "Fictional frequency", required: true },
    { key: "route", label: "Fictional route", required: true },
    {
      key: "duration_days",
      label: "Demo duration · days",
      type: "number",
      required: true,
      min: 1,
    },
    { key: "instructions", label: "Educational notes", type: "textarea" },
  ];
  return (
    <>
      <div className="form-note">
        <Pill size={17} />
        Fictional catalog and text only. No medical advice or recommended
        regimens.
      </div>
      <div className="inline-add">
        <select
          aria-label="Choose fictional medicine"
          value={chosen}
          onChange={(e) => setChosen(e.target.value)}
        >
          <option value="">Select a fictional product…</option>
          {catalog.data?.items
            .filter(
              (m) =>
                m.is_active &&
                !lines.some((l) => l.medicine_id === m.medicine_id),
            )
            .map((m) => (
              <option key={m.medicine_id} value={m.medicine_id}>
                {m.medicine_name}
              </option>
            ))}
        </select>
        <button
          type="button"
          className="button secondary"
          disabled={!chosen}
          onClick={() => {
            onChange([
              ...lines,
              {
                medicine_id: Number(chosen),
                dosage: "",
                frequency: "",
                route: "",
                duration_days: 1,
                instructions: "",
              },
            ]);
            setChosen("");
          }}
        >
          <Plus size={16} />
          Add product
        </button>
      </div>
      {lines.map((line, i) => (
        <div className="repeat-card" key={line.medicine_id}>
          <div className="repeat-heading">
            <b>
              {catalog.data?.items.find(
                (m) => m.medicine_id === line.medicine_id,
              )?.medicine_name || "Product #" + line.medicine_id}
            </b>
            <button
              type="button"
              className="icon-button"
              aria-label="Remove product"
              onClick={() => onChange(lines.filter((_, j) => j !== i))}
            >
              <X size={16} />
            </button>
          </div>
          <Fields
            fields={lineFields}
            value={line as unknown as Row}
            onChange={(key, value) =>
              onChange(
                lines.map((l, j) => (j === i ? { ...l, [key]: value } : l)),
              )
            }
          />
        </div>
      ))}
    </>
  );
}
function initial(patient = 0): CaseFormState {
  return {
    patient_id: patient,
    doctor_id: 0,
    case_date: today(),
    chief_complaint: "",
    present_illness: "",
    priority: "MEDIUM",
    notes: "",
    symptoms: [],
    history: [],
    allergies: [],
    lifestyle: {},
    vitals: {},
    examination: {},
    diagnoses: [],
    prescription: {
      doctor_id: 0,
      prescription_date: today(),
      notes: "",
      medicines: [],
    },
    followup: {},
  };
}
export default function CaseTaking() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate(),
    toast = useToast();
  const { user } = useAuth();
  const [form, setForm] = useState<CaseFormState>(() =>
      initial(Number(params.get("patient") || 0)),
    ),
    [identity, setIdentity] = useState<number | undefined>(),
    [step, setStep] = useState(0),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [draftLoading, setDraftLoading] = useState(false),
    [symptomSearch, setSymptomSearch] = useState("");
  const loadedDraft = useRef<number>();
  const docs = useApi<Page<Doctor>>("/doctors?page_size=100");
  const symptoms = useApi<Page<CatalogSymptom>>(
    "/symptoms?page_size=100&sort=symptom_name&direction=asc",
  );
  useEffect(() => {
    const own = docs.data?.items.find((d) => d.user_id === user?.user_id);
    if (own)
      setForm((f) => ({
        ...f,
        doctor_id: f.doctor_id || own.doctor_id,
        prescription: {
          ...f.prescription,
          doctor_id: f.prescription.doctor_id || own.doctor_id,
        },
      }));
  }, [docs.data, user]);
  useEffect(() => {
    const id = Number(params.get("draft"));
    if (!id || loadedDraft.current === id) return;
    setDraftLoading(true);
    Promise.all([api<CaseDetail>("/cases/" + id)])
      .then(async ([c]) => {
        if (c.record_state !== "DRAFT")
          throw new Error("This case is already submitted");
        const h = await api<History>(
          "/patients/" + c.patient_id + "/history?page_size=100",
        );
        const v = c.visits.find((v) => v.visit_type === "INITIAL_CONSULTATION");
        setForm({
          patient_id: c.patient_id,
          doctor_id: c.doctor_id,
          case_date: c.case_date,
          chief_complaint: c.chief_complaint,
          present_illness: c.present_illness || "",
          priority: c.priority,
          notes: c.notes || "",
          symptoms: c.symptoms.map((s) => ({
            symptom_id: Number(s.symptom_id),
            severity: String(s.severity),
            duration: String(s.duration || ""),
            frequency: String(s.frequency || ""),
            notes: String(s.notes || ""),
          })),
          history: h.medical_history.map((r) =>
            pick(r, ["history_id", ...historyFields.map((f) => f.key)]),
          ),
          allergies: h.allergies.map((r) =>
            pick(r, ["allergy_id", ...allergyFields.map((f) => f.key)]),
          ),
          lifestyle: pick(
            h.lifestyle || {},
            lifestyleFields.map((f) => f.key),
          ),
          vitals: pick(
            v?.vitals || {},
            vitalFields.map((f) => f.key),
          ),
          examination: pick(
            v?.examination || {},
            examFields.map((f) => f.key),
          ),
          diagnoses: (v?.diagnoses || []).map((d) =>
            pick(
              d,
              diagnosisFields.map((f) => f.key),
            ),
          ),
          prescription: v?.prescription
            ? {
                doctor_id: v.prescription.doctor_id,
                prescription_date: v.prescription.prescription_date,
                notes: v.prescription.notes || "",
                medicines: v.prescription.medicines.map(
                  (m) =>
                    ({
                      ...pick(m, [
                        "medicine_id",
                        "dosage",
                        "frequency",
                        "route",
                        "duration_days",
                        "instructions",
                      ]),
                    }) as unknown as MedicineEntry,
                ),
              }
            : {
                doctor_id: c.doctor_id,
                prescription_date: today(),
                notes: "",
                medicines: [],
              },
          followup: pick(
            v?.followups[0] || {},
            followFields.map((f) => f.key),
          ),
        });
        setIdentity(id);
        loadedDraft.current = id;
      })
      .catch((e) => setError(e.message))
      .finally(() => setDraftLoading(false));
  }, [params]);
  function set<K extends keyof CaseFormState>(key: K, value: CaseFormState[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }
  function section(
    key: "lifestyle" | "vitals" | "examination" | "followup",
    field: string,
    value: unknown,
  ) {
    setForm((f) => ({ ...f, [key]: { ...f[key], [field]: value } }));
  }
  async function save(state: "DRAFT" | "SUBMITTED") {
    setError("");
    if (!form.patient_id || !form.doctor_id) {
      setStep(0);
      setError("Select a patient and assigned doctor first");
      return;
    }
    if (state === "SUBMITTED" && !form.chief_complaint.trim()) {
      setStep(1);
      setError("A chief complaint is required before submission");
      return;
    }
    setBusy(true);
    try {
      const validHistory = form.history.filter((r) =>
          String(r.condition_name || "").trim(),
        ),
        validAllergies = form.allergies.filter((r) =>
          String(r.allergen || "").trim(),
        );
      const validLines = form.prescription.medicines.filter(
        (m) =>
          m.dosage.trim() &&
          m.frequency.trim() &&
          m.route.trim() &&
          m.duration_days > 0,
      );
      if (
        state === "SUBMITTED" &&
        (validLines.length !== form.prescription.medicines.length ||
          validHistory.length !== form.history.length ||
          validAllergies.length !== form.allergies.length)
      )
        throw new Error(
          "Complete or remove incomplete history, allergy, and product entries before submitting",
        );
      const followup =
        present(form.followup) &&
        form.followup.scheduled_date &&
        form.followup.reason
          ? pick(
              form.followup,
              followFields.map((f) => f.key),
            )
          : null;
      if (state === "SUBMITTED" && present(form.followup) && !followup)
        throw new Error(
          "Enter both a date and reason for the follow-up, or clear the section",
        );
      const payload = {
        patient_id: form.patient_id,
        doctor_id: form.doctor_id,
        case_date: form.case_date,
        chief_complaint: form.chief_complaint,
        present_illness: form.present_illness || null,
        priority: form.priority,
        notes: form.notes || null,
        record_state: state,
        case_status: "OPEN",
        symptoms: form.symptoms.map((s) => ({
          ...s,
          duration: s.duration || null,
          frequency: s.frequency || null,
          notes: s.notes || null,
        })),
        history: validHistory.map((r) =>
          pick(r, ["history_id", ...historyFields.map((f) => f.key)]),
        ),
        allergies: validAllergies.map((r) =>
          pick(r, ["allergy_id", ...allergyFields.map((f) => f.key)]),
        ),
        lifestyle: present(form.lifestyle)
          ? pick(
              form.lifestyle,
              lifestyleFields.map((f) => f.key),
            )
          : null,
        vitals: present(form.vitals)
          ? pick(
              form.vitals,
              vitalFields.map((f) => f.key),
            )
          : null,
        examination: present(form.examination)
          ? pick(
              form.examination,
              examFields.map((f) => f.key),
            )
          : null,
        diagnoses: form.diagnoses
          .filter((d) => String(d.diagnosis_name || "").trim())
          .map((d) =>
            pick(
              d,
              diagnosisFields.map((f) => f.key),
            ),
          ),
        prescription: validLines.length
          ? {
              doctor_id: form.prescription.doctor_id || form.doctor_id,
              prescription_date: form.prescription.prescription_date,
              notes: form.prescription.notes || null,
              medicines: validLines.map((m) => ({
                ...m,
                instructions: m.instructions || null,
              })),
            }
          : null,
        followup,
      };
      const r = await write<{
        case_id: number;
        saved_ids: { history: number[]; allergies: number[] };
      }>(
        "/cases" + (identity ? "/" + identity + "/bundle" : ""),
        payload,
        identity ? "PUT" : "POST",
      );
      loadedDraft.current = r.case_id;
      setIdentity(r.case_id);
      setForm((f) => ({
        ...f,
        history: f.history.map((row) => {
          const i = validHistory.indexOf(row);
          return i >= 0 ? { ...row, history_id: r.saved_ids.history[i] } : row;
        }),
        allergies: f.allergies.map((row) => {
          const i = validAllergies.indexOf(row);
          return i >= 0
            ? { ...row, allergy_id: r.saved_ids.allergies[i] }
            : row;
        }),
      }));
      if (state === "SUBMITTED") {
        toast("Case and all entered sections committed to MySQL");
        navigate("/cases/" + r.case_id);
      } else {
        setParams({ draft: String(r.case_id) });
        toast("Draft saved. Complete partial entries before final submission.");
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (draftLoading) return <Spinner />;
  const current = steps[step];
  return (
    <>
      <PageHeading
        title={
          identity ? "Continue your case" : "A new case, one step at a time."
        }
        subtitle="A structured, connected record. All entries must be fictional."
        action={
          <Link className="button secondary" to="/cases">
            <ArrowLeft size={16} />
            Back to cases
          </Link>
        }
      />
      <div className="case-taking-layout">
        <aside className="case-stepper">
          <div className="stepper-heading">
            <FileHeart size={22} />
            <div>
              <b>Case taking</b>
              <small>
                {identity ? `Draft CS-${identity}` : "New fictional case"}
              </small>
            </div>
          </div>
          {steps.map((s, i) => (
            <button
              type="button"
              className={`case-step ${i === step ? "current" : ""} ${i < step ? "past" : ""}`}
              key={s.title}
              onClick={() => setStep(i)}
            >
              <span className="step-number">
                {i < step ? (
                  <Check size={14} />
                ) : (
                  String(i + 1).padStart(2, "0")
                )}
              </span>
              <span>{s.title}</span>
            </button>
          ))}
          <div className="stepper-foot">
            <b>{Math.round(((step + 1) / 11) * 100)}% of steps explored</b>
            <div className="progress-track">
              <span style={{ width: `${((step + 1) / 11) * 100}%` }} />
            </div>
            <small>Optional clinical sections may stay empty.</small>
          </div>
        </aside>
        <section className="panel case-form-panel">
          <div className="case-form-heading">
            <span className="section-icon">
              <current.icon size={22} />
            </span>
            <div>
              <span className="eyebrow">
                STEP {String(step + 1).padStart(2, "0")} OF 11
              </span>
              <h2>{current.title}</h2>
              <p>
                {step === 0
                  ? "Choose the patient and doctor this case belongs to."
                  : "Record fictional observations. Unrecorded values remain empty."}
              </p>
            </div>
            <Badge value="DRAFT" />
          </div>
          {error && <ErrorBox message={error} />}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (step === 10) save("SUBMITTED");
              else setStep((s) => s + 1);
            }}
          >
            <div className="case-form-body">
              {step === 0 && (
                <>
                  <PatientPicker
                    value={form.patient_id}
                    onChange={(id) => set("patient_id", id)}
                  />
                  <Fields
                    fields={[
                      {
                        key: "doctor_id",
                        label: "Assigned doctor",
                        type: "select",
                        required: true,
                        options: docs.data?.items
                          .filter(
                            (d) =>
                              user?.role !== "DOCTOR" ||
                              d.user_id === user.user_id,
                          )
                          .map((d) => ({
                            value: String(d.doctor_id),
                            label: `Dr. ${d.first_name} ${d.last_name} · ${d.specialization}`,
                          })),
                      },
                      {
                        key: "case_date",
                        label: "Case date",
                        type: "date",
                        required: true,
                      },
                    ]}
                    value={form as unknown as Row}
                    onChange={(k, v) =>
                      k === "doctor_id"
                        ? set("doctor_id", Number(v))
                        : set("case_date", String(v))
                    }
                  />
                  <div className="form-note">
                    <Users size={18} />
                    Need a new patient?{" "}
                    <Link to="/patients/new">
                      Register a fictional patient first
                    </Link>
                    .
                  </div>
                </>
              )}
              {step === 1 && (
                <Fields
                  fields={[
                    {
                      key: "chief_complaint",
                      label: "Chief complaint",
                      type: "textarea",
                      required: true,
                      placeholder:
                        "Describe the fictional reason for this encounter…",
                    },
                    {
                      key: "present_illness",
                      label: "Present illness narrative",
                      type: "textarea",
                    },
                    {
                      key: "priority",
                      label: "Administrative priority",
                      type: "select",
                      options: options(["LOW", "MEDIUM", "HIGH", "URGENT"]),
                    },
                    { key: "notes", label: "Case notes", type: "textarea" },
                  ]}
                  value={form as unknown as Row}
                  onChange={(k, v) =>
                    set(
                      k as
                        | "chief_complaint"
                        | "present_illness"
                        | "priority"
                        | "notes",
                      String(v),
                    )
                  }
                />
              )}
              {step === 2 && (
                <>
                  <div className="search-input symptom-search">
                    <Activity size={16} />
                    <input
                      aria-label="Search symptom catalog"
                      placeholder="Find a symptom in the catalog…"
                      value={symptomSearch}
                      onChange={(e) => setSymptomSearch(e.target.value)}
                    />
                  </div>
                  <div className="symptom-grid">
                    {symptoms.data?.items
                      .filter(
                        (s) =>
                          s.is_active &&
                          s.symptom_name
                            .toLowerCase()
                            .includes(symptomSearch.toLowerCase()),
                      )
                      .map((s) => (
                        <label
                          className={
                            form.symptoms.some(
                              (x) => x.symptom_id === s.symptom_id,
                            )
                              ? "selected"
                              : ""
                          }
                          key={s.symptom_id}
                        >
                          <input
                            type="checkbox"
                            checked={form.symptoms.some(
                              (x) => x.symptom_id === s.symptom_id,
                            )}
                            onChange={(e) =>
                              set(
                                "symptoms",
                                e.target.checked
                                  ? [
                                      ...form.symptoms,
                                      {
                                        symptom_id: s.symptom_id,
                                        severity: "MILD",
                                        duration: "",
                                        frequency: "",
                                        notes: "",
                                      },
                                    ]
                                  : form.symptoms.filter(
                                      (x) => x.symptom_id !== s.symptom_id,
                                    ),
                              )
                            }
                          />
                          {s.symptom_name}
                        </label>
                      ))}
                  </div>
                  {form.symptoms.map((s, i) => (
                    <div className="repeat-card" key={s.symptom_id}>
                      <div className="repeat-heading">
                        <b>
                          {
                            symptoms.data?.items.find(
                              (x) => x.symptom_id === s.symptom_id,
                            )?.symptom_name
                          }
                        </b>
                      </div>
                      <Fields
                        fields={[
                          {
                            key: "severity",
                            label: "Severity",
                            type: "select",
                            options: options(["MILD", "MODERATE", "SEVERE"]),
                          },
                          { key: "duration", label: "Duration" },
                          { key: "frequency", label: "Frequency" },
                          {
                            key: "notes",
                            label: "Observation notes",
                            type: "textarea",
                          },
                        ]}
                        value={s as unknown as Row}
                        onChange={(k, v) =>
                          set(
                            "symptoms",
                            form.symptoms.map((x, j) =>
                              j === i ? { ...x, [k]: String(v) } : x,
                            ),
                          )
                        }
                      />
                    </div>
                  ))}
                </>
              )}
              {step === 3 && (
                <RepeatingSection
                  title="History episode"
                  rows={form.history}
                  fields={historyFields}
                  empty={{}}
                  onChange={(v) => set("history", v)}
                />
              )}
              {step === 4 && (
                <RepeatingSection
                  title="Allergy record"
                  rows={form.allergies}
                  fields={allergyFields}
                  empty={{ allergy_type: "OTHER", severity: "MILD" }}
                  onChange={(v) => set("allergies", v)}
                />
              )}
              {step === 5 && (
                <>
                  <Fields
                    fields={lifestyleFields}
                    value={form.lifestyle}
                    onChange={(k, v) => section("lifestyle", k, v)}
                  />
                  <div className="optional-note">
                    This is the patient’s current lifestyle snapshot.
                    Encounter-specific changes can be described in visit notes.
                  </div>
                </>
              )}
              {step === 6 && (
                <>
                  <Fields
                    fields={vitalFields}
                    value={form.vitals}
                    onChange={(k, v) => section("vitals", k, v)}
                  />
                  <div className="calculated-value">
                    <Activity size={18} />
                    <span>BMI is calculated from saved height and weight.</span>
                    {Number(form.vitals.height_cm) > 0 &&
                      Number(form.vitals.weight_kg) > 0 && (
                        <b>
                          {(
                            Number(form.vitals.weight_kg) /
                            (Number(form.vitals.height_cm) / 100) ** 2
                          ).toFixed(2)}
                          <small>preview</small>
                        </b>
                      )}
                  </div>
                </>
              )}
              {step === 7 && (
                <Fields
                  fields={examFields}
                  value={form.examination}
                  onChange={(k, v) => section("examination", k, v)}
                />
              )}
              {step === 8 && (
                <RepeatingSection
                  title="Diagnosis observation"
                  rows={form.diagnoses}
                  fields={diagnosisFields}
                  empty={{ diagnosis_type: "PRIMARY" }}
                  onChange={(v) => set("diagnoses", v)}
                />
              )}
              {step === 9 && (
                <>
                  <Fields
                    fields={[
                      {
                        key: "doctor_id",
                        label: "Prescribing doctor",
                        type: "select",
                        required: form.prescription.medicines.length > 0,
                        options: docs.data?.items
                          .filter(
                            (d) =>
                              user?.role !== "DOCTOR" ||
                              d.user_id === user.user_id,
                          )
                          .map((d) => ({
                            value: String(d.doctor_id),
                            label: `Dr. ${d.first_name} ${d.last_name}`,
                          })),
                      },
                      {
                        key: "prescription_date",
                        label: "Prescription date",
                        type: "date",
                      },
                      {
                        key: "notes",
                        label: "Document notes",
                        type: "textarea",
                      },
                    ]}
                    value={form.prescription as unknown as Row}
                    onChange={(k, v) =>
                      set("prescription", {
                        ...form.prescription,
                        [k]: k === "doctor_id" ? Number(v) : v,
                      })
                    }
                  />
                  <PrescriptionEditor
                    lines={form.prescription.medicines}
                    onChange={(lines) =>
                      set("prescription", {
                        ...form.prescription,
                        medicines: lines,
                      })
                    }
                  />
                </>
              )}
              {step === 10 && (
                <>
                  <Fields
                    fields={followFields}
                    value={form.followup}
                    onChange={(k, v) => section("followup", k, v)}
                  />
                  <div className="submission-summary">
                    <h3>Ready to connect the record?</h3>
                    <p>
                      Your case and entered sections are committed together in
                      one MySQL transaction. If a section fails validation, the
                      submission rolls back.
                    </p>
                    <div>
                      <span>
                        <b>{form.symptoms.length}</b> symptoms
                      </span>
                      <span>
                        <b>{form.diagnoses.length}</b> diagnosis observations
                      </span>
                      <span>
                        <b>{form.prescription.medicines.length}</b> fictional
                        products
                      </span>
                    </div>
                  </div>
                </>
              )}
            </div>
            <div className="case-form-footer">
              <button
                type="button"
                className="button secondary"
                disabled={step === 0 || busy}
                onClick={() => setStep((s) => s - 1)}
              >
                <ArrowLeft size={16} />
                Back
              </button>
              <button
                type="button"
                className="button secondary draft-button"
                disabled={busy}
                onClick={() => save("DRAFT")}
              >
                <Save size={16} />
                {busy ? "Saving…" : "Save draft"}
              </button>
              <button className="button primary" disabled={busy}>
                {step === 10 ? (
                  <>
                    <Check size={16} />
                    Submit case
                  </>
                ) : (
                  <>
                    Next step
                    <ArrowRight size={16} />
                  </>
                )}
              </button>
            </div>
          </form>
        </section>
      </div>
    </>
  );
}

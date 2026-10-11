import { useState, useEffect } from "react";
import {
  Link,
  useLocation,
  useNavigate,
  useSearchParams,
} from "react-router-dom";
import {
  Plus,
  Search,
  ArrowUpDown,
  Eye,
  Pencil,
  Trash2,
  CalendarDays,
  Check,
  X,
  FolderHeart,
  ChevronRight,
  Filter,
} from "lucide-react";
import { useApi } from "../hooks/useApi";
import { useAuth } from "../services/auth";
import { api, write, query } from "../services/api";
import {
  Badge,
  Spinner,
  ErrorBox,
  Empty,
  Pagination,
  FormModal,
  Modal,
  Fields,
  nice,
  dateLabel,
  initials,
  useToast,
  today,
} from "../components/ui";
import { PageHeading } from "../layouts/Workspace";
import PatientPicker from "../components/PatientPicker";
import type { Page, Row, Field, Doctor } from "../types";
export const options = (values: string[]) =>
  values.map((v) => ({ value: v, label: nice(v) }));
export const patientFields: Field[] = [
  { key: "first_name", label: "First name", required: true },
  { key: "last_name", label: "Last name", required: true },
  {
    key: "date_of_birth",
    label: "Date of birth",
    type: "date",
    required: true,
  },
  {
    key: "gender",
    label: "Gender",
    type: "select",
    required: true,
    options: options(["FEMALE", "MALE", "NON_BINARY", "OTHER", "UNDISCLOSED"]),
  },
  {
    key: "blood_group",
    label: "Blood group",
    type: "select",
    options: options(["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]),
  },
  {
    key: "phone",
    label: "Fictional phone number",
    required: true,
    placeholder: "0000000000",
  },
  {
    key: "email",
    label: "Demo email",
    type: "email",
    placeholder: "fictional.name@example.com",
  },
  { key: "city", label: "City" },
  { key: "address", label: "Address", type: "textarea" },
  { key: "occupation", label: "Occupation" },
  {
    key: "marital_status",
    label: "Marital status",
    type: "select",
    options: options([
      "SINGLE",
      "MARRIED",
      "DIVORCED",
      "WIDOWED",
      "UNDISCLOSED",
    ]),
  },
  { key: "emergency_contact_name", label: "Fictional emergency contact" },
  { key: "emergency_contact_phone", label: "Emergency contact phone" },
];
const doctorFields: Field[] = [
  { key: "first_name", label: "First name", required: true },
  { key: "last_name", label: "Last name", required: true },
  { key: "specialization", label: "Specialization", required: true },
  { key: "license_number", label: "Fictional license number", required: true },
  { key: "phone", label: "Fictional phone", required: true },
  {
    key: "email",
    label: "Professional demo email",
    type: "email",
    required: true,
  },
];
const doctorAccount: Field[] = [
  { key: "username", label: "Login username", required: true },
  {
    key: "login_email",
    label: "Login demo email",
    type: "email",
    required: true,
  },
  {
    key: "password",
    label: "Initial password (10+ characters)",
    type: "password",
    required: true,
  },
  ...doctorFields,
];
const configs: Record<
  string,
  {
    title: string;
    subtitle: string;
    id: string;
    columns: [string, string][];
    fields?: Field[];
    statuses?: string[];
    clinical?: boolean;
    adminCreate?: boolean;
  }
> = {
  patients: {
    title: "Patients",
    subtitle: "Every fictional patient, thoughtfully organized.",
    id: "patient_id",
    columns: [
      ["name", "Patient"],
      ["patient_id", "Patient ID"],
      ["gender", "Gender"],
      ["phone", "Phone"],
      ["city", "City"],
      ["created_at", "Registered"],
    ],
    fields: patientFields,
  },
  cases: {
    title: "Patient cases",
    subtitle: "A connected view of each case and its progress.",
    id: "case_id",
    columns: [
      ["case_id", "Case ID"],
      ["patient_name", "Patient"],
      ["chief_complaint", "Chief complaint"],
      ["doctor_name", "Assigned doctor"],
      ["record_state", "Record"],
      ["case_status", "Status"],
      ["priority", "Priority"],
    ],
    statuses: ["OPEN", "UNDER_REVIEW", "FOLLOW_UP", "CLOSED"],
    clinical: true,
  },
  visits: {
    title: "Visit history",
    subtitle: "Individual encounters, connected to the bigger picture.",
    id: "visit_id",
    columns: [
      ["visit_id", "Visit ID"],
      ["patient_name", "Patient"],
      ["visit_date", "Visit date"],
      ["visit_type", "Visit type"],
      ["chief_complaint", "Chief complaint"],
    ],
    clinical: true,
  },
  appointments: {
    title: "Appointments",
    subtitle: "Keep your learning clinic’s schedule in clear view.",
    id: "appointment_id",
    columns: [
      ["appointment_id", "Booking"],
      ["patient_name", "Patient"],
      ["doctor_name", "Doctor"],
      ["appointment_date", "Date"],
      ["start_time", "Start · IST"],
      ["end_time", "End · IST"],
      ["status", "Status"],
    ],
    statuses: ["SCHEDULED", "CONFIRMED", "COMPLETED", "CANCELLED", "NO_SHOW"],
  },
  followups: {
    title: "Follow-ups",
    subtitle: "Stay connected to what comes next in each fictional case.",
    id: "follow_up_id",
    columns: [
      ["follow_up_id", "Plan"],
      ["patient_name", "Patient"],
      ["doctor_name", "Assigned doctor"],
      ["scheduled_date", "Scheduled"],
      ["actual_date", "Completed"],
      ["status", "Status"],
    ],
    statuses: ["PENDING", "COMPLETED", "MISSED", "CANCELLED"],
  },
  diagnoses: {
    title: "Diagnosis observations",
    subtitle: "Fictional visit labels for your educational records.",
    id: "diagnosis_id",
    columns: [
      ["diagnosis_id", "Record"],
      ["patient_name", "Patient"],
      ["visit_id", "Visit"],
      ["diagnosis_name", "Fictional diagnosis"],
      ["diagnosis_type", "Type"],
    ],
    fields: [
      {
        key: "visit_id",
        label: "Visit ID",
        type: "number",
        required: true,
        min: 1,
      },
      {
        key: "diagnosis_name",
        label: "Fictional diagnosis label",
        required: true,
      },
      {
        key: "diagnosis_type",
        label: "Type",
        type: "select",
        required: true,
        options: options(["PRIMARY", "SECONDARY", "DIFFERENTIAL"]),
      },
      { key: "notes", label: "Educational notes", type: "textarea" },
    ],
    clinical: true,
  },
  medicines: {
    title: "Medicine library",
    subtitle: "A fictional product catalog. No treatment recommendations.",
    id: "medicine_id",
    columns: [
      ["medicine_code", "Code"],
      ["medicine_name", "Fictional product"],
      ["generic_name", "Fictional compound"],
      ["medicine_type", "Type"],
      ["strength", "Strength"],
      ["is_active", "Active"],
    ],
    fields: [
      {
        key: "medicine_code",
        label: "Unique demo product code",
        required: true,
      },
      {
        key: "medicine_name",
        label: "Fictional medicine name",
        required: true,
      },
      { key: "generic_name", label: "Fictional compound", required: true },
      { key: "manufacturer", label: "Fictional manufacturer", required: true },
      {
        key: "medicine_type",
        label: "Category",
        type: "select",
        required: true,
        options: options([
          "TABLET",
          "CAPSULE",
          "SYRUP",
          "INJECTION",
          "CREAM",
          "DROPS",
        ]),
      },
      { key: "strength", label: "Demo strength", required: true },
      { key: "form", label: "Product presentation", required: true },
      {
        key: "is_active",
        label: "Active",
        type: "select",
        options: [
          { value: "true", label: "Active" },
          { value: "false", label: "Inactive" },
        ],
      },
    ],
    clinical: true,
    adminCreate: true,
  },
  symptoms: {
    title: "Symptom library",
    subtitle: "A shared vocabulary for structured case observations.",
    id: "symptom_id",
    columns: [
      ["symptom_id", "ID"],
      ["symptom_name", "Symptom"],
      ["description", "Description"],
      ["is_active", "Active"],
    ],
    fields: [
      { key: "symptom_name", label: "Symptom name", required: true },
      { key: "description", label: "Description", type: "textarea" },
      {
        key: "is_active",
        label: "Active",
        type: "select",
        options: [
          { value: "true", label: "Active" },
          { value: "false", label: "Inactive" },
        ],
      },
    ],
    clinical: true,
    adminCreate: true,
  },
  prescriptions: {
    title: "Prescriptions",
    subtitle:
      "Fictional documents and product associations, connected to visits.",
    id: "prescription_id",
    columns: [
      ["prescription_id", "Document"],
      ["patient_name", "Patient"],
      ["visit_id", "Visit"],
      ["doctor_name", "Case doctor"],
      ["prescription_date", "Date"],
    ],
    clinical: true,
  },
  doctors: {
    title: "Your doctors",
    subtitle: "The fictional care team behind your learning workspace.",
    id: "doctor_id",
    columns: [
      ["name", "Doctor"],
      ["specialization", "Specialization"],
      ["license_number", "Demo license"],
      ["email", "Professional email"],
      ["phone", "Phone"],
    ],
    fields: doctorFields,
    adminCreate: true,
  },
  "audit-logs": {
    title: "Audit trail",
    subtitle: "Attributable database operations, recorded as they happen.",
    id: "audit_id",
    columns: [
      ["audit_id", "Event"],
      ["actor_username", "Actor"],
      ["action", "Action"],
      ["entity_type", "Entity"],
      ["entity_id", "Record ID"],
      ["description", "Operation"],
      ["created_at", "Timestamp"],
    ],
  },
  users: {
    title: "User accounts",
    subtitle: "Manage access to your educational workspace.",
    id: "user_id",
    columns: [
      ["username", "Username"],
      ["email", "Login email"],
      ["role", "Role"],
      ["is_active", "Active"],
    ],
    fields: [
      { key: "username", label: "Username", required: true },
      { key: "email", label: "Login email", type: "email", required: true },
      {
        key: "password",
        label: "Password (10+ characters)",
        type: "password",
        required: true,
      },
      {
        key: "role",
        label: "Role",
        type: "select",
        required: true,
        options: options(["ADMIN", "RECEPTIONIST"]),
      },
    ],
    adminCreate: true,
  },
};
export function cleanFields(value: Row, fields: Field[]): Row {
  const out: Row = {};
  for (const f of fields) {
    const v = value[f.key];
    if (v === undefined || v === "") {
      if (!f.required) out[f.key] = null;
      continue;
    }
    out[f.key] = f.key.endsWith("_id")
      ? Number(v)
      : f.key === "is_active"
        ? String(v) === "true"
        : v;
  }
  return out;
}
export function AppointmentModal({
  initial,
  onClose,
  onSaved,
}: {
  initial?: Row;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { user } = useAuth();
  const docs = useApi<Page<Doctor>>("/doctors?page_size=100");
  const [value, setValue] = useState<Row>({
      ...initial,
      appointment_date: initial?.appointment_date || today(),
      appointment_type: initial?.appointment_type || "CONSULTATION",
      status: initial?.status || "SCHEDULED",
    }),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const fields: Field[] = [
    {
      key: "doctor_id",
      label: "Doctor",
      type: "select",
      required: true,
      options: docs.data?.items
        .filter((d) => user?.role !== "DOCTOR" || d.user_id === user.user_id)
        .map((d) => ({
          value: String(d.doctor_id),
          label: `Dr. ${d.first_name} ${d.last_name}`,
        })),
    },
    {
      key: "appointment_date",
      label: "Appointment date",
      type: "date",
      required: true,
    },
    {
      key: "start_time",
      label: "Start time · IST",
      type: "time",
      required: true,
    },
    { key: "end_time", label: "End time · IST", type: "time", required: true },
    {
      key: "appointment_type",
      label: "Appointment type",
      type: "select",
      required: true,
      options: options([
        "CONSULTATION",
        "FOLLOW_UP",
        "ROUTINE_CHECKUP",
        "EMERGENCY",
      ]),
    },
    {
      key: "status",
      label: "Status",
      type: "select",
      required: true,
      options: options(configs.appointments.statuses!),
    },
  ];
  return (
    <Modal
      title={initial ? "Edit appointment" : "Schedule appointment"}
      onClose={onClose}
      wide
    >
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError("");
          try {
            if (!value.patient_id) throw new Error("Select a patient");
            await write(
              "/appointments" + (initial ? "/" + initial.appointment_id : ""),
              {
                patient_id: Number(value.patient_id),
                ...cleanFields(value, fields),
              },
              initial ? "PUT" : "POST",
            );
            onSaved();
          } catch (e) {
            setError((e as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        {error && <ErrorBox message={error} />}
        <PatientPicker
          value={Number(value.patient_id || 0)}
          onChange={(id) => setValue((v) => ({ ...v, patient_id: id }))}
        />
        <Fields
          fields={fields}
          value={value}
          onChange={(k, v) => setValue((p) => ({ ...p, [k]: v }))}
        />
        <div className="form-note">
          <CalendarDays size={17} /> Times use Asia/Kolkata. Overlapping
          appointments for the same doctor are rejected.
        </div>
        <div className="modal-footer">
          <button type="button" className="button secondary" onClick={onClose}>
            Cancel
          </button>
          <button disabled={busy} className="button primary">
            {busy ? "Saving…" : "Save appointment"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
export default function Records({ resource }: { resource: string }) {
  const config = configs[resource];
  const { user } = useAuth();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const [q, setQ] = useState(params.get("q") || ""),
    [page, setPage] = useState(1),
    [status, setStatus] = useState(""),
    [doctor, setDoctor] = useState(""),
    [day, setDay] = useState(""),
    [sort, setSort] = useState(""),
    [direction, setDirection] = useState("desc"),
    [editing, setEditing] = useState<Row | null>(null),
    [adding, setAdding] = useState(false),
    [confirm, setConfirm] = useState<Row | null>(null),
    [actionError, setActionError] = useState("");
  const toast = useToast();
  const doctors = useApi<Page<Doctor>>(
    ["cases", "appointments", "followups"].includes(resource)
      ? "/doctors?page_size=100"
      : null,
  );
  const response = useApi<Page>(
    "/" +
      resource +
      "?" +
      query({
        q,
        page,
        page_size: 15,
        status,
        doctor_id: doctor,
        date_from: day,
        date_to: day,
        sort,
        direction,
      }),
  );
  useEffect(() => {
    setPage(1);
  }, [q, status, doctor, day, sort, direction]);
  useEffect(() => {
    setQ(params.get("q") || "");
  }, [params]);
  const canCreate =
    (!config.adminCreate || user?.role === "ADMIN") &&
    (resource !== "followups" || user?.role !== "RECEPTIONIST") &&
    !["audit-logs", "prescriptions"].includes(resource);
  function saved() {
    setEditing(null);
    setAdding(false);
    response.refresh();
    toast("Record saved to MySQL");
  }
  function add() {
    if (resource === "cases") navigate("/cases/new");
    else if (resource === "visits") setAdding(true);
    else if (resource === "followups") setAdding(true);
    else setAdding(true);
  }
  const visitFields: Field[] = [
    {
      key: "case_id",
      label: "Submitted case ID",
      type: "number",
      required: true,
      min: 1,
    },
    {
      key: "doctor_id",
      label: "Attending doctor ID",
      type: "number",
      required: true,
      min: 1,
    },
    {
      key: "visit_type",
      label: "Visit type",
      type: "select",
      required: true,
      options: options(["FOLLOW_UP", "EMERGENCY", "ROUTINE_CHECKUP"]),
    },
    {
      key: "chief_complaint",
      label: "Chief complaint",
      type: "textarea",
      required: true,
    },
    { key: "doctor_notes", label: "Fictional visit notes", type: "textarea" },
  ];
  const followFields: Field[] = [
    ...(!editing
      ? [
          {
            key: "visit_id",
            label: "Originating visit ID",
            type: "number" as const,
            required: true,
            min: 1,
          },
        ]
      : []),
    {
      key: "scheduled_date",
      label: "Scheduled date",
      type: "date",
      required: true,
    },
    { key: "reason", label: "Fictional follow-up reason", required: true },
    {
      key: "instructions",
      label: "Educational instructions",
      type: "textarea",
    },
    ...(editing
      ? [
          {
            key: "status",
            label: "Status",
            type: "select" as const,
            required: true,
            options: options(configs.followups.statuses!),
          },
        ]
      : []),
  ];
  const fields =
    resource === "visits"
      ? visitFields
      : resource === "followups"
        ? followFields
        : resource === "doctors" && !editing
          ? doctorAccount
          : config.fields || [];
  function view(row: Row) {
    if (resource === "patients") navigate("/patients/" + row.patient_id);
    else if (resource === "cases") navigate("/cases/" + row.case_id);
    else if (resource === "visits") navigate("/visits/" + row.visit_id);
    else if (resource === "prescriptions")
      navigate("/prescriptions/" + row.prescription_id);
  }
  return (
    <>
      <PageHeading
        title={config.title}
        subtitle={config.subtitle}
        action={
          canCreate ? (
            <button className="button primary" onClick={add}>
              <Plus size={17} />
              {resource === "patients"
                ? "Register patient"
                : resource === "appointments"
                  ? "Schedule appointment"
                  : resource === "cases"
                    ? "New case"
                    : `Add ${resource === "followups" ? "follow-up" : resource.replace(/s$/, "")}`}
            </button>
          ) : resource === "prescriptions" ? (
            <Link className="button primary" to="/prescriptions/new">
              <Plus size={17} />
              Create prescription
            </Link>
          ) : undefined
        }
      />
      {actionError && <ErrorBox message={actionError} />}
      <section className="panel records-panel">
        <div className="records-tabs">
          <span className="selected">
            All {config.title.toLowerCase()}{" "}
            <b>{response.data?.total ?? "…"}</b>
          </span>
          <span className="live-label">
            <i />
            Database connected
          </span>
        </div>
        <div className="table-toolbar">
          <div className="search-input">
            <Search size={17} />
            <input
              aria-label={`Search ${config.title}`}
              value={q}
              placeholder={`Search ${config.title.toLowerCase()}…`}
              onChange={(e) => setQ(e.target.value)}
            />
            {q && (
              <button
                className="icon-button"
                aria-label="Clear search"
                onClick={() => setQ("")}
              >
                <X size={14} />
              </button>
            )}
          </div>
          <div className="table-filters">
            {config.statuses && (
              <select
                aria-label="Filter status"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                <option value="">All statuses</option>
                {config.statuses.map((s) => (
                  <option key={s} value={s}>
                    {nice(s)}
                  </option>
                ))}
              </select>
            )}
            {doctors.data && (
              <select
                aria-label="Filter doctor"
                value={doctor}
                onChange={(e) => setDoctor(e.target.value)}
              >
                <option value="">All doctors</option>
                {doctors.data.items.map((d) => (
                  <option value={d.doctor_id} key={d.doctor_id}>
                    Dr. {d.first_name} {d.last_name}
                  </option>
                ))}
              </select>
            )}
            {resource === "appointments" && (
              <input
                aria-label="Filter date"
                type="date"
                value={day}
                onChange={(e) => setDay(e.target.value)}
              />
            )}
            <select
              aria-label="Sort records"
              value={sort}
              onChange={(e) => setSort(e.target.value)}
            >
              <option value="">Latest first</option>
              {config.columns
                .filter(
                  ([k]) =>
                    k !== "name" &&
                    !["patient_name", "doctor_name"].includes(k),
                )
                .map(([k, l]) => (
                  <option value={k} key={k}>
                    {l}
                  </option>
                ))}
            </select>
            <button
              className="icon-button sort-button"
              aria-label="Toggle sort direction"
              onClick={() =>
                setDirection((d) => (d === "asc" ? "desc" : "asc"))
              }
            >
              <ArrowUpDown size={16} />
            </button>
          </div>
        </div>
        {response.loading ? (
          <Spinner />
        ) : response.error ? (
          <ErrorBox message={response.error} retry={response.refresh} />
        ) : !response.data?.items.length ? (
          <Empty />
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  {config.columns.map(([key, label]) => (
                    <th key={key}>{label}</th>
                  ))}
                  <th className="right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {response.data.items.map((row) => (
                  <tr key={String(row[config.id])}>
                    {config.columns.map(([key]) => (
                      <td key={key}>
                        {key === "name" ? (
                          <button
                            className="patient-cell"
                            onClick={() => resource === "patients" && view(row)}
                          >
                            <span className="avatar small">
                              {initials(row.first_name, row.last_name)}
                            </span>
                            <span>
                              <b>
                                {String(row.first_name)} {String(row.last_name)}
                              </b>
                              <small>
                                {resource === "patients"
                                  ? String(row.email || "No email recorded")
                                  : "Dr. · fictional profile"}
                              </small>
                            </span>
                          </button>
                        ) : [
                            "status",
                            "case_status",
                            "priority",
                            "record_state",
                            "diagnosis_type",
                            "role",
                          ].includes(key) ? (
                          <Badge value={row[key]} />
                        ) : key === "is_active" ? (
                          <Badge value={row[key] ? "ACTIVE" : "INACTIVE"} />
                        ) : key.endsWith("_date") || key === "date_of_birth" ? (
                          dateLabel(row[key])
                        ) : key === "created_at" ? (
                          <span>{dateLabel(row[key])}</span>
                        ) : key.endsWith("_id") ? (
                          <span className="record-id">
                            {(
                              {
                                patient_id: "PT",
                                case_id: "CS",
                                visit_id: "VS",
                                prescription_id: "RX",
                                follow_up_id: "FU",
                                appointment_id: "AP",
                              } as Record<string, string>
                            )[key] || "#"}
                            -{String(row[key]).padStart(4, "0")}
                          </span>
                        ) : key.includes("_time") ? (
                          String(row[key]).slice(0, 5)
                        ) : (
                          <span
                            className={
                              key === "chief_complaint" || key === "description"
                                ? "ellipsis"
                                : ""
                            }
                          >
                            {String(row[key] ?? "—")}
                          </span>
                        )}
                      </td>
                    ))}
                    <td>
                      <div className="row-actions">
                        {[
                          "patients",
                          "cases",
                          "visits",
                          "prescriptions",
                        ].includes(resource) && (
                          <button
                            className="icon-button"
                            aria-label="View record"
                            onClick={() => view(row)}
                          >
                            <Eye size={16} />
                          </button>
                        )}
                        {resource === "cases" &&
                          row.record_state === "DRAFT" && (
                            <Link
                              className="text-button"
                              to={"/cases/new?draft=" + row.case_id}
                            >
                              Resume
                            </Link>
                          )}
                        {((config.fields &&
                          resource !== "users" &&
                          resource !== "diagnoses" &&
                          (!config.adminCreate || user?.role === "ADMIN")) ||
                          (resource === "appointments" &&
                            !["COMPLETED", "NO_SHOW"].includes(
                              String(row.status),
                            )) ||
                          (resource === "followups" &&
                            user?.role !== "RECEPTIONIST" &&
                            !["COMPLETED", "CANCELLED"].includes(
                              String(row.status),
                            ))) && (
                          <button
                            className="icon-button"
                            aria-label="Edit record"
                            onClick={() => setEditing(row)}
                          >
                            <Pencil size={15} />
                          </button>
                        )}
                        {resource === "users" && (
                          <button
                            className="text-button"
                            onClick={async () => {
                              try {
                                await write(
                                  "/users/" + row.user_id,
                                  { is_active: !row.is_active },
                                  "PUT",
                                );
                                saved();
                              } catch (e) {
                                setActionError((e as Error).message);
                              }
                            }}
                          >
                            {row.is_active ? "Deactivate" : "Activate"}
                          </button>
                        )}
                        {((resource === "patients" && user?.role === "ADMIN") ||
                          (resource === "appointments" &&
                            !["CANCELLED", "COMPLETED", "NO_SHOW"].includes(
                              String(row.status),
                            ))) && (
                          <button
                            className="icon-button danger"
                            aria-label={
                              resource === "appointments"
                                ? "Cancel appointment"
                                : "Delete unused patient"
                            }
                            onClick={() => setConfirm(row)}
                          >
                            {resource === "appointments" ? (
                              <X size={15} />
                            ) : (
                              <Trash2 size={15} />
                            )}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {response.data && (
          <Pagination
            page={page}
            total={response.data.total}
            size={15}
            onChange={setPage}
          />
        )}
      </section>
      {(adding || editing) &&
        (resource === "appointments" ? (
          <AppointmentModal
            initial={editing || undefined}
            onClose={() => {
              setAdding(false);
              setEditing(null);
            }}
            onSaved={saved}
          />
        ) : (
          <FormModal
            title={
              (editing ? "Edit " : "Add ") +
              (resource === "patients"
                ? "fictional patient"
                : config.title.toLowerCase())
            }
            fields={fields}
            initial={
              editing
                ? Object.fromEntries(fields.map((f) => [f.key, editing[f.key]]))
                : {
                    is_active: "true",
                    diagnosis_type: "PRIMARY",
                    visit_type: "FOLLOW_UP",
                    status: "PENDING",
                    doctor_id: doctors.data?.items.find(
                      (d) => d.user_id === user?.user_id,
                    )?.doctor_id,
                  }
            }
            onClose={() => {
              setAdding(false);
              setEditing(null);
            }}
            onSubmit={async (value) => {
              await write(
                "/" + resource + (editing ? "/" + editing[config.id] : ""),
                cleanFields(value, fields),
                editing ? "PUT" : "POST",
              );
              saved();
            }}
          />
        ))}
      {confirm && (
        <Modal
          title={
            resource === "appointments"
              ? "Cancel this appointment?"
              : "Delete this unused patient?"
          }
          onClose={() => setConfirm(null)}
        >
          <p className="confirmation-copy">
            {resource === "appointments"
              ? "The booking will remain in history with a cancelled status."
              : "Patients with cases or appointments are protected by foreign keys and cannot be deleted."}
          </p>
          <div className="modal-footer">
            <button
              className="button secondary"
              onClick={() => setConfirm(null)}
            >
              Keep record
            </button>
            <button
              className="button danger-button"
              onClick={async () => {
                try {
                  await api("/" + resource + "/" + confirm[config.id], {
                    method: "DELETE",
                  });
                  setConfirm(null);
                  response.refresh();
                  toast(
                    resource === "appointments"
                      ? "Appointment cancelled"
                      : "Unused patient deleted",
                  );
                } catch (e) {
                  setConfirm(null);
                  setActionError((e as Error).message);
                }
              }}
            >
              Confirm{" "}
              {resource === "appointments" ? "cancellation" : "deletion"}
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}

import { useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Plus,
  Pencil,
  Printer,
  FileHeart,
  CalendarDays,
} from "lucide-react";
import { useApi } from "../hooks/useApi";
import { useAuth } from "../services/auth";
import { write } from "../services/api";
import {
  Badge,
  Spinner,
  ErrorBox,
  Empty,
  DetailGrid,
  dateLabel,
  FormModal,
  useToast,
  Fields,
  today,
} from "../components/ui";
import { PageHeading } from "../layouts/Workspace";
import { VisitCard } from "./PatientProfile";
import { options, cleanFields, patientFields } from "./Records";
import {
  PrescriptionEditor,
  diagnosisFields,
  followFields,
  vitalFields,
  examFields,
} from "./CaseTaking";
import type {
  CaseDetail,
  Visit,
  Prescription,
  Page,
  Doctor,
  Field,
  Row,
  MedicineEntry,
} from "../types";
export function NewPatient() {
  const navigate = useNavigate(),
    toast = useToast();
  const [value, setValue] = useState<Row>({ gender: "UNDISCLOSED" }),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  return (
    <>
      <PageHeading
        title="A new patient starts here."
        subtitle="Register a fictional patient in your learning workspace."
      />
      <section className="panel standalone-form">
        <div className="panel-heading">
          <div>
            <h2>Patient registration</h2>
            <p>Required details are marked with an asterisk.</p>
          </div>
          <FileHeart size={22} />
        </div>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setError("");
            setBusy(true);
            try {
              const p = await write<{ patient_id: number }>(
                "/patients",
                cleanFields(value, patientFields),
              );
              toast("Fictional patient registered in MySQL");
              navigate("/patients/" + p.patient_id);
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <div className="panel-content">
            {error && <ErrorBox message={error} />}
            <Fields
              fields={patientFields}
              value={value}
              onChange={(k, v) => setValue((p) => ({ ...p, [k]: v }))}
            />
          </div>
          <div className="modal-footer">
            <Link className="button secondary" to="/patients">
              Cancel
            </Link>
            <button className="button primary" disabled={busy}>
              {busy ? "Registering…" : "Register patient"}
            </button>
          </div>
        </form>
      </section>
    </>
  );
}
export function CaseDetails() {
  const { id } = useParams();
  const { user } = useAuth();
  const { data, error, loading, refresh } = useApi<CaseDetail>("/cases/" + id);
  const [mode, setMode] = useState<"edit" | "visit" | null>(null);
  const toast = useToast();
  const doctors = useApi<Page<Doctor>>("/doctors?page_size=100");
  if (loading) return <Spinner />;
  if (error) return <ErrorBox message={error} retry={refresh} />;
  if (!data) return null;
  const fields: Field[] =
    mode === "visit"
      ? [
          {
            key: "doctor_id",
            label: "Attending doctor",
            type: "select",
            required: true,
            options: doctors.data?.items
              .filter(
                (d) => user?.role !== "DOCTOR" || d.user_id === user.user_id,
              )
              .map((d) => ({
                value: String(d.doctor_id),
                label: `Dr. ${d.first_name} ${d.last_name}`,
              })),
          },
          {
            key: "visit_type",
            label: "Visit type",
            type: "select",
            required: true,
            options: options(["FOLLOW_UP", "ROUTINE_CHECKUP", "EMERGENCY"]),
          },
          {
            key: "chief_complaint",
            label: "Chief complaint",
            type: "textarea",
            required: true,
          },
          {
            key: "doctor_notes",
            label: "Fictional encounter notes",
            type: "textarea",
          },
        ]
      : [
          {
            key: "chief_complaint",
            label: "Chief complaint",
            type: "textarea",
            required: true,
          },
          {
            key: "present_illness",
            label: "Present illness narrative",
            type: "textarea",
          },
          {
            key: "case_status",
            label: "Case status",
            type: "select",
            required: true,
            options: options(["OPEN", "UNDER_REVIEW", "FOLLOW_UP", "CLOSED"]),
          },
          {
            key: "priority",
            label: "Priority",
            type: "select",
            required: true,
            options: options(["LOW", "MEDIUM", "HIGH", "URGENT"]),
          },
          { key: "notes", label: "Case notes", type: "textarea" },
          ...(user?.role === "ADMIN"
            ? [
                {
                  key: "doctor_id",
                  label: "Assigned doctor",
                  type: "select" as const,
                  options: doctors.data?.items.map((d) => ({
                    value: String(d.doctor_id),
                    label: `Dr. ${d.first_name} ${d.last_name}`,
                  })),
                },
              ]
            : []),
        ];
  return (
    <>
      <Link className="back-link" to="/cases">
        <ArrowLeft size={15} />
        All cases
      </Link>
      <PageHeading
        title={`Case CS-${String(data.case_id).padStart(4, "0")}`}
        subtitle={`${data.patient.first_name} ${data.patient.last_name} · ${dateLabel(data.case_date)} · Dr. ${data.doctor.first_name} ${data.doctor.last_name}`}
        action={
          <div className="heading-actions">
            {data.record_state === "DRAFT" ? (
              <Link className="button primary" to={"/cases/new?draft=" + id}>
                Resume draft
              </Link>
            ) : (
              data.case_status !== "CLOSED" && (
                <>
                  <button
                    className="button secondary"
                    onClick={() => setMode("edit")}
                  >
                    <Pencil size={15} />
                    Edit case
                  </button>
                  <button
                    className="button primary"
                    onClick={() => setMode("visit")}
                  >
                    <Plus size={16} />
                    Subsequent visit
                  </button>
                </>
              )
            )}
          </div>
        }
      />
      <div className="profile-overview">
        <section className="panel">
          <div className="panel-heading">
            <h2>Case overview</h2>
            <div className="heading-actions">
              <Badge value={data.record_state} />
              <Badge value={data.case_status} />
              <Badge value={data.priority} />
            </div>
          </div>
          <div className="panel-content prose-record">
            <h3>Chief complaint</h3>
            <p>{data.chief_complaint || "Draft: not entered"}</p>
            <h3>Present illness</h3>
            <p>{data.present_illness || "Not recorded"}</p>
            <h3>Case notes</h3>
            <p>{data.notes || "Not recorded"}</p>
            <Link className="text-button" to={"/patients/" + data.patient_id}>
              Open complete patient profile →
            </Link>
          </div>
        </section>
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Baseline symptoms</h2>
              <p>Case-level observations</p>
            </div>
          </div>
          {data.symptoms.length ? (
            data.symptoms.map((s) => (
              <div className="symptom-record" key={String(s.symptom_id)}>
                <b>{String(s.symptom_name)}</b>
                <Badge value={s.severity} />
                <small>{String(s.duration || "Duration not recorded")}</small>
              </div>
            ))
          ) : (
            <Empty title="No symptoms recorded" />
          )}
        </section>
      </div>
      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Visits in this case</h2>
            <p>
              Each encounter keeps its own attending doctor and clinical
              documents.
            </p>
          </div>
          <Badge value={`${data.visits.length} visits`} />
        </div>
        {data.visits.map((v) => (
          <VisitCard visit={v} key={v.visit_id} />
        ))}
      </section>
      {mode && (
        <FormModal
          title={mode === "visit" ? "Record a subsequent visit" : "Edit case"}
          fields={fields}
          initial={
            mode === "visit"
              ? {
                  doctor_id:
                    doctors.data?.items.find((d) => d.user_id === user?.user_id)
                      ?.doctor_id || data.doctor_id,
                  visit_type: "FOLLOW_UP",
                }
              : data
          }
          onClose={() => setMode(null)}
          onSubmit={async (v) => {
            if (mode === "visit") {
              const result = await write<{ visit_id: number }>("/visits", {
                case_id: data.case_id,
                ...cleanFields(v, fields),
              });
              setMode(null);
              toast("Subsequent visit recorded");
              window.location.assign("/visits/" + result.visit_id);
            } else {
              await write("/cases/" + id, cleanFields(v, fields), "PUT");
              setMode(null);
              refresh();
              toast("Case updated");
            }
          }}
        />
      )}
    </>
  );
}
export function VisitDetails() {
  const { id } = useParams();
  const { data, error, loading, refresh } = useApi<Visit>("/visits/" + id);
  const [mode, setMode] = useState<
    "diagnosis" | "followup" | "vitals" | "examination" | null
  >(null);
  const toast = useToast();
  if (loading) return <Spinner />;
  if (error) return <ErrorBox message={error} retry={refresh} />;
  if (!data) return null;
  return (
    <>
      <Link className="back-link" to={"/cases/" + data.case_id}>
        <ArrowLeft size={15} />
        Back to case
      </Link>
      <PageHeading
        title={`Encounter VS-${data.visit_id}`}
        subtitle={`${niceVisit(data.visit_type)} · ${dateLabel(data.visit_date)} · Attending doctor #${data.doctor_id}`}
        action={
          <div className="heading-actions">
            <button
              className="button secondary"
              onClick={() => setMode("followup")}
            >
              <CalendarDays size={16} />
              Plan follow-up
            </button>
            <button
              className="button primary"
              onClick={() => setMode("diagnosis")}
            >
              <Plus size={16} />
              Add diagnosis
            </button>
          </div>
        }
      />
      <section className="panel">
        <div className="panel-heading">
          <h2>Encounter narrative</h2>
        </div>
        <div className="panel-content prose-record">
          <h3>Chief complaint</h3>
          <p>{data.chief_complaint}</p>
          <h3>Doctor notes</h3>
          <p>{data.doctor_notes || "Not recorded"}</p>
        </div>
      </section>
      <div className="profile-overview">
        <section className="panel">
          <div className="panel-heading">
            <h2>Vital signs</h2>
            <button className="text-button" onClick={() => setMode("vitals")}>
              Record measurements
            </button>
          </div>
          {data.vitals ? (
            <DetailGrid data={data.vitals} omit={["vital_id", "visit_id"]} />
          ) : (
            <Empty title="No measurements recorded" />
          )}
        </section>
        <section className="panel">
          <div className="panel-heading">
            <h2>Physical examination</h2>
            <button
              className="text-button"
              onClick={() => setMode("examination")}
            >
              Record examination
            </button>
          </div>
          {data.examination ? (
            <DetailGrid
              data={data.examination}
              omit={["examination_id", "visit_id"]}
            />
          ) : (
            <Empty title="No examination recorded" />
          )}
        </section>
      </div>
      <section className="panel">
        <div className="panel-heading">
          <h2>Fictional diagnosis observations</h2>
        </div>
        {data.diagnoses.length ? (
          data.diagnoses.map((d) => (
            <div className="record-block" key={String(d.diagnosis_id)}>
              <h3>
                {String(d.diagnosis_name)} <Badge value={d.diagnosis_type} />
              </h3>
              <p>{String(d.notes || "No notes")}</p>
            </div>
          ))
        ) : (
          <Empty />
        )}
      </section>
      <section className="panel">
        <div className="panel-heading">
          <h2>Prescription document</h2>
          {!data.prescription && (
            <Link
              className="button secondary"
              to={"/prescriptions/new?visit=" + id}
            >
              <Plus size={15} />
              Create prescription
            </Link>
          )}
        </div>
        {data.prescription ? (
          <div className="panel-content">
            <Link
              className="button secondary"
              to={"/prescriptions/" + data.prescription.prescription_id}
            >
              Open RX-{data.prescription.prescription_id} ·{" "}
              {data.prescription.medicines.length} fictional products
            </Link>
          </div>
        ) : (
          <Empty title="No prescription recorded" />
        )}
      </section>
      <section className="panel">
        <div className="panel-heading">
          <h2>Follow-up plans</h2>
        </div>
        {data.followups.length ? (
          data.followups.map((f) => (
            <div className="record-block" key={String(f.follow_up_id)}>
              <h3>
                {dateLabel(f.scheduled_date)} <Badge value={f.status} />
              </h3>
              <DetailGrid
                data={f}
                omit={["follow_up_id", "visit_id", "scheduled_date", "status"]}
              />
            </div>
          ))
        ) : (
          <Empty />
        )}
      </section>
      {mode && (
        <FormModal
          title={
            mode === "diagnosis"
              ? "Add fictional diagnosis"
              : mode === "followup"
                ? "Schedule follow-up plan"
                : mode === "vitals"
                  ? "Record vital signs"
                  : "Record examination"
          }
          fields={
            mode === "diagnosis"
              ? diagnosisFields
              : mode === "followup"
                ? followFields.map((f) => ({
                    ...f,
                    required: f.key !== "instructions",
                  }))
                : mode === "vitals"
                  ? vitalFields
                  : examFields
          }
          initial={
            mode === "diagnosis"
              ? { diagnosis_type: "PRIMARY" }
              : mode === "vitals"
                ? data.vitals || {}
                : mode === "examination"
                  ? data.examination || {}
                  : {}
          }
          onClose={() => setMode(null)}
          onSubmit={async (v) => {
            const fields =
              mode === "diagnosis"
                ? diagnosisFields
                : mode === "followup"
                  ? followFields
                  : mode === "vitals"
                    ? vitalFields
                    : examFields;
            const section = mode === "vitals" || mode === "examination";
            await write(
              section
                ? "/visits/" + id + "/" + mode
                : mode === "diagnosis"
                  ? "/diagnoses"
                  : "/followups",
              {
                ...(!section ? { visit_id: Number(id) } : {}),
                ...cleanFields(v, fields),
              },
              section ? "PUT" : "POST",
            );
            setMode(null);
            refresh();
            toast("Visit record saved");
          }}
        />
      )}
    </>
  );
}
const niceVisit = (v: string) => v.replaceAll("_", " ").toLowerCase();
export function PrescriptionDetails() {
  const { id } = useParams();
  const { data, error, loading } = useApi<Prescription>("/prescriptions/" + id);
  if (loading) return <Spinner />;
  if (error) return <ErrorBox message={error} />;
  if (!data) return null;
  return (
    <>
      <PageHeading
        title={`Fictional prescription RX-${data.prescription_id}`}
        subtitle={`${dateLabel(data.prescription_date)} · Visit VS-${data.visit_id} · Prescriber #${data.doctor_id}`}
        action={
          <button className="button secondary" onClick={() => window.print()}>
            <Printer size={16} />
            Print demo document
          </button>
        }
      />
      <section className="panel prescription-document">
        <div className="prescription-watermark">
          EDUCATIONAL DEMO · FICTIONAL PRODUCTS ONLY
        </div>
        <div className="panel-heading">
          <h2>Prescription products</h2>
          <Badge value="DEMO ONLY" />
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                {[
                  "Fictional product",
                  "Demo amount",
                  "Frequency",
                  "Route",
                  "Days",
                  "Educational notes",
                ].map((h) => (
                  <th key={h}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.medicines.map((m) => (
                <tr key={String(m.medicine_id)}>
                  {[
                    "medicine_name",
                    "dosage",
                    "frequency",
                    "route",
                    "duration_days",
                    "instructions",
                  ].map((k) => (
                    <td key={k}>{String(m[k] || "—")}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="panel-content">
          <p>{data.notes}</p>
          <p className="form-note">
            CareTrack is an educational demonstration project using fictional
            data. It is not intended for real clinical use. This document
            provides no medical advice.
          </p>
          <Link className="text-button" to={"/visits/" + data.visit_id}>
            Back to originating visit →
          </Link>
        </div>
      </section>
    </>
  );
}
export function NewPrescription() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const initialVisit = new URLSearchParams(window.location.search).get("visit");
  const docs = useApi<Page<Doctor>>("/doctors?page_size=100");
  const [value, setValue] = useState<Row>({
      visit_id: initialVisit || "",
      prescription_date: today(),
    }),
    [lines, setLines] = useState<MedicineEntry[]>([]),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const fields: Field[] = [
    {
      key: "visit_id",
      label: "Originating visit ID",
      type: "number",
      required: true,
      min: 1,
    },
    {
      key: "doctor_id",
      label: "Prescribing doctor",
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
      key: "prescription_date",
      label: "Document date",
      type: "date",
      required: true,
    },
    { key: "notes", label: "Educational document notes", type: "textarea" },
  ];
  return (
    <>
      <PageHeading
        title="Create a fictional prescription"
        subtitle="Record a document for an existing authorized visit."
      />
      <section className="panel standalone-form">
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError("");
            try {
              if (!lines.length)
                throw new Error("Add at least one fictional catalog product");
              const r = await write<Prescription>("/prescriptions", {
                ...cleanFields(value, fields),
                medicines: lines,
              });
              navigate("/prescriptions/" + r.prescription_id);
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <div className="panel-content">
            {error && <ErrorBox message={error} />}
            <Fields
              fields={fields}
              value={value}
              onChange={(k, v) => setValue((p) => ({ ...p, [k]: v }))}
            />
            <PrescriptionEditor lines={lines} onChange={setLines} />
          </div>
          <div className="modal-footer">
            <Link to="/prescriptions" className="button secondary">
              Cancel
            </Link>
            <button className="button primary" disabled={busy}>
              {busy ? "Saving…" : "Save fictional prescription"}
            </button>
          </div>
        </form>
      </section>
    </>
  );
}

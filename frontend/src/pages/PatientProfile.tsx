import { useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Plus,
  Phone,
  Mail,
  MapPin,
  Activity,
  FolderHeart,
  Clock3,
  CalendarDays,
  ArrowUpRight,
  Pencil,
} from "lucide-react";
import { useApi } from "../hooks/useApi";
import { useAuth } from "../services/auth";
import { write } from "../services/api";
import {
  Badge,
  Spinner,
  ErrorBox,
  Empty,
  dateLabel,
  initials,
  nice,
  DetailGrid,
  Pagination,
  FormModal,
  useToast,
} from "../components/ui";
import { patientFields, cleanFields } from "./Records";
import type { Patient, History, Page, Row, Visit } from "../types";
export default function PatientProfile() {
  const { id } = useParams();
  const { user } = useAuth();
  const [tab, setTab] = useState("Overview"),
    [page, setPage] = useState(1),
    [timelinePage, setTimelinePage] = useState(1),
    [editing, setEditing] = useState(false);
  const toast = useToast();
  const p = useApi<Patient>("/patients/" + id),
    h = useApi<History>(
      user?.role !== "RECEPTIONIST"
        ? `/patients/${id}/history?page=${page}&page_size=20`
        : null,
    ),
    timeline = useApi<Page>(
      tab === "Timeline"
        ? `/patients/${id}/timeline?page=${timelinePage}&page_size=20`
        : null,
    );
  if (p.loading) return <Spinner />;
  if (p.error) return <ErrorBox message={p.error} retry={p.refresh} />;
  if (!p.data) return null;
  const patient = p.data;
  const clinical = user?.role !== "RECEPTIONIST";
  const cases = h.data?.cases || [],
    visits = cases.flatMap((c) => c.visits),
    prescriptions = visits
      .filter((v) => v.prescription)
      .map((v) => v.prescription!),
    followups = visits.flatMap((v) => v.followups);
  const tabs = clinical
    ? [
        "Overview",
        "Cases",
        "Visits",
        "Medical History",
        "Allergies",
        "Prescriptions",
        "Follow-ups",
        "Timeline",
      ]
    : ["Overview"];
  return (
    <>
      <Link className="back-link" to="/patients">
        <ArrowLeft size={15} />
        All patients
      </Link>
      <section className="patient-header panel">
        <div className="patient-title">
          <span className="avatar huge">
            {initials(patient.first_name, patient.last_name)}
          </span>
          <div>
            <div className="patient-id">
              PT-{String(patient.patient_id).padStart(4, "0")}{" "}
              <Badge value="FICTIONAL RECORD" />
            </div>
            <h1>
              {patient.first_name} {patient.last_name}
            </h1>
            <div className="patient-demographics">
              <span>{patient.age} years</span>
              <i /> <span>{nice(patient.gender)}</span>
              <i />
              <span>{patient.blood_group || "Blood group not recorded"}</span>
            </div>
          </div>
        </div>
        <div className="patient-header-actions">
          <button className="button secondary" onClick={() => setEditing(true)}>
            <Pencil size={15} />
            Edit patient
          </button>
          {clinical && (
            <Link className="button primary" to={"/cases/new?patient=" + id}>
              <Plus size={16} />
              New case
            </Link>
          )}
        </div>
        <div className="patient-contact">
          <span>
            <Phone size={14} />
            {patient.phone}
          </span>
          <span>
            <Mail size={14} />
            {patient.email || "No email recorded"}
          </span>
          <span>
            <MapPin size={14} />
            {patient.city || "No city recorded"}
          </span>
        </div>
      </section>
      <div className="profile-tabs">
        {tabs.map((t) => (
          <button
            key={t}
            className={tab === t ? "active" : ""}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </div>
      {h.error && <ErrorBox message={h.error} retry={h.refresh} />}
      {clinical && h.loading ? (
        <Spinner />
      ) : tab === "Overview" ? (
        <div className="profile-overview">
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>Patient information</h2>
                <p>The current demographic record</p>
              </div>
            </div>
            <DetailGrid
              data={patient}
              omit={[
                "first_name",
                "last_name",
                "patient_id",
                "age",
                "updated_at",
                "created_at",
              ]}
            />
          </section>
          <div>
            <section className="panel">
              <div className="panel-heading">
                <h2>Record at a glance</h2>
              </div>
              {clinical && h.data ? (
                <div className="profile-counts">
                  <span>
                    <FolderHeart size={18} />
                    <b>{h.data.case_total}</b>Cases
                  </span>
                  <span>
                    <Activity size={18} />
                    <b>{h.data.visit_count}</b>Visits
                  </span>
                  <span>
                    <Clock3 size={18} />
                    <b>
                      {followups.filter((f) => f.status === "PENDING").length}
                    </b>
                    Pending plans on this page
                  </span>
                </div>
              ) : (
                <div className="optional-note">
                  Reception access includes demographics and scheduling.
                  Clinical records require an authorized doctor or admin.
                </div>
              )}
            </section>
            {clinical && h.data?.lifestyle && (
              <section className="panel">
                <div className="panel-heading">
                  <div>
                    <h2>Lifestyle snapshot</h2>
                    <p>Current recorded values</p>
                  </div>
                </div>
                <DetailGrid
                  data={h.data.lifestyle}
                  omit={["lifestyle_id", "patient_id", "updated_at"]}
                />
              </section>
            )}
            <section className="panel">
              <div className="panel-heading">
                <h2>Scheduling</h2>
              </div>
              <div className="panel-content">
                <Link className="button secondary" to="/appointments">
                  <CalendarDays size={16} />
                  Manage appointments
                </Link>
              </div>
            </section>
          </div>
        </div>
      ) : tab === "Cases" ? (
        <section className="panel">
          <div className="panel-heading">
            <h2>Patient cases</h2>
          </div>
          {cases.length ? (
            <div className="compact-list">
              {cases.map((c) => (
                <Link key={c.case_id} to={"/cases/" + c.case_id}>
                  <span className="list-icon">
                    <FolderHeart size={19} />
                  </span>
                  <div>
                    <b>{c.chief_complaint || "Incomplete draft"}</b>
                    <small>
                      CS-{c.case_id} · {dateLabel(c.case_date)} · Dr.{" "}
                      {c.doctor.first_name} {c.doctor.last_name}
                    </small>
                  </div>
                  <Badge
                    value={c.record_state === "DRAFT" ? "DRAFT" : c.case_status}
                  />
                  <ArrowUpRight size={16} />
                </Link>
              ))}
            </div>
          ) : (
            <Empty />
          )}
        </section>
      ) : tab === "Visits" ? (
        <section className="panel">
          <div className="panel-heading">
            <h2>Encounter history</h2>
          </div>
          {visits.length ? (
            visits.map((v) => <VisitCard visit={v} key={v.visit_id} />)
          ) : (
            <Empty />
          )}
        </section>
      ) : tab === "Medical History" ? (
        <section className="panel">
          <div className="panel-heading">
            <h2>Medical history episodes</h2>
          </div>
          {h.data?.medical_history.length ? (
            h.data.medical_history.map((r) => (
              <div className="record-block" key={String(r.history_id)}>
                <h3>{String(r.condition_name)}</h3>
                <DetailGrid
                  data={r}
                  omit={["history_id", "patient_id", "condition_name"]}
                />
              </div>
            ))
          ) : (
            <Empty title="No history recorded" />
          )}
        </section>
      ) : tab === "Allergies" ? (
        <section className="panel">
          <div className="panel-heading">
            <h2>Allergy records</h2>
          </div>
          {h.data?.allergies.length ? (
            h.data.allergies.map((r) => (
              <div className="record-block" key={String(r.allergy_id)}>
                <h3>
                  {String(r.allergen)} <Badge value={r.severity} />
                </h3>
                <DetailGrid
                  data={r}
                  omit={["allergy_id", "patient_id", "allergen", "severity"]}
                />
              </div>
            ))
          ) : (
            <Empty
              title="No allergies recorded"
              description="An empty record means not recorded, not confirmed absence."
            />
          )}
        </section>
      ) : tab === "Prescriptions" ? (
        <section className="panel">
          <div className="panel-heading">
            <h2>Fictional prescription documents</h2>
          </div>
          {prescriptions.length ? (
            <div className="compact-list">
              {prescriptions.map((r) => (
                <Link
                  key={r.prescription_id}
                  to={"/prescriptions/" + r.prescription_id}
                >
                  <div>
                    <b>RX-{r.prescription_id}</b>
                    <small>
                      {dateLabel(r.prescription_date)} · {r.medicines.length}{" "}
                      fictional products
                    </small>
                  </div>
                  <ArrowUpRight size={16} />
                </Link>
              ))}
            </div>
          ) : (
            <Empty />
          )}
        </section>
      ) : tab === "Follow-ups" ? (
        <section className="panel">
          <div className="panel-heading">
            <h2>Follow-up plans</h2>
          </div>
          {followups.length ? (
            followups.map((f) => (
              <div className="record-block" key={String(f.follow_up_id)}>
                <h3>
                  {dateLabel(f.scheduled_date)} <Badge value={f.status} />
                </h3>
                <DetailGrid
                  data={f}
                  omit={[
                    "follow_up_id",
                    "visit_id",
                    "status",
                    "scheduled_date",
                  ]}
                />
              </div>
            ))
          ) : (
            <Empty />
          )}
        </section>
      ) : (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>A connected patient timeline</h2>
              <p>Date-only events do not imply an exact time.</p>
            </div>
          </div>
          {timeline.loading ? (
            <Spinner />
          ) : timeline.error ? (
            <ErrorBox message={timeline.error} />
          ) : timeline.data?.items.length ? (
            <>
              <div className="timeline">
                {timeline.data.items.map((e, i) => (
                  <div
                    className="timeline-event"
                    key={String(e.event_type) + String(e.entity_id) + i}
                  >
                    <span className="timeline-dot" />
                    <time>{dateLabel(e.event_date)}</time>
                    <h3>{String(e.event_type)}</h3>
                    <p>{String(e.description)}</p>
                    <small>Record #{String(e.entity_id)}</small>
                  </div>
                ))}
              </div>
              <Pagination
                page={timelinePage}
                total={timeline.data.total}
                size={20}
                onChange={setTimelinePage}
              />
            </>
          ) : (
            <Empty />
          )}
        </section>
      )}
      {clinical && h.data && tab !== "Timeline" && (
        <section className="profile-pagination">
          <Pagination
            page={page}
            total={Math.max(
              h.data.case_total,
              h.data.medical_history_total,
              h.data.allergies_total,
            )}
            size={20}
            onChange={setPage}
          />
          <p>
            Clinical tabs show records from this page of cases. History and
            allergy records use the same page size of 20.
          </p>
        </section>
      )}
      {editing && (
        <FormModal
          title="Edit fictional patient"
          fields={patientFields}
          initial={patient}
          onClose={() => setEditing(false)}
          onSubmit={async (v) => {
            await write(
              "/patients/" + id,
              cleanFields(v, patientFields),
              "PUT",
            );
            setEditing(false);
            p.refresh();
            toast("Patient details updated");
          }}
        />
      )}
    </>
  );
}
export function VisitCard({ visit }: { visit: Visit }) {
  return (
    <Link className="visit-card" to={"/visits/" + visit.visit_id}>
      <span className="list-icon">
        <StethoscopeIcon />
      </span>
      <div>
        <small>
          {dateLabel(visit.visit_date)} · VS-{visit.visit_id}
        </small>
        <h3>{nice(visit.visit_type)}</h3>
        <p>{visit.chief_complaint}</p>
      </div>
      <ArrowUpRight size={17} />
    </Link>
  );
}
function StethoscopeIcon() {
  return <Activity size={18} />;
}

import { useState } from "react";
import { Download, RefreshCw, ArrowRight, BarChart3 } from "lucide-react";
import { useApi } from "../hooks/useApi";
import { useAuth } from "../services/auth";
import { write, query } from "../services/api";
import { PageHeading } from "../layouts/Workspace";
import {
  Spinner,
  ErrorBox,
  Empty,
  Pagination,
  dateLabel,
  useToast,
  nice,
} from "../components/ui";
import { Chart } from "./Dashboard";
import type { Page, ChartPoint, Doctor, Row } from "../types";
const REPORTS = [
  ["patients", "Patient registrations", "Patients registered per month"],
  ["cases", "Cases per doctor", "Assigned case workload"],
  ["symptoms", "Common symptoms", "Case-level symptom associations"],
  ["diagnoses", "Diagnosis observations", "Fictional diagnosis frequencies"],
  ["medicines", "Prescribed products", "Fictional product line frequencies"],
  ["appointments", "Appointment statistics", "Bookings by current status"],
  ["followups", "Follow-up statistics", "Plans by current status"],
  ["active-cases", "Active cases", "Open, review and follow-up cases"],
  ["closed-cases", "Closed cases", "Closed cases grouped by case month"],
  [
    "multiple-cases",
    "Patients with multiple cases",
    "Patients with more than one case",
  ],
];
export default function Reports() {
  const { user } = useAuth();
  const [report, setReport] = useState("patients"),
    [from, setFrom] = useState(""),
    [to, setTo] = useState(""),
    [doctor, setDoctor] = useState(""),
    [page, setPage] = useState(1),
    [q, setQ] = useState(""),
    [sort, setSort] = useState("total"),
    [direction, setDirection] = useState("desc");
  const toast = useToast();
  const docs = useApi<Page<Doctor>>("/doctors?page_size=100");
  const response = useApi<Page<ChartPoint>>(
    "/reports/" +
      report +
      "?" +
      query({
        date_from: from,
        date_to: to,
        doctor_id: doctor,
        page,
        page_size: 15,
        q,
        sort,
        direction,
      }),
  );
  const cache = useApi<{ items: Row[]; notice: string }>(
    user?.role === "ADMIN" ? "/reports/monthly-cache" : null,
  );
  const allowed = REPORTS.filter(
    ([name]) =>
      user?.role !== "RECEPTIONIST" ||
      ["patients", "appointments", "followups"].includes(name),
  );
  const selected = REPORTS.find((r) => r[0] === report)!;
  function reset(fn: () => void) {
    fn();
    setPage(1);
  }
  function download() {
    const quote = (v: unknown) =>
      '"' +
      String(v ?? "")
        .replaceAll('"', '""')
        .replace(/^[=+@-]/, "\t$&") +
      '"';
    const csv =
      "Report,Label,Count\r\n" +
      (response.data?.items || [])
        .map((r) => [report, r.label, r.total].map(quote).join(","))
        .join("\r\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = `caretrack-${report}-page-${page}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }
  return (
    <>
      <PageHeading
        title="A clearer view of your records."
        subtitle="Explore patterns in your fictional data. Every number comes from MySQL."
        action={
          <button
            className="button secondary"
            onClick={download}
            disabled={!response.data?.items.length}
          >
            <Download size={16} />
            Export current page
          </button>
        }
      />
      <div className="reports-layout">
        <aside className="report-menu">
          {allowed.map(([name, title, desc]) => (
            <button
              className={report === name ? "active" : ""}
              key={name}
              onClick={() => reset(() => setReport(name))}
            >
              <BarChart3 size={17} />
              <span>
                <b>{title}</b>
                <small>{desc}</small>
              </span>
              <ArrowRight size={14} />
            </button>
          ))}
        </aside>
        <div>
          <section className="panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">DATABASE INSIGHTS</span>
                <h2>{selected[1]}</h2>
                <p>{selected[2]}</p>
              </div>
              <button
                className="icon-button"
                aria-label="Refresh report"
                onClick={response.refresh}
              >
                <RefreshCw size={16} />
              </button>
            </div>
            <div className="report-filters">
              <label>
                From
                <input
                  type="date"
                  value={from}
                  onChange={(e) => reset(() => setFrom(e.target.value))}
                />
              </label>
              <label>
                Through
                <input
                  type="date"
                  value={to}
                  onChange={(e) => reset(() => setTo(e.target.value))}
                />
              </label>
              <label>
                Doctor
                <select
                  value={doctor}
                  onChange={(e) => reset(() => setDoctor(e.target.value))}
                >
                  <option value="">All authorized doctors</option>
                  {docs.data?.items
                    .filter(
                      (d) =>
                        user?.role !== "DOCTOR" || d.user_id === user.user_id,
                    )
                    .map((d) => (
                      <option value={d.doctor_id} key={d.doctor_id}>
                        Dr. {d.first_name} {d.last_name}
                      </option>
                    ))}
                </select>
              </label>
            </div>
            {response.loading ? (
              <Spinner />
            ) : response.error ? (
              <ErrorBox message={response.error} retry={response.refresh} />
            ) : response.data?.items.length ? (
              <div className="report-chart">
                <Chart data={response.data.items} type="bar" height={280} />
              </div>
            ) : (
              <Empty />
            )}
            <div className="table-toolbar">
              <input
                placeholder="Filter report labels…"
                aria-label="Filter report labels"
                value={q}
                onChange={(e) => reset(() => setQ(e.target.value))}
              />
              <div className="table-filters">
                <select
                  aria-label="Sort report"
                  value={sort}
                  onChange={(e) => reset(() => setSort(e.target.value))}
                >
                  <option value="total">Count</option>
                  <option value="label">Label</option>
                </select>
                <select
                  aria-label="Report sort direction"
                  value={direction}
                  onChange={(e) => reset(() => setDirection(e.target.value))}
                >
                  <option value="desc">Descending</option>
                  <option value="asc">Ascending</option>
                </select>
              </div>
            </div>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>{selected[1]}</th>
                    <th className="right">Record count</th>
                  </tr>
                </thead>
                <tbody>
                  {response.data?.items.map((r) => (
                    <tr key={r.label}>
                      <td>{nice(r.label)}</td>
                      <td className="right">
                        <b>{r.total.toLocaleString()}</b>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {response.data && (
              <Pagination
                page={page}
                total={response.data.total}
                size={15}
                onChange={setPage}
              />
            )}
          </section>
          {user?.role === "ADMIN" && (
            <section className="panel cache-panel">
              <div className="panel-heading">
                <div>
                  <h2>Precomputed monthly summary</h2>
                  <p>MySQL materialized-view equivalent</p>
                </div>
                <button
                  className="button secondary"
                  onClick={async () => {
                    try {
                      await write("/reports/monthly-cache/refresh", {});
                      cache.refresh();
                      toast("Monthly reporting cache refreshed");
                    } catch (e) {
                      toast((e as Error).message);
                    }
                  }}
                >
                  <RefreshCw size={15} />
                  Refresh summary
                </button>
              </div>
              <div className="panel-content">
                <p>{cache.data?.notice}</p>
                <small>
                  Last refresh:{" "}
                  {cache.data?.items[0]?.refreshed_at
                    ? new Date(
                        String(cache.data.items[0].refreshed_at) + "Z",
                      ).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })
                    : "Not refreshed yet"}{" "}
                  IST
                </small>
              </div>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Case month</th>
                      <th>Cases</th>
                      <th>Unique patients</th>
                      <th>Currently closed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cache.data?.items.map((r) => (
                      <tr key={String(r.stat_month)}>
                        <td>{dateLabel(r.stat_month)}</td>
                        <td>{String(r.total_cases)}</td>
                        <td>{String(r.unique_patients)}</td>
                        <td>{String(r.completed_cases)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </div>
      </div>
    </>
  );
}

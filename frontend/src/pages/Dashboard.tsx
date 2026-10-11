import { Link } from "react-router-dom";
import {
  Users,
  FolderHeart,
  CalendarDays,
  Clock3,
  Stethoscope,
  ClipboardList,
  ArrowUpRight,
  ArrowRight,
  Plus,
  ChevronRight,
  Activity,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { useApi } from "../hooks/useApi";
import { useAuth } from "../services/auth";
import {
  Badge,
  Spinner,
  ErrorBox,
  dateLabel,
  nice,
  initials,
  Empty,
} from "../components/ui";
import type { DashboardData, ChartPoint } from "../types";
const COLORS = [
  "#137c73",
  "#73b9a5",
  "#a2d4c2",
  "#e7b66c",
  "#8b9ab0",
  "#d9e7e3",
];
export function Chart({
  data,
  type = "area",
  height = 230,
}: {
  data: ChartPoint[];
  type?: "area" | "bar" | "pie";
  height?: number;
}) {
  if (!data.length)
    return (
      <Empty
        title="No data for this view"
        description="New records will appear here."
      />
    );
  return (
    <div style={{ height, width: "100%" }}>
      <ResponsiveContainer width="100%" height="100%">
        {type === "pie" ? (
          <PieChart>
            <Pie
              isAnimationActive={false}
              data={data}
              dataKey="total"
              nameKey="label"
              innerRadius={55}
              outerRadius={82}
              paddingAngle={4}
            >
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        ) : type === "bar" ? (
          <BarChart
            data={data}
            margin={{ top: 10, right: 10, bottom: 5, left: -25 }}
          >
            <CartesianGrid vertical={false} stroke="#edf1f0" />
            <XAxis
              dataKey="label"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: "#82928c" }}
              interval={0}
              tickFormatter={(v) =>
                String(v).length > 13 ? String(v).slice(0, 11) + "…" : nice(v)
              }
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              allowDecimals={false}
              tick={{ fontSize: 11, fill: "#82928c" }}
            />
            <Tooltip cursor={{ fill: "#f4f8f6" }} />
            <Bar
              isAnimationActive={false}
              dataKey="total"
              name="Records"
              fill="#70ad9e"
              radius={[5, 5, 0, 0]}
              maxBarSize={32}
            />
          </BarChart>
        ) : (
          <AreaChart
            data={data}
            margin={{ top: 12, right: 10, bottom: 0, left: -25 }}
          >
            <defs>
              <linearGradient id="chartFill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="#137c73" stopOpacity={0.15} />
                <stop offset="100%" stopColor="#137c73" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} stroke="#edf1f0" />
            <XAxis
              dataKey="label"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: "#82928c" }}
              tickFormatter={(v) =>
                new Date(String(v) + "-15").toLocaleDateString("en-IN", {
                  month: "short",
                })
              }
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              allowDecimals={false}
              tick={{ fontSize: 11, fill: "#82928c" }}
            />
            <Tooltip />
            <Area
              isAnimationActive={false}
              type="monotone"
              dataKey="total"
              name="Records"
              stroke="#137c73"
              strokeWidth={2.5}
              fill="url(#chartFill)"
            />
          </AreaChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
export default function Dashboard() {
  const { user } = useAuth();
  const { data, error, loading, refresh } = useApi<DashboardData>(
    "/dashboard/statistics",
  );
  if (loading) return <Spinner />;
  if (error) return <ErrorBox message={error} retry={refresh} />;
  if (!data) return null;
  const cards = [
    {
      key: "total_patients",
      title: "Total patients",
      icon: Users,
      label: "Registered in your workspace",
      path: "/patients",
    },
    {
      key: "active_cases",
      title: "Active cases",
      icon: FolderHeart,
      label: "Open, review & follow-up",
      path: "/cases",
    },
    {
      key: "todays_appointments",
      title: "Today’s appointments",
      icon: CalendarDays,
      label: dateLabel(data.clinic_date),
      path: "/appointments",
    },
    {
      key: "upcoming_followups",
      title: "Upcoming follow-ups",
      icon: Clock3,
      label: "Pending from today onward",
      path: "/followups",
    },
    {
      key: "total_doctors",
      title: "Active doctors",
      icon: Stethoscope,
      label: "Your educational care team",
      path: "/doctors",
    },
    {
      key: "prescriptions_this_month",
      title: "Prescriptions this month",
      icon: ClipboardList,
      label: "Fictional documents only",
      path: "/prescriptions",
    },
  ].filter((c) => c.key in data.statistics);
  const clinical = user?.role !== "RECEPTIONIST";
  return (
    <>
      <div className="dashboard-heading">
        <div>
          <div className="greeting">
            <span /> YOUR WORKSPACE, AT A GLANCE
          </div>
          <h1>
            A little clarity for your day<span>.</span>
          </h1>
          <p>
            Welcome back, {nice(user?.username)}. Here’s what’s happening in
            your learning clinic.
          </p>
        </div>
        <div className="heading-actions">
          <span className="date-chip">
            <CalendarDays size={15} />
            {dateLabel(data.clinic_date)}
          </span>
          <Link
            className="button primary"
            to={clinical ? "/cases/new" : "/patients/new"}
          >
            <Plus size={17} />
            {clinical ? "New case" : "Register patient"}
          </Link>
        </div>
      </div>
      <div className="demo-banner">
        <ShieldIcon />
        <p>
          <b>A workspace built for learning.</b> All records are fictional. This
          educational demo provides no medical advice.
        </p>
        <span>DBMS PROJECT</span>
      </div>
      <div className="stats-grid">
        {cards.map((c, i) => (
          <Link to={c.path} className="stat-card" key={c.key}>
            <div className="stat-top">
              <span className={`stat-icon tone-${i % 4}`}>
                <c.icon size={18} />
              </span>
              <ArrowUpRight size={16} />
            </div>
            <span className="stat-label">{c.title}</span>
            <strong>{data.statistics[c.key].toLocaleString()}</strong>
            <small>{c.label}</small>
          </Link>
        ))}
      </div>
      <div className="dashboard-main-grid">
        <section className="panel chart-main">
          <div className="panel-heading">
            <div>
              <h2>Patient registrations</h2>
              <p>A month-by-month view of your workspace</p>
            </div>
            <span className="muted-tag">All recorded months</span>
          </div>
          <Chart data={data.charts.patients_per_month} />
        </section>
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Appointment overview</h2>
              <p>Your bookings by status</p>
            </div>
            <CalendarDays size={18} />
          </div>
          <div className="donut-wrap">
            <Chart
              data={data.charts.appointment_status}
              type="pie"
              height={190}
            />
            <div className="donut-center">
              <b>
                {data.charts.appointment_status.reduce(
                  (n, v) => n + v.total,
                  0,
                )}
              </b>
              <span>appointments</span>
            </div>
          </div>
          <div className="legend">
            {data.charts.appointment_status.map((v, i) => (
              <div key={v.label}>
                <span>
                  <i style={{ background: COLORS[i % COLORS.length] }} />
                  {nice(v.label)}
                </span>
                <b>{v.total}</b>
              </div>
            ))}
          </div>
        </section>
      </div>
      <div className="dashboard-main-grid">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Today’s schedule</h2>
              <p>Your next fictional patient encounters</p>
            </div>
            <Link className="text-button" to="/appointments">
              View schedule <ArrowRight size={14} />
            </Link>
          </div>
          {data.recent.appointments.length ? (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Patient</th>
                    <th>Time</th>
                    <th>Doctor</th>
                    <th>Status</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {data.recent.appointments.map((a) => (
                    <tr key={String(a.appointment_id)}>
                      <td>
                        <Link
                          className="patient-cell"
                          to={"/patients/" + a.patient_id}
                        >
                          <span className="avatar small">
                            {String(a.patient_name)
                              .split(" ")
                              .map((w) => w[0])
                              .join("")
                              .slice(0, 2)}
                          </span>
                          <b>{String(a.patient_name)}</b>
                        </Link>
                      </td>
                      <td>
                        {String(a.start_time).slice(0, 5)} <small>IST</small>
                      </td>
                      <td>Dr. {String(a.doctor_name)}</td>
                      <td>
                        <Badge value={a.status} />
                      </td>
                      <td>
                        <Link
                          className="icon-button"
                          to={
                            clinical
                              ? `/cases/new?patient=${a.patient_id}`
                              : `/patients/${a.patient_id}`
                          }
                          aria-label="Open patient"
                        >
                          <ChevronRight size={17} />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty
              title="A clear schedule"
              description="No appointments are booked for today."
            />
          )}
          <div className="panel-bottom">
            <span>
              <i className="tiny-dot" />
              Live from your MySQL database
            </span>
            <Link to="/appointments" className="text-button">
              Manage appointments
            </Link>
          </div>
        </section>
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Recently registered</h2>
              <p>New faces in your learning clinic</p>
            </div>
            <Link to="/patients" className="text-button">
              View all
            </Link>
          </div>
          <div className="recent-patients">
            {data.recent.patients.map((p) => (
              <Link to={"/patients/" + p.patient_id} key={p.patient_id}>
                <span className="avatar">
                  {initials(p.first_name, p.last_name)}
                </span>
                <div>
                  <b>
                    {p.first_name} {p.last_name}
                  </b>
                  <small>
                    PT-{String(p.patient_id).padStart(4, "0")} ·{" "}
                    {p.city || "City not recorded"}
                  </small>
                </div>
                <ChevronRight size={16} />
              </Link>
            ))}
          </div>
        </section>
      </div>
      {clinical && (
        <>
          <div className="section-label">
            <h2>A closer look</h2>
            <Link className="text-button" to="/reports">
              Explore reports <ArrowRight size={14} />
            </Link>
          </div>
          <div className="charts-three">
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Cases over time</h2>
                  <p>Submitted cases by month</p>
                </div>
              </div>
              <Chart data={data.charts.cases_per_month} height={200} />
            </section>
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Common symptoms</h2>
                  <p>Recorded case-level observations</p>
                </div>
              </div>
              <Chart data={data.charts.top_symptoms} type="bar" height={200} />
            </section>
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Case status</h2>
                  <p>Current submitted case workflow</p>
                </div>
              </div>
              <Chart data={data.charts.case_status} type="bar" height={200} />
            </section>
          </div>
          <div className="dashboard-main-grid">
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Recent cases</h2>
                  <p>Latest submitted cases</p>
                </div>
                <Link to="/cases" className="text-button">
                  View all
                </Link>
              </div>
              <div className="compact-list">
                {data.recent.cases?.map((c) => (
                  <Link to={"/cases/" + c.case_id} key={String(c.case_id)}>
                    <span className="list-icon">
                      <FolderHeart size={17} />
                    </span>
                    <div>
                      <b>{String(c.patient_name)}</b>
                      <small>{String(c.chief_complaint)}</small>
                    </div>
                    <Badge value={c.case_status} />
                  </Link>
                ))}
              </div>
            </section>
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Diagnosis observations</h2>
                  <p>Fictional labels, for learning only</p>
                </div>
              </div>
              <Chart data={data.charts.top_diagnoses} type="bar" height={235} />
            </section>
          </div>
        </>
      )}
      <section className="panel upcoming-panel">
        <div className="panel-heading">
          <div>
            <h2>Upcoming follow-ups</h2>
            <p>Plans that still need a scheduled check-in</p>
          </div>
          <Link to="/followups" className="text-button">
            View follow-ups <ArrowRight size={14} />
          </Link>
        </div>
        <div className="upcoming-cards">
          {data.recent.followups.length ? (
            data.recent.followups.map((f) => (
              <Link
                to={"/patients/" + f.patient_id}
                key={String(f.follow_up_id)}
              >
                <span className="calendar-tile">
                  <b>
                    {new Date(String(f.follow_up_date) + "T12:00:00").getDate()}
                  </b>
                  <small>
                    {new Date(
                      String(f.follow_up_date) + "T12:00:00",
                    ).toLocaleDateString("en-IN", { month: "short" })}
                  </small>
                </span>
                <div>
                  <b>{String(f.patient_name)}</b>
                  <small>Dr. {String(f.doctor_name)}</small>
                  <Badge value={f.status} />
                </div>
              </Link>
            ))
          ) : (
            <Empty title="No upcoming follow-ups" />
          )}
        </div>
      </section>
    </>
  );
}
function ShieldIcon() {
  return (
    <span className="banner-icon">
      <Activity size={18} />
    </span>
  );
}

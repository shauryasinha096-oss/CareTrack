import { NavLink, Outlet, useNavigate, useLocation } from "react-router-dom";
import {
  Activity,
  LayoutDashboard,
  Users,
  FolderHeart,
  CalendarDays,
  Stethoscope,
  Pill,
  ClipboardList,
  Clock3,
  ChartNoAxesCombined,
  ShieldCheck,
  Settings,
  LogOut,
  Search,
  Plus,
  ChevronRight,
  Menu,
  BookOpen,
} from "lucide-react";
import { useState, type FormEvent } from "react";
import { useAuth } from "../services/auth";
import { initials, nice, dateLabel, today } from "../components/ui";
const navigation = [
  {
    title: "Dashboard",
    path: "/",
    icon: LayoutDashboard,
    section: "WORKSPACE",
  },
  { title: "Patients", path: "/patients", icon: Users },
  { title: "Cases", path: "/cases", icon: FolderHeart, clinical: true },
  { title: "Visits", path: "/visits", icon: Stethoscope, clinical: true },
  { title: "Appointments", path: "/appointments", icon: CalendarDays },
  { title: "Follow-ups", path: "/followups", icon: Clock3 },
  {
    title: "Prescriptions",
    path: "/prescriptions",
    icon: ClipboardList,
    section: "CLINICAL LIBRARY",
    clinical: true,
  },
  { title: "Diagnoses", path: "/diagnoses", icon: FolderHeart, clinical: true },
  { title: "Medicines", path: "/medicines", icon: Pill, clinical: true },
  { title: "Symptoms", path: "/symptoms", icon: Activity, clinical: true },
  {
    title: "Doctors",
    path: "/doctors",
    icon: Stethoscope,
    section: "MANAGEMENT",
  },
  { title: "Reports", path: "/reports", icon: ChartNoAxesCombined },
  { title: "Audit logs", path: "/audit-logs", icon: ShieldCheck, admin: true },
  { title: "Settings", path: "/settings", icon: Settings },
];
export default function Workspace() {
  const { user, logout } = useAuth();
  const navigate = useNavigate(),
    location = useLocation();
  const [search, setSearch] = useState(""),
    [mobile, setMobile] = useState(false);
  const current =
    navigation.find(
      (n) => n.path !== "/" && location.pathname.startsWith(n.path),
    )?.title || "Dashboard";
  function submit(e: FormEvent) {
    e.preventDefault();
    navigate("/patients?q=" + encodeURIComponent(search));
    setSearch("");
  }
  return (
    <div className="workspace">
      <aside className={`sidebar ${mobile ? "open" : ""}`}>
        <NavLink to="/" className="logo">
          <span className="logo-mark">
            <Activity size={24} />
          </span>
          <span>
            CareTrack<span className="logo-dot">.</span>
            <small>CLINICAL RECORDS, SIMPLIFIED</small>
          </span>
        </NavLink>
        <div className="workspace-switch">
          <span className="clinic-avatar">C</span>
          <div>
            <b>Learning clinic</b>
            <small>College DBMS workspace</small>
          </div>
          <ChevronRight size={15} />
        </div>
        <nav>
          {navigation
            .filter(
              (n) =>
                (!n.admin || user?.role === "ADMIN") &&
                (!n.clinical || user?.role !== "RECEPTIONIST"),
            )
            .map((n) => (
              <div key={n.path}>
                {n.section && <p className="nav-section">{n.section}</p>}
                <NavLink
                  to={n.path}
                  end={n.path === "/"}
                  onClick={() => setMobile(false)}
                  className={({ isActive }) =>
                    `nav-link ${isActive ? "active" : ""}`
                  }
                >
                  <n.icon size={18} />
                  <span>{n.title}</span>
                  {n.path === "/patients" && <span className="nav-dot" />}
                </NavLink>
              </div>
            ))}
        </nav>
        <div className="sidebar-footer">
          <div className="educational-mini">
            <BookOpen size={17} />
            <div>
              <b>Built for learning</b>
              <small>Fictional data · Educational demo</small>
            </div>
          </div>
          <button className="account" onClick={logout} title="Sign out">
            <span className="avatar">{initials(user?.username)}</span>
            <span>
              <b>{nice(user?.username)}</b>
              <small>{nice(user?.role)}</small>
            </span>
            <LogOut size={16} />
          </button>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <button
            className="icon-button mobile-menu"
            aria-label="Toggle navigation"
            onClick={() => setMobile((v) => !v)}
          >
            <Menu size={20} />
          </button>
          <div className="breadcrumb">
            Workspace <ChevronRight size={13} />
            <b>{current}</b>
          </div>
          <form className="global-search" onSubmit={submit}>
            <Search size={16} />
            <input
              aria-label="Search patients globally"
              placeholder="Search patients by name, ID, phone…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </form>
          <span className="environment">
            <i /> Fictional data only
          </span>
          <span className="top-avatar">{initials(user?.username)}</span>
        </header>
        <main>
          <Outlet />
        </main>
        <footer className="disclaimer">
          <ShieldCheck size={14} />
          <span>
            CareTrack is an educational demonstration project using fictional
            data. It is not intended for real clinical use.
          </span>
        </footer>
      </div>
    </div>
  );
}
export function PageHeading({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">CARETRACK WORKSPACE</div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      {action}
    </div>
  );
}

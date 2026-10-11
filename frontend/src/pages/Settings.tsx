import { Link } from "react-router-dom";
import { ShieldCheck, Database, Code2, Users, ArrowRight } from "lucide-react";
import { useAuth } from "../services/auth";
import { useApi } from "../hooks/useApi";
import { PageHeading } from "../layouts/Workspace";
import { Badge, DetailGrid, ErrorBox } from "../components/ui";
import type { Row } from "../types";
export default function Settings() {
  const { user } = useAuth();
  const health = useApi<Row>("/health");
  return (
    <>
      <PageHeading
        title="Workspace settings"
        subtitle="Your account, access, and educational environment."
      />
      <div className="profile-overview">
        <section className="panel">
          <div className="panel-heading">
            <h2>Your account</h2>
            <ShieldCheck size={18} />
          </div>
          <DetailGrid data={user as unknown as Row} omit={["is_active"]} />
          <div className="panel-content">
            <Badge value={user?.is_active ? "ACTIVE" : "INACTIVE"} />
          </div>
        </section>
        <section className="panel">
          <div className="panel-heading">
            <h2>System connection</h2>
            <Database size={18} />
          </div>
          <div className="panel-content">
            {health.error ? (
              <ErrorBox message={health.error} />
            ) : (
              <>
                <Badge
                  value={
                    health.data?.status === "ok" ? "CONNECTED" : "CHECKING"
                  }
                />
                <p className="settings-copy">
                  React → FastAPI → SQLAlchemy → MySQL
                </p>
                <p>
                  Records are persisted in MySQL. This workspace uses fictional
                  data exclusively.
                </p>
              </>
            )}
          </div>
        </section>
      </div>
      <section className="panel">
        <div className="panel-heading">
          <h2>Project tools</h2>
        </div>
        <div className="settings-tools">
          <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">
            <Code2 size={22} />
            <span>
              <b>Interactive API documentation</b>
              <small>Inspect and try the FastAPI endpoints.</small>
            </span>
            <ArrowRight size={17} />
          </a>
          {user?.role === "ADMIN" && (
            <Link to="/users">
              <Users size={22} />
              <span>
                <b>Manage user accounts</b>
                <small>
                  Create reception/admin accounts; provision doctors in the
                  doctor directory.
                </small>
              </span>
              <ArrowRight size={17} />
            </Link>
          )}
        </div>
      </section>
      <div className="form-note">
        <ShieldCheck size={18} />
        CareTrack is an educational demonstration project using fictional data.
        It is not intended for real clinical use.
      </div>
    </>
  );
}

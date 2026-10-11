import {
  Activity,
  ArrowRight,
  ShieldCheck,
  FolderHeart,
  CalendarDays,
  ChartNoAxesCombined,
  LoaderCircle,
} from "lucide-react";
import { useState, type FormEvent } from "react";
import { useAuth } from "../services/auth";
import { ErrorBox } from "../components/ui";
export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(email, password);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="login-page">
      <section className="login-story">
        <div className="logo">
          <span className="logo-mark">
            <Activity size={28} />
          </span>
          <span>
            CareTrack<span className="logo-dot">.</span>
          </span>
        </div>
        <div className="story-copy">
          <span className="story-tag">
            A BETTER WAY TO LEARN CLINICAL RECORDS
          </span>
          <h1>
            A clear picture.
            <br />
            Every case.
            <br />
            <em>Every step.</em>
          </h1>
          <p>
            One thoughtful workspace for patient cases, visit histories, and the
            details that connect them.
          </p>
          <div className="story-features">
            {[
              [FolderHeart, "Structured case-taking"],
              [CalendarDays, "Connected scheduling"],
              [ChartNoAxesCombined, "Meaningful insights"],
            ].map(([Icon, label]) => {
              const I = Icon as typeof Activity;
              return (
                <span key={String(label)}>
                  <I size={18} />
                  {String(label)}
                </span>
              );
            })}
          </div>
        </div>
        <div className="story-footer">
          <ShieldCheck size={20} />
          <p>
            Educational Demo — Fictional Data Only
            <br />
            <small>Designed for your DBMS project. No medical advice.</small>
          </p>
        </div>
      </section>
      <section className="login-form-wrap">
        <div className="login-form">
          <span className="eyebrow">YOUR LEARNING WORKSPACE</span>
          <h2>Welcome back.</h2>
          <p>Sign in to continue to CareTrack.</p>
          {error && <ErrorBox message={error} />}
          <form onSubmit={submit}>
            <label>
              Email address
              <input
                type="email"
                autoComplete="username"
                required
                value={email}
                placeholder="you@caretrack.example.com"
                onChange={(e) => setEmail(e.target.value)}
              />
            </label>
            <label>
              Password
              <input
                type="password"
                autoComplete="current-password"
                required
                value={password}
                placeholder="Enter your password"
                onChange={(e) => setPassword(e.target.value)}
              />
            </label>
            <button className="button primary login-submit" disabled={busy}>
              {busy ? (
                <LoaderCircle size={17} className="spin" />
              ) : (
                <>
                  Sign in to workspace <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>
          <div className="demo-accounts">
            <b>Explore the educational demo</b>
            <p>
              Choose a role to fill its demo email. Password:{" "}
              <code>CareTrackDemo2026!</code>
            </p>
            <div>
              {[
                ["Admin", "admin"],
                ["Doctor", "doctor1"],
                ["Reception", "reception"],
              ].map(([label, name]) => (
                <button
                  className="button secondary"
                  key={name}
                  onClick={() => {
                    setEmail(name + "@caretrack.example.com");
                    setPassword("CareTrackDemo2026!");
                  }}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          <p className="login-disclaimer">
            CareTrack is an educational demonstration project using fictional
            data. It is not intended for real clinical use.
          </p>
        </div>
      </section>
    </div>
  );
}

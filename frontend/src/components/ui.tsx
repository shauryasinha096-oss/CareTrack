import {
  createContext,
  useContext,
  useState,
  type ReactNode,
  type FormEvent,
} from "react";
import {
  X,
  Check,
  AlertCircle,
  LoaderCircle,
  ChevronLeft,
  ChevronRight,
  Search,
} from "lucide-react";
import type { Field, Row } from "../types";
export const nice = (value: unknown) =>
  String(value ?? "—")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
export const dateLabel = (value: unknown) =>
  value
    ? new Date(String(value).slice(0, 10) + "T12:00:00").toLocaleDateString(
        "en-IN",
        { day: "numeric", month: "short", year: "numeric" },
      )
    : "—";
export const initials = (first: unknown, last: unknown = "") =>
  `${String(first || "").slice(0, 1)}${String(last || "").slice(0, 1)}`.toUpperCase();
export const today = () =>
  new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Kolkata",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
export function Badge({
  children,
  value,
}: {
  children?: ReactNode;
  value?: unknown;
}) {
  const text = String(value ?? children ?? "");
  return (
    <span className={`badge badge-${text.toLowerCase().replaceAll("_", "-")}`}>
      {children || nice(value)}
    </span>
  );
}
export function Spinner() {
  return (
    <div className="loading">
      <LoaderCircle className="spin" size={22} /> Loading records from MySQL…
    </div>
  );
}
export function ErrorBox({
  message,
  retry,
}: {
  message: string;
  retry?: () => void;
}) {
  return (
    <div className="error-box" role="alert">
      <AlertCircle size={18} />
      <span>{message}</span>
      {retry && (
        <button className="text-button" onClick={retry}>
          Retry
        </button>
      )}
    </div>
  );
}
export function Empty({
  title = "No records found",
  description = "Try another search or add your first fictional record.",
}: {
  title?: string;
  description?: string;
}) {
  return (
    <div className="empty">
      <Search size={28} />
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  );
}
export function Modal({
  title,
  children,
  onClose,
  wide = false,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  wide?: boolean;
}) {
  return (
    <div
      className="modal-overlay"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <section
        className={`modal ${wide ? "wide" : ""}`}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <div className="modal-heading">
          <div>
            <span className="eyebrow">CARETRACK WORKSPACE</span>
            <h2>{title}</h2>
          </div>
          <button
            className="icon-button"
            aria-label="Close dialog"
            onClick={onClose}
          >
            <X size={20} />
          </button>
        </div>
        {children}
      </section>
    </div>
  );
}
export function Pagination({
  page,
  total,
  size,
  onChange,
}: {
  page: number;
  total: number;
  size: number;
  onChange: (n: number) => void;
}) {
  const max = Math.max(1, Math.ceil(total / size));
  return (
    <div className="pagination">
      <span>
        {total === 0
          ? "0 records"
          : `${(page - 1) * size + 1}–${Math.min(page * size, total)} of ${total.toLocaleString()} records`}
      </span>
      <div>
        <button
          className="icon-button"
          aria-label="Previous page"
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
        >
          <ChevronLeft size={17} />
        </button>
        <span>
          Page {page} of {max}
        </span>
        <button
          className="icon-button"
          aria-label="Next page"
          disabled={page >= max}
          onClick={() => onChange(page + 1)}
        >
          <ChevronRight size={17} />
        </button>
      </div>
    </div>
  );
}
export function Fields({
  fields,
  value,
  onChange,
}: {
  fields: Field[];
  value: Row;
  onChange: (key: string, value: unknown) => void;
}) {
  return (
    <div className="form-grid">
      {fields.map((f) => (
        <label key={f.key} className={f.type === "textarea" ? "span-2" : ""}>
          <span>
            {f.label}
            {f.required && <b className="required"> *</b>}
          </span>
          {f.type === "select" ? (
            <select
              aria-label={f.label}
              required={f.required}
              value={String(value[f.key] ?? "")}
              onChange={(e) => onChange(f.key, e.target.value)}
            >
              <option value="">Select…</option>
              {f.options?.map((o) => (
                <option value={o.value} key={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          ) : f.type === "textarea" ? (
            <textarea
              aria-label={f.label}
              required={f.required}
              placeholder={f.placeholder}
              rows={3}
              value={String(value[f.key] ?? "")}
              onChange={(e) => onChange(f.key, e.target.value)}
            />
          ) : (
            <input
              aria-label={f.label}
              type={f.type || "text"}
              required={f.required}
              step={f.step}
              min={f.min}
              max={f.max}
              placeholder={f.placeholder}
              value={String(value[f.key] ?? "")}
              onChange={(e) =>
                onChange(
                  f.key,
                  f.type === "number" && e.target.value !== ""
                    ? Number(e.target.value)
                    : e.target.value,
                )
              }
            />
          )}
        </label>
      ))}
    </div>
  );
}
export function DetailGrid({
  data,
  omit = [],
}: {
  data: Row;
  omit?: string[];
}) {
  const entries = Object.entries(data).filter(
    ([k, v]) =>
      !omit.includes(k) &&
      v !== null &&
      v !== undefined &&
      typeof v !== "object",
  );
  return (
    <dl className="detail-grid">
      {entries.map(([k, v]) => (
        <div key={k}>
          <dt>{nice(k)}</dt>
          <dd>{String(v)}</dd>
        </div>
      ))}
    </dl>
  );
}
export function FormModal({
  title,
  fields,
  initial = {},
  onSubmit,
  onClose,
}: {
  title: string;
  fields: Field[];
  initial?: Row;
  onSubmit: (v: Row) => Promise<void>;
  onClose: () => void;
}) {
  const [value, setValue] = useState<Row>(initial),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await onSubmit(value);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal title={title} onClose={onClose} wide>
      <form onSubmit={submit}>
        {error && <ErrorBox message={error} />}
        <Fields
          fields={fields}
          value={value}
          onChange={(k, v) => setValue((p) => ({ ...p, [k]: v }))}
        />
        <div className="modal-footer">
          <p>Fictional data only</p>
          <button type="button" className="button secondary" onClick={onClose}>
            Cancel
          </button>
          <button disabled={busy} className="button primary">
            {busy ? (
              <LoaderCircle className="spin" size={16} />
            ) : (
              <Check size={16} />
            )}{" "}
            Save record
          </button>
        </div>
      </form>
    </Modal>
  );
}
const ToastContext = createContext<(message: string) => void>(() => {});
export function ToastProvider({ children }: { children: ReactNode }) {
  const [message, setMessage] = useState("");
  function toast(v: string) {
    setMessage(v);
    window.setTimeout(() => setMessage(""), 4500);
  }
  return (
    <ToastContext.Provider value={toast}>
      {children}
      {message && (
        <div role="status" className="toast">
          <Check size={18} />
          {message}
          <button
            aria-label="Dismiss notification"
            onClick={() => setMessage("")}
          >
            <X size={15} />
          </button>
        </div>
      )}
    </ToastContext.Provider>
  );
}
export const useToast = () => useContext(ToastContext);

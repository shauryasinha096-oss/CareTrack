import { useState } from "react";
import { Search, Check } from "lucide-react";
import { useApi } from "../hooks/useApi";
import { query } from "../services/api";
import type { Page, Patient } from "../types";
export default function PatientPicker({
  value,
  onChange,
}: {
  value: number;
  onChange: (id: number) => void;
}) {
  const [search, setSearch] = useState(""),
    [open, setOpen] = useState(false),
    [page, setPage] = useState(1);
  const { data } = useApi<Page<Patient>>(
    "/patients?" +
      query({
        q: search,
        page,
        page_size: 10,
        sort: "first_name",
        direction: "asc",
      }),
  );
  const selected = useApi<Patient>(value ? "/patients/" + value : null);
  return (
    <div className="patient-picker">
      <span>
        Patient <b className="required">*</b>
      </span>
      <button
        type="button"
        className="picker-button"
        onClick={() => setOpen((v) => !v)}
      >
        <Search size={16} />
        {selected.data
          ? `${selected.data.first_name} ${selected.data.last_name} · PT-${value}`
          : "Search and select a fictional patient…"}
      </button>
      {open && (
        <div className="picker-results">
          <input
            aria-label="Search patients to select"
            placeholder="Name, ID, email or phone…"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            autoFocus
          />
          {data?.items.map((p) => (
            <button
              type="button"
              key={p.patient_id}
              onClick={() => {
                onChange(p.patient_id);
                setOpen(false);
              }}
            >
              <span>
                <b>
                  {p.first_name} {p.last_name}
                </b>
                <small>
                  PT-{p.patient_id} · {p.city}
                </small>
              </span>
              {p.patient_id === value && <Check size={16} />}
            </button>
          ))}
          {!data?.items.length && <p>No matching patients</p>}
          <div className="picker-pagination">
            <button
              type="button"
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </button>
            <span>Page {page}</span>
            <button
              type="button"
              disabled={!data || page * 10 >= data.total}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

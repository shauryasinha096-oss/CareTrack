import { useEffect, useState } from "react";
import { api } from "../services/api";
export function useApi<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true),
    [revision, setRevision] = useState(0);
  useEffect(() => {
    if (!path) {
      setData(null);
      setLoading(false);
      return;
    }
    const c = new AbortController();
    setData(null);
    setLoading(true);
    setError("");
    api<T>(path, { signal: c.signal })
      .then((v) => {
        setData(v);
        setLoading(false);
      })
      .catch((e) => {
        if (e.name !== "AbortError") {
          setError(e.message);
          setLoading(false);
        }
      });
    return () => c.abort();
  }, [path, revision]);
  return { data, error, loading, refresh: () => setRevision((v) => v + 1) };
}

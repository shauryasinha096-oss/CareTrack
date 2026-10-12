export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}
// Full API prefix, including /api. Empty means the local Vite /api proxy.
const apiBase = (import.meta.env.VITE_API_URL || "/api")
  .trim()
  .replace(/\/+$/, "");
export const token = () => sessionStorage.getItem("caretrack.token");
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(apiBase + path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token() ? { Authorization: `Bearer ${token()}` } : {}),
      ...options.headers,
    },
  });
  const body = await res
    .json()
    .catch(() => ({ detail: "The server did not return a valid response" }));
  if (!res.ok) {
    if (res.status === 401 && path != "/auth/login") {
      sessionStorage.removeItem("caretrack.token");
      window.dispatchEvent(new Event("caretrack:expired"));
    }
    const detail = body.detail;
    const message = Array.isArray(detail)
      ? detail
          .map(
            (x: { loc: string[]; msg: string }) =>
              `${x.loc.slice(1).join(" · ")}: ${x.msg}`,
          )
          .join("; ")
      : String(detail || "Unable to complete this request");
    throw new ApiError(message, res.status);
  }
  return body as T;
}
export const write = <T>(path: string, body: unknown, method = "POST") =>
  api<T>(path, { method, body: JSON.stringify(body) });
export function query(params: Record<string, string | number | undefined>) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(params))
    if (v !== undefined && v !== "") p.set(k, String(v));
  return p.toString();
}

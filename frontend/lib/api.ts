export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
export function csrfToken() {
  if (typeof document === "undefined") return "";
  return decodeURIComponent(
    document.cookie
      .split("; ")
      .find((row) => row.startsWith("tl_csrf="))
      ?.split("=")
      .slice(1)
      .join("=") || "",
  );
}
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (options.method && options.method !== "GET") headers.set("X-CSRF-Token", csrfToken());
  const response = await fetch(`/api/v1${path}`, {
    ...options,
    headers,
    credentials: "include",
    cache: "no-store",
  });
  if (!response.ok) {
    const data = await response
      .json()
      .catch(() => ({ detail: "Unable to reach the service. Please retry." }));
    const detail =
      typeof data.detail === "string"
        ? data.detail
        : Array.isArray(data.detail)
          ? data.detail.map((item: { msg: string }) => item.msg).join(". ")
          : "Request failed";
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
export const send = (method: string, value?: unknown): RequestInit => ({
  method,
  body: value === undefined ? undefined : JSON.stringify(value),
});

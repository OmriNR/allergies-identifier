export class ApiError extends Error {
  status: number;

  constructor(message: string, status = 400) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const TOKEN_STORAGE_KEY = "auth:token";

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

function extractErrorMessage(body: unknown, fallback: string): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((d) => (d && typeof d === "object" && "msg" in d ? String((d as { msg: unknown }).msg) : String(d)))
        .join("; ");
    }
  }
  return fallback;
}

export interface RequestOptions {
  json?: unknown;
  form?: Record<string, string>;
  token?: string | null;
  query?: Record<string, string | number | undefined>;
}

// `url` is the full request URL (caller owns the base URL) - this client
// doesn't know or care which backend it's talking to.
async function request<T>(method: string, url: string, options: RequestOptions = {}): Promise<T> {
  const { json, form, token, query } = options;

  let fullUrl = url;
  if (query) {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) params.set(key, String(value));
    }
    const qs = params.toString();
    if (qs) fullUrl += (fullUrl.includes("?") ? "&" : "?") + qs;
  }

  const headers: Record<string, string> = {};
  const authToken = token !== undefined ? token : getStoredToken();
  if (authToken) headers.Authorization = `Bearer ${authToken}`;

  let body: BodyInit | undefined;
  if (form) {
    body = new URLSearchParams(form);
    headers["Content-Type"] = "application/x-www-form-urlencoded";
  } else if (json !== undefined) {
    body = JSON.stringify(json);
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(fullUrl, { method, headers, body });

  const text = await response.text();
  let data: unknown;
  try {
    data = text ? JSON.parse(text) : undefined;
  } catch {
    data = undefined;
  }

  if (!response.ok) {
    throw new ApiError(extractErrorMessage(data, response.statusText), response.status);
  }

  return data as T;
}

export function get<T>(url: string, options?: Omit<RequestOptions, "json" | "form">): Promise<T> {
  return request<T>("GET", url, options);
}

export function post<T>(url: string, options?: RequestOptions): Promise<T> {
  return request<T>("POST", url, options);
}

export function put<T>(url: string, options?: RequestOptions): Promise<T> {
  return request<T>("PUT", url, options);
}

export function patch<T>(url: string, options?: RequestOptions): Promise<T> {
  return request<T>("PATCH", url, options);
}

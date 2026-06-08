/**
 * Frontend API client — typed wrapper around the backend endpoints.
 *
 * Session auth is handled by the browser via the HttpOnly cookie set
 * during OAuth callback; every fetch goes out with credentials:
 * "include" so the cookie is sent automatically.
 */

export const API_BASE = "/api";

export class ApiError extends Error {
  status: number;
  body: string;
  constructor(status: number, body: string) {
    super(`API error ${status}: ${body.slice(0, 200)}`);
    this.status = status;
    this.body = body;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init.headers ?? {}) },
    ...init,
  });
  if (!resp.ok) {
    const body = await resp.text();
    throw new ApiError(resp.status, body);
  }
  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

export const api = {
  get: <T,>(path: string) => request<T>(path),
  post: <T,>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  patch: <T,>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  del: <T,>(path: string) => request<T>(path, { method: "DELETE" }),
};

// ---------------------------------------------------------------------------
// Auth + users
// ---------------------------------------------------------------------------

export interface CurrentUser {
  id: number;
  email: string;
  name: string | null;
  role: string;
  intro_seen: boolean;
}

export const auth = {
  logout: () => api.post<void>("/auth/logout", {}),
};

export const users = {
  me: () => api.get<CurrentUser>("/users/me"),
  markIntroSeen: () => api.patch<void>("/users/me/intro-seen", {}),
};

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------

export type ChatRole = "user" | "assistant";

export interface ChatMessage {
  role: ChatRole;
  content: string;
}

export interface ToolCallTrace {
  name: string;
  params: Record<string, unknown>;
  result: Record<string, unknown>;
}

export type ContactType =
  | "Client"
  | "Partner"
  | "Vendor"
  | "Advisor"
  | "Other";

export interface ContactCardData {
  id: number;
  name: string;
  email: string | null;
  cell_phone: string | null;
  office_phone: string | null;
  title: string | null;
  company_name: string | null;
  contact_type: ContactType | string;
  country: string | null;
  notes: string | null;
  is_private: boolean;
  is_self_owned: boolean;
  owner_id: number;
}

export interface ExportFilter {
  query?: string;
  contact_type?: ContactType;
}

export interface SearchContactsResult {
  results: ContactCardData[];
  limit: number;
  truncated: boolean;
}

export interface ChatRequestBody {
  message: string;
  history: ChatMessage[];
  mode: "text" | "voice";
}

export interface ChatResponse {
  reply: string;
  tool_calls: ToolCallTrace[];
  input_tokens_used: number;
  output_tokens_used: number;
}

export const CHAT_INPUT_MAX_CHARS = 4000;

export const chat = {
  send: (body: ChatRequestBody) => api.post<ChatResponse>("/chat", body),
};

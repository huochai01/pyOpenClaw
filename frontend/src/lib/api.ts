export type SessionSummary = {
  id: string;
  title: string;
  created_at: number;
  updated_at: number;
  message_count: number;
};

export type SessionHistory = {
  id: string;
  title: string;
  messages: Array<{
    role: "user" | "assistant";
    content: string;
    tool_calls?: Array<{ tool: string; input?: unknown; output?: unknown }>;
  }>;
  compressed_context?: string;
};

export type SseEvent =
  | { type: "retrieval"; data: { query: string; results: Array<{ text: string; score: number; source: string }> } }
  | { type: "token"; data: { content: string } }
  | { type: "tool_start"; data: { tool: string; input: unknown } }
  | { type: "tool_end"; data: { tool: string; output: unknown } }
  | { type: "new_response"; data: 0 }
  | { type: "done"; data: { content: string; session_id?: string } }
  | { type: "title"; data: { session_id: string; title: string } }
  | { type: "error"; data: { error: string } };

export type ScheduledSessionEvent =
  | { type: "scheduled_start"; data: { run_id: string; user_content: string } }
  | { type: "scheduled_token"; data: { run_id: string; content: string } }
  | { type: "scheduled_tool_start"; data: { run_id: string; tool: string; input: unknown } }
  | { type: "scheduled_tool_end"; data: { run_id: string; tool: string; output: unknown } }
  | { type: "scheduled_done"; data: { run_id: string; content: string } }
  | { type: "scheduled_error"; data: { run_id: string; error: string; content?: string } };

export type FileEntry = {
  name: string;
  path: string;
};

function getApiBase() {
  if (typeof window === "undefined") {
    return "http://127.0.0.1:8010/api";
  }
  return `http://${window.location.hostname}:8010/api`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = init?.body instanceof FormData;
  const response = await fetch(`${getApiBase()}${path}`, {
    ...init,
    headers: isFormData
      ? init?.headers
      : {
          "Content-Type": "application/json",
          ...(init?.headers ?? {})
        }
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export async function listSessions() {
  return request<SessionSummary[]>("/sessions");
}

export async function createSession() {
  return request<SessionHistory>("/sessions", { method: "POST" });
}

export async function getSessionHistory(sessionId: string) {
  return request<SessionHistory>(`/sessions/${sessionId}/history`);
}

export async function renameSession(sessionId: string, title: string) {
  return request(`/sessions/${sessionId}`, {
    method: "PUT",
    body: JSON.stringify({ title })
  });
}

export async function deleteSession(sessionId: string) {
  return request(`/sessions/${sessionId}`, { method: "DELETE" });
}

export async function compressSession(sessionId: string) {
  return request<{ archived_count: number; remaining_count: number }>(`/sessions/${sessionId}/compress`, {
    method: "POST"
  });
}

export async function getFile(path: string) {
  return request<{ path: string; content: string }>(`/files?path=${encodeURIComponent(path)}`);
}

export async function saveFile(path: string, content: string) {
  return request<{ ok: boolean; path: string }>("/files", {
    method: "POST",
    body: JSON.stringify({ path, content })
  });
}

export async function listSkills() {
  return request<Array<{ name: string; path: string }>>("/skills");
}

export async function listKnowledgeFiles() {
  return request<FileEntry[]>("/knowledge/files");
}

export async function uploadKnowledgeFile(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return request<{ ok: boolean; path: string }>("/knowledge/upload", {
    method: "POST",
    body: formData
  });
}

export async function deleteKnowledgeFile(path: string) {
  return request<{ ok: boolean; path: string }>(`/knowledge/files?path=${encodeURIComponent(path)}`, {
    method: "DELETE"
  });
}

export async function getRagMode() {
  return request<{ enabled: boolean }>("/config/rag-mode");
}

export async function setRagMode(enabled: boolean) {
  return request<{ enabled: boolean }>("/config/rag-mode", {
    method: "PUT",
    body: JSON.stringify({ enabled })
  });
}

export async function getSessionTokens(sessionId: string) {
  return request<{ system_tokens: number; message_tokens: number; total_tokens: number }>(
    `/tokens/session/${sessionId}`
  );
}

export async function streamChat(
  message: string,
  sessionId: string,
  onEvent: (event: SseEvent) => void
) {
  const response = await fetch(`${getApiBase()}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      stream: true
    })
  });

  if (!response.ok || !response.body) {
    throw new Error(await response.text());
  }

  const decoder = new TextDecoder();
  const reader = response.body.getReader();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      const lines = part.split("\n");
      const eventLine = lines.find((line) => line.startsWith("event: "));
      const dataLine = lines.find((line) => line.startsWith("data: "));
      if (!eventLine || !dataLine) {
        continue;
      }
      const type = eventLine.slice(7) as SseEvent["type"];
      const data = JSON.parse(dataLine.slice(6));
      onEvent({ type, data } as SseEvent);
    }
  }
}

export function openSessionEvents(
  sessionId: string,
  onEvent: (event: ScheduledSessionEvent) => void
) {
  const source = new EventSource(`${getApiBase()}/sessions/${sessionId}/events`);
  const eventTypes: ScheduledSessionEvent["type"][] = [
    "scheduled_start",
    "scheduled_token",
    "scheduled_tool_start",
    "scheduled_tool_end",
    "scheduled_done",
    "scheduled_error"
  ];

  for (const type of eventTypes) {
    source.addEventListener(type, (rawEvent) => {
      const messageEvent = rawEvent as MessageEvent<string>;
      onEvent({ type, data: JSON.parse(messageEvent.data) } as ScheduledSessionEvent);
    });
  }

  return source;
}

"use client";

import {
  compressSession,
  createSession,
  deleteSession,
  getFile,
  getRagMode,
  getSessionHistory,
  getSessionTokens,
  listSessions,
  listSkills,
  saveFile,
  setRagMode,
  streamChat,
  type SessionSummary,
  type SseEvent
} from "@/lib/api";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren
} from "react";

export type ToolCall = {
  tool: string;
  input?: unknown;
  output?: unknown;
};

export type RetrievalItem = {
  text: string;
  score: number;
  source: string;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolCalls: ToolCall[];
  retrievals: RetrievalItem[];
};

type StoreValue = {
  sessions: SessionSummary[];
  currentSessionId: string | null;
  messages: ChatMessage[];
  isStreaming: boolean;
  sidebarWidth: number;
  inspectorWidth: number;
  selectedFile: string;
  fileContent: string;
  skills: Array<{ name: string; path: string }>;
  ragEnabled: boolean;
  tokenStats: { system_tokens: number; message_tokens: number; total_tokens: number } | null;
  isFileDirty: boolean;
  setSidebarWidth: (next: number) => void;
  setInspectorWidth: (next: number) => void;
  loadSession: (sessionId: string) => Promise<void>;
  createNewSession: () => Promise<void>;
  sendMessage: (text: string) => Promise<void>;
  selectFile: (path: string) => Promise<void>;
  setFileContent: (next: string) => void;
  persistFile: () => Promise<void>;
  refreshSessions: () => Promise<void>;
  toggleRagMode: (enabled: boolean) => Promise<void>;
  compressCurrentSession: () => Promise<void>;
  deleteExistingSession: (sessionId: string) => Promise<void>;
};

const StoreContext = createContext<StoreValue | null>(null);

function makeId() {
  return Math.random().toString(36).slice(2);
}

function mapSessionMessages(
  session: Awaited<ReturnType<typeof getSessionHistory>>
): ChatMessage[] {
  return session.messages.map((message) => ({
    id: makeId(),
    role: message.role,
    content: message.content,
    toolCalls: message.tool_calls ?? [],
    retrievals: []
  }));
}

function areMessagesEqual(left: ChatMessage[], right: ChatMessage[]) {
  if (left.length !== right.length) {
    return false;
  }
  return left.every((message, index) => {
    const next = right[index];
    if (!next) {
      return false;
    }
    return (
      message.role === next.role &&
      message.content === next.content &&
      JSON.stringify(message.toolCalls) === JSON.stringify(next.toolCalls)
    );
  });
}

function updateLastAssistantMessage(
  items: ChatMessage[],
  updater: (message: ChatMessage) => ChatMessage
): ChatMessage[] {
  if (items.length === 0) {
    return items;
  }
  const last = items[items.length - 1];
  if (last.role !== "assistant") {
    return items;
  }
  return [...items.slice(0, -1), updater(last)];
}

export function AppProvider({ children }: PropsWithChildren) {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(280);
  const [inspectorWidth, setInspectorWidth] = useState(470);
  const [selectedFile, setSelectedFile] = useState("memory/MEMORY.md");
  const [fileContent, setFileContentState] = useState("");
  const [savedFileContent, setSavedFileContent] = useState("");
  const [skills, setSkills] = useState<Array<{ name: string; path: string }>>([]);
  const [ragEnabled, setRagEnabled] = useState(false);
  const [tokenStats, setTokenStats] = useState<StoreValue["tokenStats"]>(null);

  const isFileDirty = fileContent !== savedFileContent;

  const refreshSessions = useCallback(async () => {
    const next = await listSessions();
    setSessions(next);
    if (!currentSessionId && next[0]) {
      setCurrentSessionId(next[0].id);
    }
  }, [currentSessionId]);

  const refreshMeta = useCallback(async () => {
    const [skillsData, ragData] = await Promise.all([listSkills(), getRagMode()]);
    setSkills(skillsData);
    setRagEnabled(ragData.enabled);
  }, []);

  const loadSession = useCallback(async (sessionId: string) => {
    const session = await getSessionHistory(sessionId);
    setCurrentSessionId(sessionId);
    setMessages(mapSessionMessages(session));
    const stats = await getSessionTokens(sessionId);
    setTokenStats(stats);
  }, []);

  const syncSessionSilently = useCallback(
    async (sessionId: string) => {
      const session = await getSessionHistory(sessionId);
      const nextMessages = mapSessionMessages(session);
      setMessages((prev) => (areMessagesEqual(prev, nextMessages) ? prev : nextMessages));
      const stats = await getSessionTokens(sessionId);
      setTokenStats(stats);
    },
    []
  );

  const createNewSession = useCallback(async () => {
    const session = await createSession();
    await refreshSessions();
    await loadSession(session.id);
  }, [loadSession, refreshSessions]);

  const selectFile = useCallback(async (path: string) => {
    const file = await getFile(path);
    setSelectedFile(path);
    setFileContentState(file.content);
    setSavedFileContent(file.content);
  }, []);

  const setFileContent = useCallback((next: string) => {
    setFileContentState(next);
  }, []);

  const persistFile = useCallback(async () => {
    await saveFile(selectedFile, fileContent);
    setSavedFileContent(fileContent);
  }, [fileContent, selectedFile]);

  const toggleRagMode = useCallback(async (enabled: boolean) => {
    await setRagMode(enabled);
    setRagEnabled(enabled);
  }, []);

  const compressCurrentSession = useCallback(async () => {
    if (!currentSessionId) return;
    if (!window.confirm("确定要压缩当前会话历史吗？此操作会归档前半段消息。")) return;
    await compressSession(currentSessionId);
    await loadSession(currentSessionId);
    await refreshSessions();
  }, [currentSessionId, loadSession, refreshSessions]);

  const deleteExistingSession = useCallback(
    async (sessionId: string) => {
      if (!window.confirm("确定要删除这条历史会话吗？")) return;
      const remaining = sessions.filter((session) => session.id !== sessionId);
      await deleteSession(sessionId);
      if (currentSessionId === sessionId) {
        setCurrentSessionId(remaining[0]?.id ?? null);
        if (!remaining.length) {
          setMessages([]);
          setTokenStats(null);
        }
      }
      await refreshSessions();
    },
    [currentSessionId, refreshSessions, sessions]
  );

  const sendMessage = useCallback(
    async (text: string) => {
      let sessionId = currentSessionId;
      if (!sessionId) {
        const session = await createSession();
        sessionId = session.id;
        setCurrentSessionId(sessionId);
      }

      const userMessage: ChatMessage = {
        id: makeId(),
        role: "user",
        content: text,
        toolCalls: [],
        retrievals: []
      };
      const assistantMessage: ChatMessage = {
        id: makeId(),
        role: "assistant",
        content: "",
        toolCalls: [],
        retrievals: []
      };
      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setIsStreaming(true);

      const handleEvent = (event: SseEvent) => {
        if (event.type === "retrieval") {
          setMessages((prev) =>
            updateLastAssistantMessage(prev, (last) => ({
              ...last,
              retrievals: [...event.data.results]
            }))
          );
          return;
        }

        if (event.type === "token") {
          setMessages((prev) =>
            updateLastAssistantMessage(prev, (last) => ({
              ...last,
              content: last.content + event.data.content
            }))
          );
          return;
        }

        if (event.type === "tool_start") {
          setMessages((prev) =>
            updateLastAssistantMessage(prev, (last) => ({
              ...last,
              toolCalls: [...last.toolCalls, { tool: event.data.tool, input: event.data.input }]
            }))
          );
          return;
        }

        if (event.type === "tool_end") {
          setMessages((prev) =>
            updateLastAssistantMessage(prev, (last) => {
              if (last.toolCalls.length === 0) {
                return last;
              }
              const nextToolCalls = [...last.toolCalls];
              const currentTool = nextToolCalls[nextToolCalls.length - 1];
              nextToolCalls[nextToolCalls.length - 1] = {
                ...currentTool,
                output: event.data.output
              };
              return {
                ...last,
                toolCalls: nextToolCalls
              };
            })
          );
          return;
        }

        if (event.type === "new_response") {
          setMessages((prev) => [
            ...prev,
            { id: makeId(), role: "assistant", content: "", toolCalls: [], retrievals: [] }
          ]);
          return;
        }

        if (event.type === "done") {
          setIsStreaming(false);
          return;
        }

        if (event.type === "title") {
          void refreshSessions();
          return;
        }

        if (event.type === "error") {
          setIsStreaming(false);
          setMessages((prev) => [
            ...prev,
            {
              id: makeId(),
              role: "assistant",
              content: `发生错误: ${event.data.error}`,
              toolCalls: [],
              retrievals: []
            }
          ]);
        }
      };

      await streamChat(text, sessionId, handleEvent);
      await refreshSessions();
      const stats = await getSessionTokens(sessionId);
      setTokenStats(stats);
    },
    [currentSessionId, refreshSessions]
  );

  useEffect(() => {
    void refreshSessions();
    void refreshMeta();
    void selectFile("memory/MEMORY.md");
  }, [refreshMeta, refreshSessions, selectFile]);

  useEffect(() => {
    if (currentSessionId) {
      void loadSession(currentSessionId);
    }
  }, [currentSessionId, loadSession]);

  useEffect(() => {
    if (!currentSessionId || isStreaming) {
      return;
    }

    const timer = window.setInterval(() => {
      void syncSessionSilently(currentSessionId);
      void refreshSessions();
    }, 1000);

    return () => window.clearInterval(timer);
  }, [currentSessionId, isStreaming, refreshSessions, syncSessionSilently]);

  const value = useMemo<StoreValue>(
    () => ({
      sessions,
      currentSessionId,
      messages,
      isStreaming,
      sidebarWidth,
      inspectorWidth,
      selectedFile,
      fileContent,
      skills,
      ragEnabled,
      tokenStats,
      isFileDirty,
      setSidebarWidth: (next) => setSidebarWidth(Math.max(220, Math.min(420, next))),
      setInspectorWidth: (next) => setInspectorWidth(Math.max(340, Math.min(640, next))),
      loadSession,
      createNewSession,
      sendMessage,
      selectFile,
      setFileContent,
      persistFile,
      refreshSessions,
      toggleRagMode,
      compressCurrentSession,
      deleteExistingSession
    }),
    [
      createNewSession,
      currentSessionId,
      deleteExistingSession,
      fileContent,
      inspectorWidth,
      isFileDirty,
      isStreaming,
      loadSession,
      messages,
      persistFile,
      ragEnabled,
      refreshSessions,
      selectedFile,
      selectFile,
      sendMessage,
      sessions,
      sidebarWidth,
      skills,
      tokenStats,
      toggleRagMode,
      compressCurrentSession,
      setFileContent
    ]
  );

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}

export function useAppStore() {
  const value = useContext(StoreContext);
  if (!value) {
    throw new Error("useAppStore must be used within AppProvider");
  }
  return value;
}

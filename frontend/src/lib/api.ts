import { type BoardData } from "@/lib/kanban";

const BOARD_ENDPOINT = "/api/board?username=user";
const AI_CHAT_ENDPOINT = "/api/ai/chat?username=user";

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type ChatResult = {
  model: string;
  assistant_response: string;
  board_updated: boolean;
  board: BoardData;
};

const parseError = async (response: Response) => {
  try {
    const payload = await response.json();
    if (typeof payload?.detail === "string") {
      return payload.detail;
    }
  } catch {
    // Ignore parse errors and fallback to status text.
  }
  return response.statusText || "Request failed";
};

export const fetchBoard = async (): Promise<BoardData> => {
  const response = await fetch(BOARD_ENDPOINT, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to load board: ${await parseError(response)}`);
  }

  return (await response.json()) as BoardData;
};

export const saveBoard = async (board: BoardData): Promise<BoardData> => {
  const response = await fetch(BOARD_ENDPOINT, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(board),
  });

  if (!response.ok) {
    throw new Error(`Failed to save board: ${await parseError(response)}`);
  }

  return (await response.json()) as BoardData;
};

export const chatWithAi = async (
  question: string,
  history: ChatMessage[]
): Promise<ChatResult> => {
  const response = await fetch(AI_CHAT_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, history }),
  });

  if (!response.ok) {
    throw new Error(`Failed to chat with AI: ${await parseError(response)}`);
  }

  return (await response.json()) as ChatResult;
};

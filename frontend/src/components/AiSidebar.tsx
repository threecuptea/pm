"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { chatWithAi, type ChatMessage } from "@/lib/api";
import type { BoardData } from "@/lib/kanban";

type AiSidebarProps = {
  isReady: boolean;
  onBoardUpdate: (board: BoardData) => void;
};

export const AiSidebar = ({ isReady, onBoardUpdate }: AiSidebarProps) => {
  const [aiInput, setAiInput] = useState("");
  const [aiHistory, setAiHistory] = useState<ChatMessage[]>([]);
  const [aiError, setAiError] = useState<string | null>(null);
  const [aiModel, setAiModel] = useState<string | null>(null);
  const [isAiSubmitting, setIsAiSubmitting] = useState(false);
  const aiHistoryViewportRef = useRef<HTMLDivElement | null>(null);

  const handleSubmitAi = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const question = aiInput.trim();
    if (!question || isAiSubmitting) {
      return;
    }

    const historySnapshot = aiHistory;
    const userMessage: ChatMessage = { role: "user", content: question };
    setAiInput("");
    setAiError(null);
    setIsAiSubmitting(true);
    setAiHistory((prev) => [...prev, userMessage]);

    try {
      const response = await chatWithAi(question, historySnapshot);
      setAiModel(response.model);
      setAiHistory((prev) => [
        ...prev,
        { role: "assistant", content: response.assistant_response },
      ]);

      if (response.board_updated) {
        onBoardUpdate(response.board);
      }
    } catch (error) {
      setAiError(
        error instanceof Error ? error.message : "Failed to get AI response"
      );
      setAiHistory(historySnapshot);
      setAiInput(question);
    } finally {
      setIsAiSubmitting(false);
    }
  };

  useEffect(() => {
    if (!aiHistoryViewportRef.current) {
      return;
    }
    aiHistoryViewportRef.current.scrollTop = aiHistoryViewportRef.current.scrollHeight;
  }, [aiHistory]);

  return (
    <aside
      data-testid="ai-sidebar"
      className="flex h-[620px] min-h-[520px] flex-col rounded-[28px] border border-[var(--stroke)] bg-white/85 p-5 shadow-[var(--shadow)] backdrop-blur"
    >
      <div className="border-b border-[var(--stroke)] pb-4">
        <p className="text-xs font-semibold uppercase tracking-[0.26em] text-[var(--gray-text)]">
          AI Copilot
        </p>
        <h2 className="mt-2 font-display text-2xl font-semibold text-[var(--navy-dark)]">
          Board Assistant
        </h2>
        <p className="mt-2 text-xs leading-5 text-[var(--gray-text)]">
          Ask for prioritization help or direct board changes.
        </p>
        {aiModel ? (
          <p className="mt-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--primary-blue)]">
            Model: {aiModel}
          </p>
        ) : null}
      </div>

      <div
        ref={aiHistoryViewportRef}
        className="mt-4 flex-1 space-y-3 overflow-y-auto pr-1"
        aria-live="polite"
      >
        {aiHistory.length === 0 ? (
          <p className="rounded-xl border border-dashed border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-xs text-[var(--gray-text)]">
            Try: "Move card-1 into Review" or "Suggest top 3 priorities for this board."
          </p>
        ) : null}
        {aiHistory.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={
              message.role === "assistant"
                ? "rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--navy-dark)]"
                : "ml-auto max-w-[92%] rounded-2xl bg-[var(--primary-blue)] px-3 py-2 text-sm text-white"
            }
          >
            {message.content}
          </div>
        ))}
      </div>

      {aiError ? (
        <p className="mt-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs font-medium text-red-700">
          {aiError}
        </p>
      ) : null}

      <form onSubmit={handleSubmitAi} className="mt-4 space-y-2">
        <label
          htmlFor="ai-message"
          className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]"
        >
          Ask AI
        </label>
        <textarea
          id="ai-message"
          value={aiInput}
          onChange={(event) => setAiInput(event.target.value)}
          placeholder="Ask for advice or describe a board edit..."
          className="min-h-[86px] w-full resize-none rounded-2xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)] focus:ring-2 focus:ring-[rgba(32,157,215,0.2)]"
        />
        <button
          type="submit"
          disabled={isAiSubmitting || !aiInput.trim() || !isReady}
          className="w-full rounded-2xl bg-[var(--secondary-purple)] px-4 py-2 text-sm font-semibold text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isAiSubmitting ? "Thinking..." : "Send"}
        </button>
      </form>
    </aside>
  );
};

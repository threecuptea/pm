import { describe, expect, it, vi } from "vitest";

import { chatWithAi, fetchBoard, saveBoard } from "@/lib/api";

const boardPayload = {
  columns: [{ id: "col-backlog", title: "Backlog", cardIds: [] }],
  cards: {},
};

describe("api", () => {
  it("fetchBoard returns board data", async () => {
    const fetchMock = vi
      .spyOn(global, "fetch")
      .mockResolvedValue(new Response(JSON.stringify(boardPayload), { status: 200 }));

    const result = await fetchBoard();

    expect(result.columns[0].title).toBe("Backlog");
    expect(fetchMock).toHaveBeenCalledOnce();

    fetchMock.mockRestore();
  });

  it("saveBoard sends payload and returns board data", async () => {
    const fetchMock = vi
      .spyOn(global, "fetch")
      .mockResolvedValue(new Response(JSON.stringify(boardPayload), { status: 200 }));

    const result = await saveBoard(boardPayload);

    expect(result.columns[0].title).toBe("Backlog");
    expect(fetchMock).toHaveBeenCalledOnce();
    const [, options] = fetchMock.mock.calls[0];
    expect(options?.method).toBe("PUT");

    fetchMock.mockRestore();
  });

  it("fetchBoard throws readable error on failure", async () => {
    const fetchMock = vi
      .spyOn(global, "fetch")
      .mockResolvedValue(new Response(JSON.stringify({ detail: "broken" }), { status: 500 }));

    await expect(fetchBoard()).rejects.toThrow("Failed to load board: broken");

    fetchMock.mockRestore();
  });

  it("chatWithAi sends question and returns result", async () => {
    const chatPayload = {
      model: "openai/gpt-oss-120b",
      assistant_response: "No change needed.",
      board_updated: false,
      board: boardPayload,
    };

    const fetchMock = vi
      .spyOn(global, "fetch")
      .mockResolvedValue(new Response(JSON.stringify(chatPayload), { status: 200 }));

    const result = await chatWithAi("What next?", [
      { role: "user", content: "Help me prioritize." },
    ]);

    expect(result.assistant_response).toBe("No change needed.");
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/ai/chat?username=user");
    expect(options?.method).toBe("POST");

    fetchMock.mockRestore();
  });

  it("chatWithAi throws readable error on failure", async () => {
    const fetchMock = vi
      .spyOn(global, "fetch")
      .mockResolvedValue(
        new Response(JSON.stringify({ detail: "provider unavailable" }), {
          status: 502,
        })
      );

    await expect(chatWithAi("hello", [])).rejects.toThrow(
      "Failed to chat with AI: provider unavailable"
    );

    fetchMock.mockRestore();
  });
});

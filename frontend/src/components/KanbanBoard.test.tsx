import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, vi } from "vitest";
import { KanbanBoard } from "@/components/KanbanBoard";
import { initialData } from "@/lib/kanban";

const getFirstColumn = () => screen.getAllByTestId(/column-/i)[0];
let fetchMock: ReturnType<typeof vi.spyOn>;

describe("KanbanBoard", () => {
  beforeEach(() => {
    fetchMock = vi.spyOn(global, "fetch").mockImplementation((input, init) => {
      const method = (init?.method ?? "GET").toUpperCase();
      const url = typeof input === "string" ? input : input.toString();

      if (method === "POST" && url.includes("/api/ai/chat")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              model: "openai/gpt-oss-120b",
              assistant_response: "Try moving discovery items into review.",
              board_updated: false,
              board: initialData,
            }),
            { status: 200 }
          )
        );
      }

      if (method === "GET") {
        return Promise.resolve(
          new Response(JSON.stringify(initialData), { status: 200 })
        );
      }
      return Promise.resolve(
        new Response(JSON.stringify(initialData), { status: 200 })
      );
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders five columns", () => {
    render(<KanbanBoard />);
    expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
  });

  it("renames a column", async () => {
    render(<KanbanBoard />);
    const column = getFirstColumn();
    const input = within(column).getByLabelText("Column title");

    await waitFor(() => {
      expect(input).toHaveValue("Backlog");
    });

    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    expect(input).toHaveValue("New Name");
  });

  it("adds and removes a card", async () => {
    render(<KanbanBoard />);
    const column = getFirstColumn();
    const addButton = within(column).getByRole("button", {
      name: /add a card/i,
    });
    await userEvent.click(addButton);

    const titleInput = within(column).getByPlaceholderText(/card title/i);
    await userEvent.type(titleInput, "New card");
    const detailsInput = within(column).getByPlaceholderText(/details/i);
    await userEvent.type(detailsInput, "Notes");

    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    expect(within(column).getByText("New card")).toBeInTheDocument();

    const deleteButton = within(column).getByRole("button", {
      name: /delete new card/i,
    });
    await userEvent.click(deleteButton);

    expect(within(column).queryByText("New card")).not.toBeInTheDocument();
  });

  it("submits an AI message and shows the response", async () => {
    render(<KanbanBoard />);

    await waitFor(() => {
      expect(screen.getAllByLabelText("Column title").length).toBeGreaterThan(0);
    });

    await userEvent.type(screen.getByLabelText("Ask AI"), "What should I do next?");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => {
      expect(
        screen.getByText("Try moving discovery items into review.")
      ).toBeInTheDocument();
    });
  });

  it("applies AI board updates immediately", async () => {
    render(<KanbanBoard />);

    await waitFor(() => {
      expect(screen.getAllByLabelText("Column title")[0]).toHaveValue("Backlog");
    });

    const updatedBoard = {
      ...initialData,
      columns: initialData.columns.map((column, index) =>
        index === 0 ? { ...column, title: "AI Backlog" } : column
      ),
    };

    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          model: "openai/gpt-oss-120b",
          assistant_response: "Updated your board.",
          board_updated: true,
          board: updatedBoard,
        }),
        { status: 200 }
      )
    );

    await userEvent.type(screen.getByLabelText("Ask AI"), "Rename backlog");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => {
      expect(screen.getAllByLabelText("Column title")[0]).toHaveValue("AI Backlog");
    });
  });
});

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { KanbanBoard } from "@/components/KanbanBoard";
import { initialData } from "@/lib/kanban";

const buildMutatedBoard = () => {
  const cardId = "card-ai";
  return {
    ...initialData,
    cards: {
      ...initialData.cards,
      [cardId]: {
        id: cardId,
        title: "AI added card",
        details: "Created via AI response",
      },
    },
    columns: initialData.columns.map((column, index) =>
      index === 0 ? { ...column, cardIds: [...column.cardIds, cardId] } : column
    ),
  };
};

describe("KanbanBoard AI chat", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("shows assistant response without board mutation", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (!init?.method && url.includes("/api/board/user")) {
        return {
          ok: true,
          json: async () => ({ board: initialData }),
        } as Response;
      }
      if (url.includes("/api/ai/chat/user")) {
        return {
          ok: true,
          json: async () => ({
            status: "ok",
            model: "openrouter/free",
            reply: "No board changes needed.",
            boardUpdated: false,
            board: null,
          }),
        } as Response;
      }
      throw new Error(`Unhandled fetch: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<KanbanBoard username="user" />);
    await screen.findByTestId("column-col-backlog");

    await userEvent.type(screen.getByLabelText(/chat prompt/i), "Summarize my board");
    await userEvent.click(screen.getByRole("button", { name: /send to ai/i }));

    expect(await screen.findByText("No board changes needed.")).toBeInTheDocument();
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/ai/chat/user",
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
        })
      );
    });
  });

  it("applies AI mutation and refreshes board", async () => {
    const mutatedBoard = buildMutatedBoard();
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (!init?.method && url.includes("/api/board/user")) {
        return {
          ok: true,
          json: async () => ({ board: mutatedBoard }),
        } as Response;
      }
      if (url.includes("/api/ai/chat/user")) {
        return {
          ok: true,
          json: async () => ({
            status: "ok",
            model: "openrouter/free",
            reply: "Added a new backlog card.",
            boardUpdated: true,
            board: mutatedBoard,
          }),
        } as Response;
      }
      throw new Error(`Unhandled fetch: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<KanbanBoard username="user" />);
    await screen.findByTestId("column-col-backlog");

    await userEvent.type(screen.getByLabelText(/chat prompt/i), "Add a new backlog card");
    await userEvent.click(screen.getByRole("button", { name: /send to ai/i }));

    expect(await screen.findByText("AI added card")).toBeInTheDocument();
    await waitFor(() => {
      const getCalls = fetchMock.mock.calls.filter(
        ([input, init]) => String(input).includes("/api/board/user") && !init?.method
      );
      expect(getCalls.length).toBeGreaterThanOrEqual(2);
    });
  });

  it("shows an error message on invalid AI payload", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (!init?.method && url.includes("/api/board/user")) {
        return {
          ok: true,
          json: async () => ({ board: initialData }),
        } as Response;
      }
      if (url.includes("/api/ai/chat/user")) {
        return {
          ok: true,
          json: async () => ({ status: "ok", boardUpdated: false }),
        } as Response;
      }
      throw new Error(`Unhandled fetch: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<KanbanBoard username="user" />);
    await screen.findByTestId("column-col-backlog");

    await userEvent.type(screen.getByLabelText(/chat prompt/i), "Do something");
    await userEvent.click(screen.getByRole("button", { name: /send to ai/i }));

    expect(
      await screen.findByText("Unable to get AI response right now. Please try again.")
    ).toBeInTheDocument();
  });
});

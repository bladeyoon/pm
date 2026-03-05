import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { KanbanBoard } from "@/components/KanbanBoard";
import { initialData } from "@/lib/kanban";

describe("KanbanBoard persistence", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("loads board from backend when username is provided", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        ({
          ok: true,
          json: async () => ({ board: initialData }),
        }) as Response
      )
    );

    render(<KanbanBoard username="user" />);

    expect(await screen.findByTestId("column-col-backlog")).toBeInTheDocument();
    expect(global.fetch).toHaveBeenCalledWith(
      "/api/board/user",
      expect.objectContaining({ cache: "no-store" })
    );
  });

  it("persists board changes via PUT", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (!init?.method) {
        return {
          ok: true,
          json: async () => ({ board: initialData }),
        } as Response;
      }
      return {
        ok: true,
        json: async () => ({ ok: true }),
      } as Response;
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<KanbanBoard username="user" />);
    const firstColumn = await screen.findByTestId("column-col-backlog");
    const input = within(firstColumn).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "Updated");

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/board/user",
        expect.objectContaining({
          method: "PUT",
          headers: { "Content-Type": "application/json" },
        })
      );
    });
  });
});

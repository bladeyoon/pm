import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Home from "@/app/page";
import { initialData } from "@/lib/kanban";
import { vi } from "vitest";

const AUTH_STORAGE_KEY = "kanban-authenticated";
const AUTH_USERNAME_STORAGE_KEY = "kanban-username";

describe("Home auth flow", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    vi.restoreAllMocks();
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        ({
          ok: true,
          json: async () => ({ board: initialData }),
        }) as Response
      )
    );
  });

  it("shows login before authentication", () => {
    render(<Home />);

    expect(screen.getByRole("heading", { name: "Kanban Studio" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
    expect(screen.queryByTestId("column-col-backlog")).not.toBeInTheDocument();
  });

  it("rejects invalid credentials", async () => {
    render(<Home />);

    await userEvent.type(screen.getByLabelText(/username/i), "wrong");
    await userEvent.type(screen.getByLabelText(/password/i), "bad");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(
      screen.getByText("Invalid credentials. Use user / password.")
    ).toBeInTheDocument();
    expect(screen.queryByTestId("column-col-backlog")).not.toBeInTheDocument();
  });

  it("allows login and logout with demo credentials", async () => {
    render(<Home />);

    await userEvent.type(screen.getByLabelText(/username/i), "user");
    await userEvent.type(screen.getByLabelText(/password/i), "password");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByTestId("column-col-backlog")).toBeInTheDocument();
    expect(window.sessionStorage.getItem(AUTH_STORAGE_KEY)).toBe("true");
    expect(window.sessionStorage.getItem(AUTH_USERNAME_STORAGE_KEY)).toBe("user");

    await userEvent.click(screen.getByRole("button", { name: /log out/i }));
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
    expect(window.sessionStorage.getItem(AUTH_STORAGE_KEY)).toBeNull();
  });

  it("restores authenticated session from sessionStorage", async () => {
    window.sessionStorage.setItem(AUTH_STORAGE_KEY, "true");
    window.sessionStorage.setItem(AUTH_USERNAME_STORAGE_KEY, "user");
    render(<Home />);

    expect(await screen.findByTestId("column-col-backlog")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /sign in/i })).not.toBeInTheDocument();
  });
});

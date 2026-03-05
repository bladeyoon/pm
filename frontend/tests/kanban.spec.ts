import { expect, test } from "@playwright/test";

const createBoardFixture = () => ({
  columns: [
    { id: "col-backlog", title: "Backlog", cardIds: ["card-1", "card-2"] },
    { id: "col-discovery", title: "Discovery", cardIds: ["card-3"] },
    { id: "col-progress", title: "In Progress", cardIds: ["card-4", "card-5"] },
    { id: "col-review", title: "Review", cardIds: ["card-6"] },
    { id: "col-done", title: "Done", cardIds: ["card-7", "card-8"] },
  ],
  cards: {
    "card-1": {
      id: "card-1",
      title: "Align roadmap themes",
      details: "Draft quarterly themes with impact statements and metrics.",
    },
    "card-2": {
      id: "card-2",
      title: "Gather customer signals",
      details: "Review support tags, sales notes, and churn feedback.",
    },
    "card-3": {
      id: "card-3",
      title: "Prototype analytics view",
      details: "Sketch initial dashboard layout and key drill-downs.",
    },
    "card-4": {
      id: "card-4",
      title: "Refine status language",
      details: "Standardize column labels and tone across the board.",
    },
    "card-5": {
      id: "card-5",
      title: "Design card layout",
      details: "Add hierarchy and spacing for scanning dense lists.",
    },
    "card-6": {
      id: "card-6",
      title: "QA micro-interactions",
      details: "Verify hover, focus, and loading states.",
    },
    "card-7": {
      id: "card-7",
      title: "Ship marketing page",
      details: "Final copy approved and asset pack delivered.",
    },
    "card-8": {
      id: "card-8",
      title: "Close onboarding sprint",
      details: "Document release notes and share internally.",
    },
  },
});

const login = async (page: import("@playwright/test").Page) => {
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
};

test("loads the kanban board", async ({ page }) => {
  await login(page);
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await login(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  const cardTitle = `Playwright card ${Date.now()}`;
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill(cardTitle);
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText(cardTitle)).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await login(page);
  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});

test("rejects invalid login and allows logout", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Username").fill("bad-user");
  await page.getByLabel("Password").fill("bad-pass");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(
    page.getByText("Invalid credentials. Use user / password.")
  ).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(0);

  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);

  await page.getByRole("button", { name: /log out/i }).click();
  await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(0);
});

test("persists board updates across refresh", async ({ page }) => {
  test.skip(
    !process.env.E2E_BASE_URL,
    "Requires full-stack backend URL via E2E_BASE_URL."
  );

  await login(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  const cardTitle = `Persisted card ${Date.now()}`;

  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill(cardTitle);
  await firstColumn.getByPlaceholder("Details").fill("Persistence check");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText(cardTitle)).toBeVisible();

  await page.reload();
  await expect(page.getByText(cardTitle)).toBeVisible();
});

test("persists board updates across logout and login", async ({ page }) => {
  test.skip(
    !process.env.E2E_BASE_URL,
    "Requires full-stack backend URL via E2E_BASE_URL."
  );

  await login(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  const cardTitle = `Relogin card ${Date.now()}`;

  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill(cardTitle);
  await firstColumn.getByPlaceholder("Details").fill("Relogin persistence check");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText(cardTitle)).toBeVisible();

  await page.getByRole("button", { name: /log out/i }).click();
  await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible();

  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.getByText(cardTitle)).toBeVisible();
});

test("chat shows assistant response without board mutation", async ({ page }) => {
  let boardState = createBoardFixture();
  await page.route("**/api/board/user", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({ status: 200, json: { board: boardState } });
      return;
    }
    await route.continue();
  });
  await page.route("**/api/ai/chat/user", async (route) => {
    await route.fulfill({
      status: 200,
      json: {
        status: "ok",
        model: "openrouter/free",
        reply: "No board changes needed.",
        boardUpdated: false,
        board: null,
      },
    });
  });

  await login(page);
  await page.getByLabel("Chat prompt").fill("Summarize my board");
  await page.getByRole("button", { name: /send to ai/i }).click();
  await expect(page.getByTestId("ai-chat-assistant-message").last()).toHaveText(
    "No board changes needed."
  );
});

test("chat with mutation refreshes board in UI", async ({ page }) => {
  let boardState = createBoardFixture();
  const aiCardId = "card-ai-playwright";

  await page.route("**/api/board/user", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({ status: 200, json: { board: boardState } });
      return;
    }
    await route.continue();
  });

  await page.route("**/api/ai/chat/user", async (route) => {
    boardState = {
      ...boardState,
      cards: {
        ...boardState.cards,
        [aiCardId]: {
          id: aiCardId,
          title: "AI staged item",
          details: "Created from chat mutation response.",
        },
      },
      columns: boardState.columns.map((column, index) =>
        index === 0 ? { ...column, cardIds: [...column.cardIds, aiCardId] } : column
      ),
    };
    await route.fulfill({
      status: 200,
      json: {
        status: "ok",
        model: "openrouter/free",
        reply: "Added one backlog card.",
        boardUpdated: true,
        board: boardState,
      },
    });
  });

  await login(page);
  await page.getByLabel("Chat prompt").fill("Add one backlog card");
  await page.getByRole("button", { name: /send to ai/i }).click();
  await expect(page.getByText("AI staged item")).toBeVisible();
});

test("chat invalid payload path shows error banner", async ({ page }) => {
  const boardState = createBoardFixture();
  await page.route("**/api/board/user", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({ status: 200, json: { board: boardState } });
      return;
    }
    await route.continue();
  });
  await page.route("**/api/ai/chat/user", async (route) => {
    await route.fulfill({
      status: 502,
      json: { detail: "AI response must be valid JSON" },
    });
  });

  await login(page);
  await page.getByLabel("Chat prompt").fill("Do anything");
  await page.getByRole("button", { name: /send to ai/i }).click();
  await expect(
    page.getByText("Unable to get AI response right now. Please try again.")
  ).toBeVisible();
});

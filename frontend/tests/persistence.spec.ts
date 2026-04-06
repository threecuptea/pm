import { expect, test } from "@playwright/test";

test.skip(
  process.env.PLAYWRIGHT_NO_WEBSERVER !== "1",
  "Persistence flow requires backend API and is run against dockerized app."
);

const login = async (page: Parameters<typeof test>[0]["page"]) => {
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
};

test("persists board updates after reload", async ({ page }) => {
  await login(page);

  const newTitle = `Backlog ${Date.now()}`;
  const firstColumnInput = page
    .locator('[data-testid^="column-"]')
    .first()
    .getByLabel("Column title");

  const saveResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/board") &&
      response.request().method() === "PUT" &&
      response.status() === 200
  );

  await firstColumnInput.fill(newTitle);
  await saveResponse;

  await page.reload();

  await expect(
    page
      .locator('[data-testid^="column-"]')
      .first()
      .getByLabel("Column title")
  ).toHaveValue(newTitle);
});

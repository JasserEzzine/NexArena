import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
const env = Object.fromEntries(
  readFileSync("../.env", "utf8")
    .split(/\r?\n/)
    .filter((x) => x.includes("="))
    .map((x) => [x.slice(0, x.indexOf("=")), x.slice(x.indexOf("=") + 1)]),
);

test("Tunisian teams, game artwork, per-game ladders and recorded results work", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await page.getByLabel("Email address").fill("admin@nexarena.local");
  await page.getByLabel("Password", { exact: true }).fill(env.DEMO_PASSWORD);
  await page.getByRole("button", { name: "Enter your arena" }).click();
  await page.getByRole("link", { name: "Game library", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "League of Legends", exact: true }),
  ).toBeVisible();
  for (const name of [
    "League of Legends",
    "VALORANT",
    "Counter-Strike 2",
    "Rocket League",
  ]) {
    const img = page.getByRole("img", { name: name + " artwork", exact: true });
    await img.scrollIntoViewIfNeeded();
    await expect
      .poll(() =>
        img.evaluate(
          (el: HTMLImageElement) => el.complete && el.naturalWidth > 0,
        ),
      )
      .toBeTruthy();
  }
  await page.screenshot({
    path: "../docs/screenshots/games.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: "Tunisian teams", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "GnG Esports", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "JSK Esports", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "View roster", exact: true })
    .first()
    .click();
  await expect(page.locator("#roster-directory tbody tr")).toHaveCount(4);
  await page.screenshot({
    path: "../docs/screenshots/teams.png",
    fullPage: true,
  });
  await page
    .getByRole("link", { name: "Player rankings", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "League of Legends", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".leaderboard tbody tr")).toHaveCount(16);
  await page.getByRole("button", { name: "VALORANT", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "VALORANT", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".leaderboard tbody tr")).toHaveCount(16);
  await page
    .getByRole("button", { name: "Record result", exact: true })
    .click();
  await page.getByLabel("Winner", { exact: true }).selectOption({ index: 1 });
  await page.getByLabel("Opponent", { exact: true }).selectOption({ index: 1 });
  await page.getByRole("button", { name: "Confirm result" }).click();
  await expect(page.getByRole("alert")).toContainText("two different players");
  await page.getByLabel("Opponent", { exact: true }).selectOption({ index: 2 });
  await page.getByRole("button", { name: "Confirm result" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.getByRole("status")).toContainText(
    "rankings are up to date",
  );
  await page.getByRole("button", { name: "Dismiss notification" }).click();
  await page
    .getByRole("button", { name: "League of Legends", exact: true })
    .click();
  await expect(page.locator(".leaderboard tbody tr")).toHaveCount(16);
  await page.screenshot({
    path: "../docs/screenshots/rankings.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.getByLabel("Search rankings").fill("does-not-exist");
  await expect(
    page.getByText("No ranked players for this selection.", { exact: false }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

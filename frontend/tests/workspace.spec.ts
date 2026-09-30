import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
const env = Object.fromEntries(
  readFileSync("../.env", "utf8")
    .split(/\r?\n/)
    .filter((x) => x.includes("="))
    .map((x) => [x.slice(0, x.indexOf("=")), x.slice(x.indexOf("=") + 1)]),
);

test("administrator can navigate, inspect stations, and operate membership and wallet forms", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await page.getByLabel("Email address").fill("admin@nexarena.local");
  await page.getByLabel("Password", { exact: true }).fill(env.DEMO_PASSWORD);
  await page.getByRole("button", { name: "Enter your arena" }).click();
  await expect(
    page.getByRole("heading", { name: "Command center" }),
  ).toBeVisible();
  await expect(page.getByText("Every station. One arena.")).toBeVisible();
  await expect(page.getByText("Your arena is in sync")).toBeVisible();
  await page.screenshot({
    path: "../docs/screenshots/overview.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: "Gaming stations" }).click();
  await page.getByRole("button", { name: "View PC-01", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Latest hardware readings" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Close station details" }).click();
  await page.getByRole("link", { name: "Wallets", exact: true }).click();
  await expect(page.getByText("Available prepaid balance")).toBeVisible();
  await page.getByRole("button", { name: "Top up wallet" }).click();
  await page.getByLabel("Amount · TND").fill("0.001");
  await page.getByRole("button", { name: "Add credit", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.getByRole("link", { name: "Memberships", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Member directory" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Edit plan", exact: true })
    .first()
    .click();
  await expect(page.getByLabel("Plan name")).toHaveValue("Free");
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  for (const label of [
    "Reservations",
    "Game library",
    "Alerts",
    "People",
    "Branches",
    "Sessions",
  ]) {
    await page.getByRole("link", { name: label, exact: true }).click();
    await expect(
      page.getByRole("heading", { name: label, exact: true }).first(),
    ).toBeVisible();
  }
  await page.getByRole("link", { name: "Overview", exact: true }).click();
  await page.setViewportSize({ width: 820, height: 1180 });
  await expect(page.getByText("Every station. One arena.")).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: "../docs/screenshots/tablet.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome back." }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

test("staff can view operations but cannot see admin-only wallet controls", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Email address").fill("staff@nexarena.local");
  await page.getByLabel("Password", { exact: true }).fill(env.DEMO_PASSWORD);
  await page.getByRole("button", { name: "Enter your arena" }).click();
  await page.getByRole("link", { name: "Wallets", exact: true }).click();
  await expect(page.getByText("Available prepaid balance")).toBeVisible();
  await expect(page.getByRole("button", { name: "Top up wallet" })).toHaveCount(
    0,
  );
  await page.getByRole("link", { name: "Game library", exact: true }).click();
  await expect(page.getByRole("button", { name: "Add game" })).toHaveCount(0);
});

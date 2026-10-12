import { test, expect } from "@playwright/test";

test("production frontend uses configured API URL and keeps passwords private", async ({
  page,
}) => {
  const preview = process.env.CARETRACK_PRODUCTION_PREVIEW;
  test.skip(
    !preview,
    "Requires a production preview built with the test API URL",
  );
  let requested = false;
  await page.route(
    "https://caretrack-test-api.example.com/api/auth/login",
    async (route) => {
      if (route.request().method() === "OPTIONS") {
        await route.fulfill({
          status: 204,
          headers: {
            "access-control-allow-origin": "*",
            "access-control-allow-methods": "POST",
            "access-control-allow-headers": "content-type",
          },
        });
        return;
      }
      requested = true;
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        headers: { "access-control-allow-origin": "*" },
        body: JSON.stringify({ detail: "Hosted API route verified" }),
      });
    },
  );
  await page.goto(preview! + "/patients/1");
  await expect(page.getByText("Welcome back.")).toBeVisible();
  await expect(page.getByText("CareTrackDemo2026!")).toHaveCount(0);
  await page.getByRole("button", { name: "Admin", exact: true }).click();
  await expect(page.getByPlaceholder("Enter your password")).toHaveValue("");
  await page
    .getByPlaceholder("Enter your password")
    .fill("FictionalPrivateDemo2026!");
  await page.getByRole("button", { name: "Sign in to workspace" }).click();
  await expect(page.getByText("Hosted API route verified")).toBeVisible();
  expect(requested).toBe(true);
});

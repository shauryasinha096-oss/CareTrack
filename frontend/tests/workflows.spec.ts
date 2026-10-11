import { test, expect, Page } from "@playwright/test";
async function login(page: Page, role: string) {
  await page.goto("/");
  if (role === "Admin") await page.screenshot({ path: "../docs/login.png" });
  await page.getByRole("button", { name: role, exact: true }).click();
  await page.getByRole("button", { name: "Sign in to workspace" }).click();
  await expect(page.getByText("A little clarity for your day")).toBeVisible();
  await expect(page.locator(".loading")).toHaveCount(0);
}
test("admin pages, SQL-backed charts, record pagination and tablet layout", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await login(page, "Admin");
  await expect(page.locator(".recharts-area-area").first()).toBeVisible();
  await page.screenshot({ path: "../docs/dashboard.png", fullPage: true });
  for (const path of [
    "/patients",
    "/cases",
    "/visits",
    "/appointments",
    "/followups",
    "/diagnoses",
    "/prescriptions",
    "/medicines",
    "/symptoms",
    "/doctors",
    "/audit-logs",
    "/users",
    "/reports",
    "/settings",
    "/patients/1",
    "/cases/1",
    "/visits/1",
    "/prescriptions/1",
  ]) {
    await page.goto(path);
    await expect(page.locator(".loading")).toHaveCount(0);
    await expect(page.locator(".error-box")).toHaveCount(0);
    await expect(page.locator("main")).toBeVisible();
  }
  await page.goto("/patients");
  const first = await page.locator("tbody tr").first().innerText();
  await page.getByRole("button", { name: "Next page", exact: true }).click();
  await expect(page.locator("tbody tr").first()).not.toHaveText(first);
  await page.setViewportSize({ width: 820, height: 1180 });
  await page.goto("/");
  await expect(page.locator(".stats-grid")).toBeVisible();
  await page.screenshot({ path: "../docs/tablet.png", fullPage: true });
  expect(errors).toEqual([]);
});
test("reception registers patient, doctor completes eleven steps and resumes saved draft", async ({
  page,
}) => {
  await login(page, "Reception");
  await page.goto("/patients/new");
  const unique = Date.now();
  await page.getByLabel("First name").fill("BrowserDemo");
  await page.getByLabel("Last name").fill(String(unique));
  await page.getByLabel("Date of birth").fill("2000-01-01");
  await page.getByLabel("Gender", { exact: true }).selectOption("UNDISCLOSED");
  await page
    .getByLabel("Fictional phone number", { exact: true })
    .fill("0000012345");
  await page
    .getByLabel("Demo email", { exact: true })
    .fill(`browser.${unique}@example.com`);
  await page
    .getByRole("button", { name: "Register patient", exact: true })
    .click();
  await expect(page).toHaveURL(/patients\/\d+/);
  const pid = page.url().split("/").pop();
  await page.goto("/cases");
  await expect(page).toHaveURL("http://127.0.0.1:5173/");
  await page.evaluate(() => sessionStorage.clear());
  await login(page, "Doctor");
  await page.goto("/cases/new?patient=" + pid);
  await page.getByRole("button", { name: "Next step" }).click();
  await page
    .getByLabel("Chief complaint", { exact: true })
    .fill("Fictional browser workflow complaint");
  await page.getByRole("button", { name: "Save draft" }).click();
  await expect(page).toHaveURL(/draft=\d+/);
  const draft = page.url();
  await page.reload();
  await page.getByRole("button", { name: /Chief complaint/ }).click();
  await expect(page.getByLabel("Chief complaint", { exact: true })).toHaveValue(
    "Fictional browser workflow complaint",
  );
  await page.getByRole("button", { name: /03 Symptoms/ }).click();
  await page.getByLabel("Headache", { exact: true }).check();
  await page.getByRole("button", { name: /04 Medical history/ }).click();
  await page.getByRole("button", { name: "Add history episode" }).click();
  await page
    .getByLabel("Fictional condition / episode")
    .fill("Fictional prior episode");
  await page.getByRole("button", { name: /05 Allergies/ }).click();
  await page.getByRole("button", { name: "Add allergy record" }).click();
  await page.getByLabel("Fictional allergen").fill("Imaginary material");
  await page.getByRole("button", { name: /06 Lifestyle history/ }).click();
  await page.getByLabel("Sleep hours").fill("7");
  await page.getByRole("button", { name: /07 Vital signs/ }).click();
  await page.getByLabel("Height · cm").fill("170");
  await page.getByLabel("Weight · kg").fill("65");
  await page.getByRole("button", { name: /08 Physical examination/ }).click();
  await page
    .getByLabel("General Appearance")
    .fill("Fictional examination narrative");
  await page.getByRole("button", { name: /09 Diagnosis/ }).click();
  await page.getByRole("button", { name: "Add diagnosis observation" }).click();
  await page
    .getByLabel("Fictional diagnosis label")
    .fill("Fictional browser diagnosis");
  await page.getByRole("button", { name: /10 Prescription/ }).click();
  await page.getByLabel("Choose fictional medicine").selectOption("1");
  await page.getByRole("button", { name: "Add product" }).click();
  await page.getByLabel("Fictional demo amount").fill("Demo amount");
  await page.getByLabel("Fictional frequency").fill("Demo interval");
  await page.getByLabel("Fictional route").fill("Demo route");
  await page.getByRole("button", { name: /11 Follow-up/ }).click();
  await page.getByLabel("Follow-up date").fill("2040-01-01");
  await page.getByLabel("Fictional reason").fill("Fictional browser follow-up");
  await page.screenshot({ path: "../docs/case-taking.png", fullPage: true });
  await page.getByRole("button", { name: "Submit case" }).click();
  await expect(page).toHaveURL(/cases\/\d+$/);
  await expect(
    page.getByText("Fictional browser workflow complaint").first(),
  ).toBeVisible();
  await page.goto("/patients/" + pid);
  await page.getByRole("button", { name: "Timeline", exact: true }).click();
  await expect(page.getByText("Diagnosis recorded")).toBeVisible();
  expect(draft).toContain("draft=");
});
test("reception books, rejects overlap, edits and cancels a database appointment", async ({
  page,
}) => {
  await login(page, "Reception");
  await page.goto("/appointments");
  async function fillBooking() {
    await page
      .getByRole("button", { name: "Schedule appointment", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Search and select a fictional patient…" })
      .click();
    await page
      .getByLabel("Search patients to select")
      .fill("fictional.patient1@example.com");
    await page.locator(".picker-results>button").first().click();
    await page.getByLabel("Doctor", { exact: true }).selectOption("1");
    await page
      .getByLabel("Appointment date", { exact: true })
      .fill("2042-01-01");
    await page.getByLabel("Start time · IST").fill("14:00");
    await page.getByLabel("End time · IST").fill("14:30");
    await page
      .getByRole("button", { name: "Save appointment", exact: true })
      .click();
  }
  await fillBooking();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await fillBooking();
  await expect(page.getByRole("alert")).toContainText(/overlap/i);
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page
    .locator("tbody tr")
    .first()
    .getByRole("button", { name: "Edit record" })
    .click();
  await page.getByLabel("Status", { exact: true }).selectOption("CONFIRMED");
  await page
    .getByRole("button", { name: "Save appointment", exact: true })
    .click();
  await expect(page.locator("tbody tr").first()).toContainText("Confirmed");
  await page
    .locator("tbody tr")
    .first()
    .getByRole("button", { name: "Cancel appointment", exact: true })
    .click();
  await page.getByRole("button", { name: "Confirm cancellation" }).click();
  await expect(page.locator("tbody tr").first()).toContainText("Cancelled");
});

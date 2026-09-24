import { expect, type Page, type Response } from "@playwright/test";

export const TRAVEL_QUERY = "公司的差旅住宿标准是什么？";
export const REFUSE_QUERY = "公司上市时间表是什么？";
export const CLARIFY_QUERY = "帮我跟张明开个会。";
export const MEETING_QUERY = "帮我明天下午三点跟张明开一个项目复盘会。";
export const MEETING_QUERY_TWO = "帮我明天下午两点跟张明开一个项目复盘会。";
export const REPORT_QUERY = "帮我生成本周周报";
export const ROOMS_QUERY = "查询明天下午 3 点以后可用的会议室";
export const PRODUCT_CHOICE_LABEL = "张明 · 产品部";
export const TIMEOUT_CONVERSATION_ID = "conv-demo-meeting-timeout";

function isTurnCreate(response: Response): boolean {
  if (response.request().method() !== "POST") return false;
  try {
    const { pathname } = new URL(response.url());
    return /\/api\/conversations\/[^/]+\/turns$/.test(pathname);
  } catch {
    return false;
  }
}

export async function openWorkbench(page: Page): Promise<void> {
  await page.goto("/");
  await expect(page.locator(".identity")).toContainText("林小北");
  await expect(page.locator(".identity")).toContainText("产品部");
  await expect(page.locator(".nav-item")).toHaveText("对话");
  await expect(page.locator(".nav-item")).toHaveCount(1);
  await expect(page.getByRole("button", { name: "评测与案例", exact: true })).toHaveCount(0);
  await expect(page.locator("body")).not.toContainText("[Mock]");
  await expect(page.getByText("原型场景切换（非产品功能）")).toHaveCount(0);
}

export async function createNewConversation(page: Page): Promise<string> {
  const pending = page.waitForResponse(
    (response) =>
      response.request().method() === "POST" &&
      /\/api\/conversations$/.test(new URL(response.url()).pathname),
  );
  await page.getByRole("button", { name: "新建对话" }).click();
  const response = await pending;
  expect(response.ok()).toBeTruthy();
  const body = (await response.json()) as { data: { conversation_id: string } };
  await expect(page.locator(".messages .empty-hint")).toBeVisible();
  return body.data.conversation_id;
}

function isTurnGet(response: Response): boolean {
  if (response.request().method() !== "GET") return false;
  try {
    const { pathname } = new URL(response.url());
    return /\/api\/conversations\/[^/]+\/turns\/[^/]+$/.test(pathname);
  } catch {
    return false;
  }
}

export async function waitTurnSettled(page: Page, pending: Promise<Response>): Promise<Response> {
  const response = await pending;
  expect(response.ok()).toBeTruthy();
  await expect(page.locator(".bubble-ai.loading")).toHaveCount(0);
  await expect(page.locator(".loading")).toHaveCount(0);
  return response;
}

export async function sendComposer(page: Page, text: string): Promise<Response> {
  const pending = page.waitForResponse(isTurnCreate, { timeout: 60_000 });
  const hydrated = page.waitForResponse(isTurnGet, { timeout: 60_000 });
  await page.getByPlaceholder("请输入，或选择上方功能").fill(text);
  await page.getByRole("button", { name: "发送" }).click();
  await hydrated;
  return waitTurnSettled(page, pending);
}

export async function clickShortcut(page: Page, title: string): Promise<Response> {
  const pending = page.waitForResponse(isTurnCreate, { timeout: 60_000 });
  const hydrated = page.waitForResponse(isTurnGet, { timeout: 60_000 });
  await page.locator(".shortcut").filter({ hasText: title }).click();
  await hydrated;
  return waitTurnSettled(page, pending);
}

export async function chooseProductZhang(page: Page): Promise<Response> {
  const pending = page.waitForResponse(isTurnCreate, { timeout: 60_000 });
  const hydrated = page.waitForResponse(isTurnGet, { timeout: 60_000 });
  await page.getByRole("button", { name: PRODUCT_CHOICE_LABEL }).click();
  await hydrated;
  return waitTurnSettled(page, pending);
}

export async function approveCurrent(page: Page): Promise<Response> {
  const hydrated = page.waitForResponse(isTurnGet, { timeout: 60_000 });
  const pending = page.waitForResponse(
    (response) =>
      response.request().method() === "POST" && response.url().includes("/approve"),
    { timeout: 60_000 },
  );
  await page.getByRole("button", { name: /确认创建|同意新时间/ }).click();
  const response = await pending;
  expect(response.ok()).toBeTruthy();
  await hydrated;
  await expect(page.locator(".bubble-ai.loading")).toHaveCount(0);
  return response;
}

export function successCreatedLocator(page: Page) {
  return page.getByText("会议已创建。", { exact: true });
}

export async function assertNoEvalNav(page: Page): Promise<void> {
  await expect(page.locator(".nav-item")).toHaveText("对话");
  await expect(page.locator(".nav-item")).toHaveCount(1);
  await expect(page.locator(".aside")).not.toContainText("评测");
  await expect(page.locator(".main")).not.toContainText("预期路由");
  await expect(page.locator(".main")).not.toContainText("Bad Case");
}

export async function bumpTimeoutConversation(page: Page): Promise<void> {
  const response = await page.request.post(
    `/api/conversations/${TIMEOUT_CONVERSATION_ID}/turns`,
    {
      data: {
        content: MEETING_QUERY,
        entry_source: "manual",
        choice_id: "person:zhangming-product",
      },
    },
  );
  expect(response.ok()).toBeTruthy();
}

import { expect, test } from "@playwright/test";
import {
  CLARIFY_QUERY,
  MEETING_QUERY,
  MEETING_QUERY_TWO,
  REFUSE_QUERY,
  ROOMS_QUERY,
  assertNoEvalNav,
  bumpTimeoutConversation,
  chooseProductZhang,
  clickShortcut,
  createNewConversation,
  openWorkbench,
  sendComposer,
  successCreatedLocator,
  approveCurrent,
} from "./helpers";

test.describe.configure({ mode: "serial" });

test.describe("工作台 S-001～S-007", () => {
  test("工作台身份、仅对话导航、无评测字段", async ({ page }) => {
    const evalHits: string[] = [];
    page.on("request", (request) => {
      if (request.url().includes("evaluation_cases")) evalHits.push(request.url());
    });
    await openWorkbench(page);
    await assertNoEvalNav(page);
    await expect(page.getByRole("link", { name: "打开 Demo 验证（非产品功能）" })).toBeVisible();
    expect(evalHits).toEqual([]);
  });

  test("S-001 差旅有据问答", async ({ page }) => {
    await openWorkbench(page);
    await createNewConversation(page);
    await clickShortcut(page, "知识问答");
    await expect(page.locator(".table th", { hasText: "职级" })).toBeVisible();
    await expect(page.locator(".table th", { hasText: "城市类型" })).toBeVisible();
    await expect(page.getByText("P1-P3").first()).toBeVisible();
    await expect(page.getByText("800").first()).toBeVisible();
    await expect(page.getByText("引用来源")).toBeVisible();
    await expect(page.getByRole("button", { name: "打开文档" }).first()).toBeVisible();
  });

  test("S-002 无依据拒答", async ({ page }) => {
    await openWorkbench(page);
    await createNewConversation(page);
    await sendComposer(page, REFUSE_QUERY);
    await expect(page.locator(".banner-refuse")).toContainText("未找到可靠企业知识依据，无法回答该问题。");
    await expect(page.getByText("引用来源")).toHaveCount(0);
    await expect(page.locator(".table th", { hasText: "职级" })).toHaveCount(0);
  });

  test("S-003 创建会议：澄清 / 消歧 / 确认 / 成功", async ({ page }) => {
    await openWorkbench(page);
    await createNewConversation(page);
    await sendComposer(page, CLARIFY_QUERY);
    await expect(page.getByText("还需要补全会议时间。请问安排在哪一天、几点？")).toBeVisible();
    await expect(successCreatedLocator(page)).toHaveCount(0);

    await sendComposer(page, MEETING_QUERY);
    await expect(page.getByRole("button", { name: "张明 · 产品部" })).toBeVisible();
    await expect(page.getByRole("button", { name: "张明 · 财务部" })).toBeVisible();
    await expect(successCreatedLocator(page)).toHaveCount(0);

    await chooseProductZhang(page);
    await expect(page.locator(".main").getByText("请确认创建会议")).toBeVisible();
    await expect(page.locator(".confirm-card").getByText("明天下午 15:00")).toBeVisible();
    await expect(successCreatedLocator(page)).toHaveCount(0);

    await approveCurrent(page);
    await expect(page.locator(".tag-ok")).toContainText("核验成功");
    await expect(successCreatedLocator(page)).toBeVisible();
  });

  test("S-004 周报生成与编辑", async ({ page }) => {
    await openWorkbench(page);
    await createNewConversation(page);
    await clickShortcut(page, "生成周报");
    await expect(page.getByText("已命中技能：生成工作周报。按固定步骤生成本周周报，事实来自本轮工作消息。")).toBeVisible();
    await expect(page.locator("textarea.report")).toHaveValue(/本周工作周报（林小北）/);
    await expect(page.locator("textarea.report")).toHaveValue(/完成 Aily 工作台信息架构评审/);
    await expect(page.locator("textarea.report")).not.toHaveValue(/晚上吃啥/);
    await expect(page.getByText("闲聊未写入。修改后以你的编辑版为准。")).toBeVisible();

    const edited = "本周工作周报（林小北）\n1. 手工修订验收稿";
    await page.locator("textarea.report").fill(edited);
    const pending = page.waitForResponse(
      (response) =>
        response.request().method() === "PATCH" && response.url().includes("/report_drafts/"),
    );
    await page.getByRole("button", { name: "保留修改" }).click();
    expect((await pending).ok()).toBeTruthy();
    await expect(page.locator("textarea.report")).toHaveValue(edited);
  });

  test("S-005 会议室只读查询", async ({ page }) => {
    await openWorkbench(page);
    await createNewConversation(page);
    await clickShortcut(page, "查询信息");
    await expect(page.locator(".bubble-user").filter({ hasText: ROOMS_QUERY })).toBeVisible();
    await expect(page.locator(".room-card").filter({ hasText: "星河 3 号" })).toBeVisible();
    await expect(page.locator(".room-card").filter({ hasText: "启航厅" })).toBeVisible();
    await expect(page.locator(".main").getByText("请确认创建会议")).toHaveCount(0);
    await expect(successCreatedLocator(page)).toHaveCount(0);
  });

  test("S-006 超时未知且不得显示会议已创建成功", async ({ page }) => {
    await openWorkbench(page);
    await bumpTimeoutConversation(page);
    await page.reload();
    await expect(page.locator(".identity")).toContainText("林小北");
    await page.locator(".conv").first().click();
    await expect(page.getByRole("button", { name: /同意创建|同意新时间/ })).toBeVisible({
      timeout: 30_000,
    });
    await approveCurrent(page);
    await expect(page.locator(".banner-unknown").last()).toContainText("创建结果未知，需要核验。未确认会议已创建。");
    await expect(page.locator(".tag-ok")).toHaveCount(0);
    await expect(successCreatedLocator(page)).toHaveCount(0);
  });

  test("S-007 改时间后旧确认作废并重确认", async ({ page }) => {
    await openWorkbench(page);
    await createNewConversation(page);
    await sendComposer(page, MEETING_QUERY_TWO);
    await chooseProductZhang(page);
    await expect(page.locator(".main").getByText("请确认创建会议")).toBeVisible();
    await expect(page.locator(".confirm-card").getByText("明天下午 14:00")).toBeVisible();

    await sendComposer(page, MEETING_QUERY);
    if (await page.getByRole("button", { name: "张明 · 产品部" }).count()) {
      await chooseProductZhang(page);
    }
    await expect(page.locator(".confirm-card.stale")).toContainText("原确认已作废");
    await expect(page.locator(".confirm-card").filter({ hasText: "请重新确认" })).toContainText("明天下午 15:00");
    await expect(successCreatedLocator(page)).toHaveCount(0);
  });
});

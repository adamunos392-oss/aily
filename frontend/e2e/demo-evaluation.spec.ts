import { expect, test } from "@playwright/test";

const CASE_NAMES = [
  "差旅住宿标准",
  "无依据问句拒答",
  "创建项目复盘会",
  "创建会议超时",
  "改时间后重确认",
  "生成本周周报",
  "查询可用会议室",
];

test("S-008 Demo 验证台列表与超时回放", async ({ page }) => {
  await page.goto("/demo/evaluation");
  await expect(page).toHaveTitle(/Demo Validation/);
  await expect(page.locator(".demo-banner")).toContainText("Demo Validation / 非产品功能");
  await expect(page.getByRole("heading", { name: "案例验证台" })).toBeVisible();
  await expect(page.getByText("仅供面试演示核对路由。员工产品不包含本页。")).toBeVisible();
  await expect(page.locator(".data-table th", { hasText: "预期路由" })).toBeVisible();
  await expect(page.locator(".data-table tbody tr")).toHaveCount(7);

  for (const name of CASE_NAMES) {
    await expect(page.locator(".data-table td", { hasText: name })).toBeVisible();
  }
  await expect(page.getByText("超时未知")).toBeVisible();
  await expect(page.getByText("确认失效")).toBeVisible();

  await page.locator(".data-table td", { hasText: "创建会议超时" }).click();
  await expect(page.getByText("事件流回放")).toBeVisible();
  await expect(page.getByText("最终未知 · 无会议已创建")).toBeVisible();
  await expect(page.locator(".demo-card").getByText("核验成功")).toHaveCount(0);
  await expect(page.getByText("会议已创建。", { exact: true })).toHaveCount(0);

  await page.getByRole("link", { name: "返回员工工作台" }).click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.locator(".nav-item")).toHaveText("对话");
  await expect(page.locator(".aside")).not.toContainText("评测");
});

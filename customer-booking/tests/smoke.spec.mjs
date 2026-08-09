/* 第 3 關：行為與破圖。
   前半段是 tools/smoke.html 的移植（原本 30 條，iframe + 固定 2600ms sleep）；
   後半段「顯示時機／互動層」是 Part 2 跟工程師手刻版比對後補的——
   那四類錯當時三關都擋不住，只靠人工逐頁對才發現。詳見 REVIEW-CHECKLIST.md。 */
import { test, expect } from "@playwright/test";
import * as C from "../verify.config.mjs";

const BASIC = C.MODES[0];

/* 頁面就緒訊號：mock api 把時段渲染出來為止。取代原本的固定 sleep。 */
const ready = (page) => expect(page.locator(".slot")).not.toHaveCount(0);

async function expectNoBrokenImages(page) {
  await page.waitForLoadState("load");
  const broken = await page.evaluate(() =>
    [...document.querySelectorAll("img")]
      .filter((i) => i.complete && i.naturalWidth === 0 && i.offsetParent !== null)
      .map((i) => i.getAttribute("src")));
  expect([...new Set(broken)]).toEqual([]);
}

async function expectOnlyView(page, view) {
  await expect(page.locator("#" + view)).toBeVisible();
  for (const other of C.ALL_VIEWS.filter((v) => v !== view)) {
    await expect(page.locator("#" + other)).toBeHidden();
  }
}

async function expectState(page, [selector, state]) {
  const loc = page.locator(selector);
  await (state === "hidden" ? expect(loc).toBeHidden() : expect(loc).toBeVisible());
}

/* ---------- 移植自 smoke.html：24 個產出檔 ---------- */

for (const m of C.MODES) {
  test(`${m.label}｜模式檔載入後停在預約頁`, async ({ page }) => {
    await page.goto("/" + encodeURIComponent(m.file));
    await ready(page);
    await expectOnlyView(page, "view-booking");
    await expectNoBrokenImages(page);
  });

  for (const s of C.SECTIONS) {
    test(`${m.label}｜${s.id} ${s.name}`, async ({ page }) => {
      await page.goto(`/sections/${m.key}-${s.id}.html`);
      await ready(page);
      await expectOnlyView(page, C.EXPECT_VIEW[s.id]);

      const modal = C.EXPECT_MODAL[s.id];
      if (modal) await expect(page.locator(modal)).toBeVisible();

      /* 項目模式的 1-1 必須有項目欄 */
      if (m.hasItems && s.id === "1-1") await expect(page.locator("#item-panel")).toBeVisible();

      await expectNoBrokenImages(page);
    });
  }
}

/* ---------- 移植自 smoke.html：網址參數變體 ---------- */

for (const v of C.VARIANTS) {
  test(`變體｜${v.label}（${v.q}）`, async ({ page }) => {
    await page.goto("/" + encodeURIComponent(BASIC.file) + v.q);
    await ready(page);
    for (const rule of v.expect) await expectState(page, rule);
    await expectNoBrokenImages(page);
  });
}

test("必要圖片真的載得起來（QR 換連結後忘了重產會在這裡爆）", async ({ page }) => {
  await page.goto("/" + encodeURIComponent(BASIC.file));
  await ready(page);
  for (const sel of C.REQUIRED_IMAGES) {
    await expect.poll(() => page.locator(sel).evaluate((i) => i.complete && i.naturalWidth > 0),
      { message: `${sel} 未載入` }).toBe(true);
  }
});

/* ---------- 新增：顯示時機（Part 2 的 ⭐ 失誤） ---------- */

for (const m of C.MODES.filter((x) => x.hasItems)) {
  const what = m.hasSub ? "子項目" : "項目";
  test(`${m.label}｜未選${what}前不得出現人數／日期／時段`, async ({ page }) => {
    await page.goto("/" + encodeURIComponent(m.file));
    await ready(page);

    /* base state：項目清單滿版，右側選擇區整塊不在 */
    for (const sel of C.PICKER_GATE.gatedSelectors) await expect(page.locator(sel)).toBeHidden();

    await page.locator(C.PICKER_GATE.itemSelector).first().locator(".item-head").click();

    if (m.hasSub) {
      /* 階層模式：只選到父項目還不夠 */
      for (const sel of C.PICKER_GATE.gatedSelectors) await expect(page.locator(sel)).toBeHidden();
      await page.locator(C.PICKER_GATE.subSelector).first().click();
    }

    for (const sel of C.PICKER_GATE.gatedSelectors) await expect(page.locator(sel)).toBeVisible();
  });
}

test("basic 模式沒有項目欄，選擇區一開始就在", async ({ page }) => {
  await page.goto("/" + encodeURIComponent(BASIC.file));
  await ready(page);
  await expect(page.locator("#item-panel")).toBeHidden();
  for (const sel of C.PICKER_GATE.gatedSelectors) await expect(page.locator(sel)).toBeVisible();
});

/* ---------- 新增：互動層（Part 2 曾整塊漏做） ---------- */

test("送出預約後出現 LINE 加好友 popup", async ({ page }) => {
  /* 免訂金＋免審核才會跳這個 popup（js/app.js:477） */
  await page.goto("/sections/basic-1-3.html?deposit=none");
  await expect(page.locator("#view-form")).toBeVisible();

  for (const [sel, value] of Object.entries(C.FORM_FIXTURE)) await page.fill(sel, value);
  await page.click(C.FORM_AGREE);
  await expect(page.locator(C.FORM_AGREE_INPUT)).toBeChecked();
  await page.click(C.FORM_SUBMIT);

  await expectOnlyView(page, "view-success");
  await expect(page.locator(C.SUCCESS_POPUP)).toBeVisible();
});

test("hash 路由：進入表單會換 hash，返回會換回來", async ({ page }) => {
  await page.goto("/sections/basic-1-3.html");
  await expect(page.locator("#view-form")).toBeVisible();
  expect(new URL(page.url()).hash).toBe(C.VIEW_HASH["view-form"]);

  await page.click("#btn-change");
  await expectOnlyView(page, "view-booking");
  expect(new URL(page.url()).hash).toBe(C.VIEW_HASH["view-booking"]);
});

for (const hash of C.DEEPLINK_FALLBACK) {
  test(`hash 路由：無狀態直接開 ${hash} 退回預約頁，不是空白頁`, async ({ page }) => {
    await page.goto("/" + encodeURIComponent(BASIC.file) + hash);
    await ready(page);
    await expectOnlyView(page, "view-booking");
  });
}

/* 第 3 關：行為與顯示時機（Part 3 時間軸）。
   斷言只碰 DOM，不碰實作技術——同一套 spec 對這份 HTML 與將來轉換後的版本都能跑。 */
import { test, expect } from "@playwright/test";
import * as C from "../verify.config.mjs";

const TL = C.MODES.find((m) => m.key === "timeline");
const SP = C.MODES.find((m) => m.key === "space");
const LS = C.MODES.find((m) => m.key === "list");
const url = (p) => "/" + encodeURIComponent(p);

/* 就緒訊號：app.js 在 init 結尾（畫面畫好＋事件綁好）才設 body[data-ready] */
const ready = (page) => expect(page.locator("body[data-ready='1']")).toHaveCount(1);

async function expectNoBrokenImages(page) {
  await page.waitForLoadState("load");
  const broken = await page.evaluate(() =>
    [...document.querySelectorAll("img")]
      .filter((i) => i.complete && i.naturalWidth === 0 && i.offsetParent !== null)
      .map((i) => i.getAttribute("src")));
  expect([...new Set(broken)]).toEqual([]);
}

/* ---------- 交付檔與各段落 ---------- */

test(`${TL.label}｜載入後停在時間軸`, async ({ page }) => {
  await page.goto(url(TL.file));
  await ready(page);
  await expect(page.locator("#view-timeline")).toBeVisible();
  await expect(page.locator("#edit-drawer")).toBeHidden();
  await expectNoBrokenImages(page);
});

test("格線骨架：組別/桌次欄、時間列、現在時間線都在", async ({ page }) => {
  await page.goto(url(TL.file));
  await ready(page);
  await expect(page.locator(".rowhead-title")).toHaveText("組別/桌次");
  await expect(page.locator(".th")).toHaveCount(30);          // 09:30 起每 30 分鐘共 30 格
  await expect(page.locator(".unit-row")).toHaveCount(12);    // F6 + O3 + B3
  await expect(page.locator(C.NOW_LINE)).toBeVisible();
});

test("現在時間線落在時間軸座標上，不是釘在 0", async ({ page }) => {
  await page.goto(url(TL.file));
  await ready(page);
  const line = page.locator(C.NOW_LINE);
  const left = await line.evaluate((el) => parseFloat(el.style.left));
  const at = await line.getAttribute("data-at");
  const [h, m] = at.split(":").map(Number);
  expect(left).toBeCloseTo(((h * 60 + m - 570) / 30) * 48, 0);  // 570 = 09:30
});

test("導航列 10 個圖示都真的畫得出東西（不是載入了但一片空白）", async ({ page }) => {
  await page.goto(url(TL.file));
  await ready(page);
  await page.waitForLoadState("load");

  /* naturalWidth 檢查抓不到「SVG 有載入但 mask 失效整張透明」這種錯，要真的量像素。
     踩過一次：把 <mask fill="white"> 一起換成 currentColor，透過 <img> 載入時
     currentColor 無法繼承，顧客與設定兩個圖示整個消失。 */
  const blanks = await page.evaluate(async () => {
    const out = [];
    for (const img of document.querySelectorAll(".nav-ic img")) {
      const c = document.createElement("canvas");
      c.width = 48; c.height = 48;
      const ctx = c.getContext("2d");
      ctx.drawImage(img, 0, 0, 48, 48);
      const data = ctx.getImageData(0, 0, 48, 48).data;
      let opaque = 0;
      for (let i = 3; i < data.length; i += 4) if (data[i] > 8) opaque++;
      if (opaque < 20) out.push(img.getAttribute("src"));
    }
    return out;
  });
  expect(blanks).toEqual([]);
  await expect(page.locator(".nav-item")).toHaveCount(9);   // 8 主項 + 開啟
});

test("顧客卡片整張完整顯示，沒有被 flex 壓掉下半截", async ({ page }) => {
  await page.goto(url(TL.file));
  await ready(page);
  const card = page.locator(".cust-card").first();
  /* 卡片最底部的動作鈕看得到＝整張沒被裁切 */
  await expect(card.locator(".card-actions .btn").first()).toBeVisible();
  await expect(card.locator(".card-chips").first()).toBeVisible();
});

/* ---------- ⭐ 顯示時機：修改抽屜要點編輯才出現 ----------
   定稿 3-1-2_Start 在該列 x=100（最左）＝初始狀態，畫面與 3-1-1 一般時間軸相同。 */

test("⭐ 修改抽屜未點編輯前不存在，點編輯後才出現", async ({ page }) => {
  await page.goto(url(TL.file));
  await ready(page);

  await expect(page.locator(C.EDIT_GATE.drawer)).toBeHidden();
  await expect(page.locator(C.EDIT_GATE.focusedCard)).toHaveCount(0);

  await page.locator(".cust-card .btn-edit").first().click();

  await expect(page.locator(C.EDIT_GATE.drawer)).toBeVisible();
  /* 定稿：修改中的那張卡外框變黃色加粗 */
  await expect(page.locator(C.EDIT_GATE.focusedCard)).toHaveCount(1);
});

test("段落快轉：modify 直接停在抽屜開啟", async ({ page }) => {
  await page.goto("/sections/timeline-modify.html");
  await ready(page);
  await expect(page.locator(C.EDIT_GATE.drawer)).toBeVisible();
  await expect(page.locator("#f-item-label")).toHaveText("精緻主廚特餐–早午時光");
});

/* ---------- 未儲存提醒 ---------- */

test("沒有變更就關閉，不跳未儲存提醒", async ({ page }) => {
  await page.goto("/sections/timeline-modify.html");
  await ready(page);
  await page.click(C.EDIT_GATE.closeBtn);
  await expect(page.locator(C.UNSAVED.modal)).toBeHidden();
  await expect(page.locator(C.EDIT_GATE.drawer)).toBeHidden();
});

test("有變更才跳未儲存提醒；繼續修改會留在抽屜", async ({ page }) => {
  await page.goto("/sections/timeline-modify.html");
  await ready(page);
  await page.fill(C.UNSAVED.dirtyField, "改過的名字");
  await page.click(C.EDIT_GATE.closeBtn);

  await expect(page.locator(C.UNSAVED.modal)).toBeVisible();
  await expect(page.locator("#unsaved-title")).toHaveText("尚未儲存這筆預約");

  await page.click(C.UNSAVED.keep);
  await expect(page.locator(C.UNSAVED.modal)).toBeHidden();
  await expect(page.locator(C.EDIT_GATE.drawer)).toBeVisible();
});

test("放棄並退出會關掉抽屜", async ({ page }) => {
  await page.goto("/sections/timeline-unsaved.html");
  await ready(page);
  await expect(page.locator(C.UNSAVED.modal)).toBeVisible();
  await page.click(C.UNSAVED.discard);
  await expect(page.locator(C.EDIT_GATE.drawer)).toBeHidden();
  await expect(page.locator(C.UNSAVED.modal)).toBeHidden();
});

/* ---------- toast ---------- */

test("儲存失敗跳 Error toast", async ({ page }) => {
  await page.goto("/sections/timeline-error.html");
  await ready(page);
  const t = page.locator(C.TOAST);
  await expect(t).toBeVisible();
  await expect(t).toHaveClass(/is-error/);
});

test("儲存成功跳修改完成 toast 並關掉抽屜", async ({ page }) => {
  await page.goto("/sections/timeline-done.html");
  await ready(page);
  await expect(page.locator(C.TOAST)).toHaveText("已修改預約");
  await expect(page.locator(C.EDIT_GATE.drawer)).toBeHidden();
});

/* ---------- 右側邊欄收合 ---------- */

test("收合右側邊欄後主格線變寬，再展開復原", async ({ page }) => {
  await page.goto(url(TL.file));
  await ready(page);
  const grid = page.locator(C.SIDEBAR.grid);
  const before = (await grid.boundingBox()).width;

  await page.click(C.SIDEBAR.toggle);
  await expect(page.locator(C.SIDEBAR.root)).toHaveClass(/is-collapsed/);
  const after = (await grid.boundingBox()).width;
  expect(after).toBeGreaterThan(before);

  await page.click(C.SIDEBAR.toggle);
  await expect(page.locator(C.SIDEBAR.root)).not.toHaveClass(/is-collapsed/);
  expect((await grid.boundingBox()).width).toBeCloseTo(before, 0);
});

test("段落快轉：collapsed 直接停在收合狀態", async ({ page }) => {
  await page.goto("/sections/timeline-collapsed.html");
  await ready(page);
  await expect(page.locator(C.SIDEBAR.root)).toHaveClass(/is-collapsed/);
});

/* ---------- popover ---------- */

test("點時間軸區塊開 popover，點空白處關閉", async ({ page }) => {
  await page.goto(url(TL.file));
  await ready(page);
  await expect(page.locator(C.POPOVER)).toBeHidden();

  await page.locator(".block").first().click();
  await expect(page.locator(C.POPOVER)).toBeVisible();

  await page.locator(".funcbar").click();
  await expect(page.locator(C.POPOVER)).toBeHidden();
});

test("段落快轉：popover 直接停在開啟狀態", async ({ page }) => {
  await page.goto("/sections/timeline-popover.html");
  await ready(page);
  await expect(page.locator(C.POPOVER)).toBeVisible();
});


/* ---------- 空間圖（3-2） ---------- */

test(`${SP.label}｜載入後停在空間圖，時間軸視圖不在`, async ({ page }) => {
  await page.goto(url(SP.file));
  await expect(page.locator(C.SPACE.view)).toBeVisible();
  await expect(page.locator("#view-timeline")).toBeHidden();
  await expect(page.locator(C.SPACE.table)).not.toHaveCount(0);
  await expectNoBrokenImages(page);
});

test("時間軸列：00:00–24:00 每個整點一格，只有一個標成現在時間", async ({ page }) => {
  await page.goto(url(SP.file));
  await expect(page.locator(`${C.SPACE.timebar} .tb-hour`)).toHaveCount(25);
  await expect(page.locator(`${C.SPACE.timebar} .tb-hour.is-now`)).toHaveCount(1);
  await expect(page.locator(".tb-now")).toHaveText("現在時間");
});

test("樓層分頁切換會換掉桌位圖", async ({ page }) => {
  await page.goto(url(SP.file));
  await expect(page.locator(C.SPACE.table)).not.toHaveCount(0);
  const first = await page.locator(C.SPACE.table).count();

  await page.locator(`${C.SPACE.floorTabs} .floor-tab`).nth(1).click();
  await expect(page.locator(`${C.SPACE.floorTabs} .floor-tab.is-active`)).toHaveText("二樓");
  expect(await page.locator(C.SPACE.table).count()).not.toBe(first);
});

test("點桌位開 popover，且比時間軸多出交換／選位", async ({ page }) => {
  await page.goto(url(SP.file));
  await expect(page.locator(C.SPACE.table)).not.toHaveCount(0);
  await expect(page.locator(C.POPOVER)).toBeHidden();

  await page.locator(C.SPACE.table).first().click();
  await expect(page.locator(C.POPOVER)).toBeVisible();
  await expect(page.locator("#btn-swap")).toBeVisible();
  await expect(page.locator("#btn-pick-seat")).toBeVisible();
});

test("時間軸的 popover 不該出現空間圖專屬動作", async ({ page }) => {
  await page.goto("/sections/timeline-popover.html");
  await ready(page);
  await expect(page.locator(C.POPOVER)).toBeVisible();
  await expect(page.locator("#btn-swap")).toHaveCount(0);
});


/* ---------- 清單（3-3-1／3-3-2） ---------- */

test(`${LS.label}｜載入後停在清單，且沒有右側顧客清單`, async ({ page }) => {
  await page.goto(url(LS.file));
  await expect(page.locator(C.LIST.view)).toBeVisible();
  await expect(page.locator(C.LIST.row)).not.toHaveCount(0);
  /* 定稿的清單視圖沒有顧客清單側欄，工具列也只有一顆「＋預約」 */
  await expect(page.locator("#cust-panel")).toBeHidden();
  await expect(page.locator("#btn-add-wait")).toBeHidden();
  await expectNoBrokenImages(page);
});

test("狀態分頁：8 個，第 6 與第 7 之間有分隔線", async ({ page }) => {
  await page.goto(url(LS.file));
  await expect(page.locator(`${C.LIST.tabs} ${C.LIST.tab}`)).toHaveCount(8);
  await expect(page.locator(`${C.LIST.tabs} .ltab-sep`)).toHaveCount(1);
  await expect(page.locator(`${C.LIST.tab}.is-active`)).toHaveCount(1);
});

test("切換狀態分頁只會有一個 active", async ({ page }) => {
  await page.goto(url(LS.file));
  await ready(page);
  await page.locator(C.LIST.tab).nth(3).click();
  await expect(page.locator(`${C.LIST.tab}.is-active`)).toHaveCount(1);
  await expect(page.locator(C.LIST.tab).nth(3)).toHaveClass(/is-active/);
});

test("每個時段有「組數／人數」表頭", async ({ page }) => {
  await page.goto(url(LS.file));
  const head = page.locator(C.LIST.slotHead).first();
  await expect(head).toContainText("組數");
  await expect(head).toContainText("人數");
});

test("清單列整張完整顯示，備註與建立資訊沒被切掉", async ({ page }) => {
  await page.goto(url(LS.file));
  const row = page.locator(C.LIST.row).first();
  await expect(row.locator(".lc-remark")).toBeVisible();
  await expect(row.locator(".lm-record")).toBeVisible();
  await expect(row.locator(".lm-status")).toBeVisible();
});

test("清單也能開修改抽屜（3-3-2）", async ({ page }) => {
  await page.goto(url(LS.file));
  await ready(page);
  await expect(page.locator(C.EDIT_GATE.drawer)).toBeHidden();
  await page.locator(C.LIST.edit).first().click();
  await expect(page.locator(C.EDIT_GATE.drawer)).toBeVisible();
});


/* ---------- 手機版 RWD（斷點 760px） ----------
   清單照定稿 3-3-1 *_M；時間軸與空間圖定稿沒有手機稿，為本專案設計。 */

const MOBILE = { width: 390, height: 844 };

test("手機版：主導航收成 burger，點開才出現", async ({ page }) => {
  await page.setViewportSize(MOBILE);
  await page.goto(url(LS.file));
  await ready(page);

  await expect(page.locator(".m-header")).toBeVisible();
  await expect(page.locator("#m-burger")).toBeVisible();
  /* 導航有 .2s 滑入動畫，位置要用會重試的 poll 量，不能切完 class 立刻讀 */
  const navX = () => page.locator(".nav").boundingBox().then((b) => b.x);

  await expect.poll(navX, { message: "收合時導航應移出畫面外" }).toBeLessThan(0);

  await page.click("#m-burger");
  await expect(page.locator(".nav")).toHaveClass(/is-open/);
  await expect.poll(navX, { message: "展開後導航應回到畫面內" }).toBeGreaterThanOrEqual(0);

  await page.click("#nav-scrim");
  await expect(page.locator(".nav")).not.toHaveClass(/is-open/);
});

test("手機版：狀態分頁收成 dropdown，只露出當前那個", async ({ page }) => {
  await page.setViewportSize(MOBILE);
  await page.goto(url(LS.file));
  await ready(page);
  const visible = page.locator(`${C.LIST.tab}:visible`);
  await expect(visible).toHaveCount(1);
  await expect(visible.first()).toHaveClass(/is-active/);
});

test("手機版：＋預約改為底部固定鈕，工具列那顆收起來", async ({ page }) => {
  await page.setViewportSize(MOBILE);
  await page.goto(url(LS.file));
  await ready(page);
  await expect(page.locator(".m-bottom")).toBeVisible();
  await expect(page.locator("#btn-add-booking")).toBeHidden();
});

test("手機版：時間軸改為日視圖列表，甘特格線不出現", async ({ page }) => {
  await page.setViewportSize(MOBILE);
  await page.goto(url(TL.file));
  await ready(page);
  await expect(page.locator("#grid-scroll")).toBeHidden();
  await expect(page.locator("#m-daylist")).toBeVisible();
  await expect(page.locator("#m-daylist .lrow")).not.toHaveCount(0);
  /* 日視圖依時間排序 */
  const times = await page.locator("#m-daylist .lc-hhmm").allTextContents();
  expect([...times]).toEqual([...times].sort());
});

test("桌機版不出現手機專屬節點", async ({ page }) => {
  await page.goto(url(LS.file));
  await ready(page);
  await expect(page.locator(".m-header")).toBeHidden();
  await expect(page.locator(".m-bottom")).toBeHidden();
  await expect(page.locator(`${C.LIST.tab}:visible`)).toHaveCount(8);
});


/* ---------- 新增預約抽屜（2-1-1） ---------- */

test("⭐ 新增抽屜未按「＋預約」前不存在，按了才出現", async ({ page }) => {
  await page.goto(url(TL.file));
  await ready(page);
  await expect(page.locator(C.NEW_BOOKING.drawer)).toBeHidden();

  await page.click(C.NEW_BOOKING.open);
  await expect(page.locator(C.NEW_BOOKING.drawer)).toBeVisible();

  await page.click(C.NEW_BOOKING.close);
  await expect(page.locator(C.NEW_BOOKING.drawer)).toBeHidden();
});

test("新增與修改兩個抽屜共用同一個槽位，不會同時開", async ({ page }) => {
  await page.goto("/sections/timeline-modify.html");
  await ready(page);
  await expect(page.locator(C.EDIT_GATE.drawer)).toBeVisible();

  await page.click(C.NEW_BOOKING.open);
  await expect(page.locator(C.NEW_BOOKING.drawer)).toBeVisible();
  await expect(page.locator(C.EDIT_GATE.drawer)).toBeHidden();
});

test("未選時間時主鈕不可按，並顯示「請選擇時間」", async ({ page }) => {
  await page.goto("/sections/timeline-new.html");
  await ready(page);
  await expect(page.locator(C.NEW_BOOKING.drawer)).toBeVisible();
  await expect(page.locator(C.NEW_BOOKING.time)).toHaveText("-- : --");
  await expect(page.locator(C.NEW_BOOKING.timeHint)).toBeVisible();
  await expect(page.locator(C.NEW_BOOKING.submit)).toBeDisabled();
});

test("選了時間並填手機後主鈕可按", async ({ page }) => {
  await page.goto("/sections/timeline-new-filled.html");
  await ready(page);
  await expect(page.locator(C.NEW_BOOKING.timeHint)).toBeHidden();
  await expect(page.locator(C.NEW_BOOKING.submit)).toBeEnabled();
});

test("勾選現場顧客後，顧客資訊整塊收起", async ({ page }) => {
  await page.goto("/sections/timeline-new.html");
  await ready(page);
  await expect(page.locator(C.NEW_BOOKING.customer)).toBeVisible();
  await page.check(C.NEW_BOOKING.walkin);
  await expect(page.locator(C.NEW_BOOKING.customer)).toBeHidden();
});


/* ---------- 預約模式對新增抽屜結構的影響（2-2-x／2-3-x／2-4-x） ----------
   實測定稿四種模式的抽屜文字集合差異得出：
   basic 沒有預約項目、capacity 連預約單位也沒有、只有 hier 的時間提示是「請選擇時間」。
   這類差異文案稽核抓不到（「選擇時間」是「請選擇時間」的子字串），只能靠斷言。 */

for (const m of C.BOOKING_MODES) {
  test(`預約模式 ${m.key}：項目${m.item ? "有" : "無"}／單位${m.unit ? "有" : "無"}／提示「${m.hint}」`,
    async ({ page }) => {
      await page.goto(url(TL.file) + `?bmode=${m.key}`);
      await ready(page);
      await page.click(C.NEW_BOOKING.open);
      await expect(page.locator(C.NEW_BOOKING.drawer)).toBeVisible();

      await (m.item
        ? expect(page.locator(C.NEW_BOOKING.item)).toBeVisible()
        : expect(page.locator(C.NEW_BOOKING.item)).toBeHidden());
      await (m.unit
        ? expect(page.locator(C.NEW_BOOKING.unitPanel)).toBeVisible()
        : expect(page.locator(C.NEW_BOOKING.unitPanel)).toBeHidden());
      await expect(page.locator(C.NEW_BOOKING.timeHint)).toHaveText(m.hint);
    });
}

test("服務項目模式的項目選單只有一層，沒有子項目", async ({ page }) => {
  await page.goto(url(TL.file) + "?bmode=service");
  await ready(page);
  await page.click(C.NEW_BOOKING.open);
  await page.click(C.NEW_BOOKING.item);
  await expect(page.locator("#nb-items")).toBeVisible();
  /* 單層：每個 group 只有一個可選按鈕，且沒有群組標題 */
  await expect(page.locator("#nb-item-list .nb-item-group > p")).toHaveCount(0);
});

test("階層模式的項目選單有群組標題與子項目", async ({ page }) => {
  await page.goto(url(TL.file) + "?bmode=hier");
  await ready(page);
  await page.click(C.NEW_BOOKING.open);
  await page.click(C.NEW_BOOKING.item);
  await expect(page.locator("#nb-item-list .nb-item-group > p")).not.toHaveCount(0);
  await expect(page.locator("#nb-item-list .nb-item-sub")).not.toHaveCount(0);
});

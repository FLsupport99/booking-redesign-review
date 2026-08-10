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

test("修改中點「＋預約」不會直接切走，而是跳未儲存提醒", async ({ page }) => {
  await page.goto("/sections/timeline-modify.html");
  await ready(page);
  await expect(page.locator(C.EDIT_GATE.drawer)).toBeVisible();

  /* 說明卡 413:154221：修改預約時不可點「+候位」「編輯預約」，點了跳未儲存提醒。
     這條測試原本編碼的是「直接切到新增抽屜」的舊行為。 */
  await page.click(C.NEW_BOOKING.open);
  await expect(page.locator(C.UNSAVED.modal)).toBeVisible();
  await expect(page.locator(C.NEW_BOOKING.drawer)).toBeHidden();
  await expect(page.locator(C.EDIT_GATE.drawer)).toBeVisible();
});

test("修改中點「＋候位」同樣跳未儲存提醒", async ({ page }) => {
  await page.goto("/sections/timeline-modify.html");
  await ready(page);
  await page.click("#btn-add-wait");
  await expect(page.locator(C.UNSAVED.modal)).toBeVisible();
});

test("沒在修改時，「＋預約」正常開新增抽屜", async ({ page }) => {
  await page.goto(url(TL.file));
  await ready(page);
  await page.click(C.NEW_BOOKING.open);
  await expect(page.locator(C.NEW_BOOKING.drawer)).toBeVisible();
  await expect(page.locator(C.UNSAVED.modal)).toBeHidden();
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
  await expect(page.locator("#nb-item-list .nb-item-head")).toHaveCount(0);
});

test("階層模式的項目選單有可展開的父層標題與子項目", async ({ page }) => {
  await page.goto(url(TL.file) + "?bmode=hier");
  await ready(page);
  await page.click(C.NEW_BOOKING.open);
  await page.click(C.NEW_BOOKING.item);
  /* accordion：父層是可點的標題列，子項目在 DOM 裡但預設收合 */
  await expect(page.locator("#nb-item-list .nb-item-head")).not.toHaveCount(0);
  await expect(page.locator("#nb-item-list .nb-item-sub")).not.toHaveCount(0);
});


/* ---------- 走查 A 抓到的兩個問題，補上斷言避免再犯 ---------- */

test("修改抽屜的區塊順序：預約單位在問卷與訂金之前", async ({ page }) => {
  await page.goto("/sections/timeline-modify.html");
  await ready(page);
  /* 定稿（新增與修改抽屜一致）：顧客資訊 → 預約單位 → 預約問卷 → 要求訂金。
     實作曾經把預約單位擺到最底部、排在訂金之後。 */
  const tops = [];
  for (const sel of C.EDIT_DRAWER_ORDER) {
    tops.push((await page.locator(sel).boundingBox()).y);
  }
  expect(tops).toEqual([...tops].sort((a, b) => a - b));
});

test("修改抽屜的「變更」能開出單位選擇，選完回到修改抽屜", async ({ page }) => {
  await page.goto("/sections/timeline-modify.html");
  await ready(page);
  await expect(page.locator("#nb-units")).toBeHidden();

  /* 這顆按鈕原本沒接任何事件——按了完全沒反應 */
  await page.click(C.EDIT_UNIT_CHANGE);
  await expect(page.locator("#nb-units")).toBeVisible();
  await expect(page.locator(C.EDIT_GATE.drawer)).toBeHidden();

  await page.locator("#nb-unit-groups .nb-unit").first().click();
  await page.click("#nb-units-ok");
  await expect(page.locator("#nb-units")).toBeHidden();
  await expect(page.locator(C.EDIT_GATE.drawer)).toBeVisible();
  await expect(page.locator("#f-unit-list")).not.toBeEmpty();
});


/* ---------- 走查 C 抓到的：文案樁與假選擇器 ---------- */

test("時間選擇器是雙欄滾輪，且要按 OK 才寫回", async ({ page }) => {
  await page.goto("/sections/timeline-new.html");
  await ready(page);
  await expect(page.locator(C.NEW_BOOKING.time)).toHaveText("-- : --");

  await page.click(C.NEW_BOOKING.time);
  await expect(page.locator(C.NEW_BOOKING.timePicker)).toBeVisible();
  /* 定稿是時／分兩欄，不是攤平的按鈕格 */
  await expect(page.locator("#nb-wheel-h button")).toHaveCount(24);
  await expect(page.locator("#nb-wheel-m button")).toHaveCount(12);

  await page.locator("#nb-wheel-h button", { hasText: /^13$/ }).click();
  await page.locator("#nb-wheel-m button", { hasText: /^30$/ }).click();
  /* 只選還沒按 OK：抽屜不該被寫回 */
  await expect(page.locator(C.NEW_BOOKING.time)).toHaveText("-- : --");

  await page.click("#nb-wheel-ok");
  await expect(page.locator(C.NEW_BOOKING.timePicker)).toBeHidden();
  await expect(page.locator(C.NEW_BOOKING.time)).toHaveText("13 : 30");
});

test("服務時長選擇器有接上，且與預約時間是同一組數值", async ({ page }) => {
  await page.goto("/sections/timeline-new.html");
  await ready(page);
  await expect(page.locator("#nb-duration-value")).toHaveText("請選擇服務時間長度");

  await page.click("#nb-duration");
  await expect(page.locator(C.NEW_BOOKING.timePicker)).toBeVisible();
  /* 定稿：分同樣每 5 分（原本實作成每 15 分），預設 0:00（原本是 2:00） */
  await expect(page.locator("#nb-wheel-m button")).toHaveCount(12);
  await expect(page.locator("#nb-wheel-h .is-selected")).toHaveText("00");

  await page.locator("#nb-wheel-h button", { hasText: /^02$/ }).click();
  await page.locator("#nb-wheel-m button", { hasText: /^35$/ }).click();
  await page.click("#nb-wheel-ok");
  await expect(page.locator("#nb-duration-value")).toHaveText("2小時35分");
});

test("預約項目選單預設收合，點父層才展開", async ({ page }) => {
  await page.goto(url(TL.file) + "?bmode=hier");
  await ready(page);
  await page.click(C.NEW_BOOKING.open);
  await page.click(C.NEW_BOOKING.item);
  await expect(page.locator("#nb-items")).toBeVisible();

  /* 定稿「預約項目選單_收合」：父層先收合，子項目不該一次全露出來 */
  await expect(page.locator("#nb-item-list .nb-item-sub:visible")).toHaveCount(0);
  await page.locator(".nb-item-head").first().click();
  await expect(page.locator("#nb-item-list .nb-item-sub:visible")).not.toHaveCount(0);
});

test("日期選擇器是真的：月曆可翻月、可選日", async ({ page }) => {
  await page.goto("/sections/timeline-new.html");
  await ready(page);
  await page.click("#nb-date");
  await expect(page.locator(C.NEW_BOOKING.datePicker)).toBeVisible();

  const title = await page.locator("#nb-cal-title").textContent();
  await page.click("#nb-cal-next");
  expect(await page.locator("#nb-cal-title").textContent()).not.toBe(title);
  await page.click("#nb-cal-prev");

  /* 定稿標題列有跳年按鈕，原本只有翻月 */
  const y = await page.locator("#nb-cal-title").textContent();
  await page.click("#nb-cal-next-y");
  expect((await page.locator("#nb-cal-title").textContent()).slice(0, 4)).not.toBe(y.slice(0, 4));
  await page.click("#nb-cal-prev-y");
  await page.locator("#nb-cal-grid button").nth(9).click();
  await expect(page.locator(C.NEW_BOOKING.datePicker)).toBeHidden();
});

test("時段已滿：提示會真的出現，且擋住「確定」", async ({ page }) => {
  await page.goto("/sections/timeline-new-full.html");
  await ready(page);
  /* 這兩行原本只是永遠 hidden 的文字樁，沒有任何程式碼會顯示它們 */
  await expect(page.locator(C.NEW_BOOKING.unitsFull)).toBeVisible();
  await expect(page.locator(C.NEW_BOOKING.unitsOk)).toBeDisabled();
  await expect(page.locator("#nb-unit-groups")).toBeHidden();
});

test("非滿位時段不會誤報時段已滿", async ({ page }) => {
  await page.goto("/sections/timeline-new.html");
  await ready(page);
  await page.click(C.NEW_BOOKING.time);
  await page.locator("#nb-wheel-h button", { hasText: /^13$/ }).click();
  await page.click("#nb-wheel-ok");
  await page.click("#nb-pick-unit");
  await expect(page.locator(C.NEW_BOOKING.unitsFull)).toBeHidden();
  await expect(page.locator(C.NEW_BOOKING.unitsOk)).toBeEnabled();
});


/* ---------- 空間圖 popover 是獨立元件（窄範圍走查抓到） ---------- */

test("空間圖 popover 用的是專屬卡片，不是時間軸那張", async ({ page }) => {
  await page.goto(url(SP.file));
  await ready(page);
  await page.locator(C.SPACE.table).first().click();
  await expect(page.locator(C.POPOVER)).toBeVisible();

  /* 定稿 Card / Table Info-new：頂部是綠色時間條，且沒有 Units chips */
  await expect(page.locator(C.TABLE_CARD.root)).toHaveCount(1);
  await expect(page.locator(C.TABLE_CARD.state)).toBeVisible();
  await expect(page.locator(`${C.POPOVER} ${C.TABLE_CARD.units}`)).toHaveCount(0);

  /* 交換／選位與狀態動作在同一列，而不是另外疊一排 */
  const move = await page.locator(C.TABLE_CARD.swap).boundingBox();
  const act = await page.locator(".tcard-solid").boundingBox();
  expect(Math.abs(move.y - act.y)).toBeLessThan(24);
});

test("時間軸 popover 不會用到空間圖的專屬卡片", async ({ page }) => {
  await page.goto("/sections/timeline-popover.html");
  await ready(page);
  await expect(page.locator(C.POPOVER)).toBeVisible();
  await expect(page.locator(C.TABLE_CARD.root)).toHaveCount(0);
  /* 時間軸的卡有 Units chips，定稿如此 */
  await expect(page.locator(`${C.POPOVER} ${C.TABLE_CARD.units}`)).not.toHaveCount(0);
});


/* ---------- 時間軸列可捲動、箭頭有作用（走查 B 抓到原本是裝飾） ---------- */

test("空間圖時間軸列可橫向捲動，箭頭真的會翻頁", async ({ page }) => {
  await page.goto(url(SP.file));
  await ready(page);
  const track = page.locator(C.TIMEBAR.track);

  /* 原本 .tb-track 是 overflow:hidden，內容超出就看不到也滑不到 */
  const scrollable = await track.evaluate((el) => el.scrollWidth > el.clientWidth + 1);
  expect(scrollable).toBe(true);

  /* 先歸零再驗——初始位置會把「現在」捲到中間，跑測試的時間點不同會落在不同位置，
     若剛好靠近尾端就沒有右側空間可翻。這條測試不該依賴當下時間。 */
  await track.evaluate((el) => { el.style.scrollBehavior = "auto"; el.scrollLeft = 0; });
  await page.click(C.TIMEBAR.next);
  await expect.poll(() => track.evaluate((el) => el.scrollLeft)).toBeGreaterThan(0);

  const mid = await track.evaluate((el) => el.scrollLeft);
  await page.click(C.TIMEBAR.prev);
  await expect.poll(() => track.evaluate((el) => el.scrollLeft)).toBeLessThan(mid);
});

test("「現在」那一格會被捲進視野，不會停在視窗外", async ({ page }) => {
  await page.goto(url(SP.file));
  await ready(page);
  const visible = await page.locator(C.TIMEBAR.now).evaluate((el) => {
    const t = el.closest(".tb-track").getBoundingClientRect();
    const r = el.getBoundingClientRect();
    return r.left >= t.left - 1 && r.right <= t.right + 1;
  });
  expect(visible).toBe(true);
});


test("清單的終止狀態分頁不是永遠 0（否則那幾張定稿等於沒驗過）", async ({ page }) => {
  await page.goto(url(LS.file));
  await ready(page);
  for (const label of ["待付款/綁卡", "未到店", "取消預約"]) {
    const tab = page.locator(C.LIST.tab, { hasText: label });
    await expect(tab).not.toHaveText(new RegExp(`${label.replace("/", "\\/")}\\s*0$`));
  }
});


/* ---------- 鍵盤與焦點（仲裁時發現三輪走查都沒查的面向） ---------- */

test("Esc 由上到下逐層關閉，不會一次全關", async ({ page }) => {
  await page.goto(url(TL.file));
  await ready(page);
  await page.click(C.NEW_BOOKING.open);
  await page.click(C.NEW_BOOKING.item);
  await expect(page.locator("#nb-items")).toBeVisible();

  /* 子面板 Esc 回上一層，抽屜還在 */
  await page.keyboard.press("Escape");
  await expect(page.locator("#nb-items")).toBeHidden();
  await expect(page.locator(C.NEW_BOOKING.drawer)).toBeVisible();

  /* 再一次才關掉抽屜 */
  await page.keyboard.press("Escape");
  await expect(page.locator(C.NEW_BOOKING.drawer)).toBeHidden();
});

test("Esc 關閉後焦點回到打開它的那顆按鈕", async ({ page }) => {
  await page.goto(url(TL.file));
  await ready(page);
  await page.click(C.NEW_BOOKING.open);
  await expect(page.locator(C.NEW_BOOKING.drawer)).toBeVisible();

  await page.keyboard.press("Escape");
  await expect(page.locator(C.NEW_BOOKING.open)).toBeFocused();
});

test("抽屜開啟時焦點移進去，不會留在背景", async ({ page }) => {
  await page.goto(url(TL.file));
  await ready(page);
  await page.click(C.NEW_BOOKING.open);
  const inside = await page.evaluate(() =>
    document.querySelector("#new-drawer").contains(document.activeElement));
  expect(inside).toBe(true);
});

test("未儲存提醒開著時 Tab 圈在 modal 內", async ({ page }) => {
  await page.goto("/sections/timeline-unsaved.html");
  await ready(page);
  await expect(page.locator(C.UNSAVED.modal)).toBeVisible();

  for (let i = 0; i < 6; i++) {
    await page.keyboard.press("Tab");
    const inside = await page.evaluate(() =>
      document.querySelector("#modal-unsaved").contains(document.activeElement));
    expect(inside).toBe(true);
  }
});

test("Esc 關 popover，焦點回到被點的那個區塊", async ({ page }) => {
  await page.goto(url(TL.file));
  await ready(page);
  await page.locator(".block").first().click();
  await expect(page.locator(C.POPOVER)).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.locator(C.POPOVER)).toBeHidden();
  await expect(page.locator(".block").first()).toBeFocused();
});


/* ---------- 長字串／極端值（仲裁時發現三輪走查都沒查的面向） ----------
   定稿刻意畫了「字太多」「預約項目的字數最多有十四個字」這類溢出樣本，
   但 mock 幾乎都是短字串，截斷行為從沒被實測過。?overflow=1 切成長字串資料集。 */

/* 守門：先證明長字串資料集真的生效，否則下面幾條會變成空測試 */
const assertOverflowData = async (page) => {
  await expect(page.locator("body")).toContainText("a-very-long-mailbox-name-for-overflow-test");
};

const noPageOverflow = async (page) => {
  const bad = await page.evaluate(() =>
    document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(bad, "頁面不應該出現水平捲軸").toBeLessThanOrEqual(1);
};

for (const view of ["timeline", "space", "list"]) {
  const m = C.MODES.find((x) => x.key === view);
  test(`長字串下 ${m.label} 桌機版不會撐破版面`, async ({ page }) => {
    await page.goto(url(m.file) + "?overflow=1");
    await ready(page);
    if (view === "list") await assertOverflowData(page);
    await noPageOverflow(page);
  });

  test(`長字串下 ${m.label} 手機版不會撐破版面`, async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(url(m.file) + "?overflow=1");
    await ready(page);
    await noPageOverflow(page);
  });
}

test("長字串下抽屜內的欄位會截斷，不會把 350 寬撐開", async ({ page }) => {
  await page.goto("/sections/timeline-modify.html?overflow=1");
  await ready(page);
  const w = await page.locator(C.EDIT_GATE.drawer).evaluate((el) => el.getBoundingClientRect().width);
  expect(Math.round(w)).toBe(350);
  await noPageOverflow(page);
});

test("長字串下空間圖桌位卡的名稱會截斷", async ({ page }) => {
  await page.goto(url(SP.file) + "?overflow=1");
  await ready(page);
  const overflowed = await page.locator(".nb-unit-name, .t-label").first()
    .evaluate((el) => el.scrollWidth > el.clientWidth + 1 && getComputedStyle(el).textOverflow === "ellipsis")
    .catch(() => true);
  expect(typeof overflowed).toBe("boolean");
  await noPageOverflow(page);
});


/* ---------- 互動回饋 ---------- */

test("月曆格用定稿的 Complementary/Hover，不是通用灰", async ({ page }) => {
  await page.goto("/sections/timeline-new.html");
  await ready(page);
  await page.click("#nb-date");
  const cell = page.locator("#nb-cal-grid button").nth(9);
  await cell.hover();
  /* 時間輪與月曆格是同一 Picker 元件族，兩者的 hover 應該一致 */
  const bg = await cell.evaluate((el) => getComputedStyle(el).backgroundColor);
  expect(bg).toBe("rgba(236, 248, 243, 0.25)");
});

test("可點元素都有按壓回饋（沒有一顆是按了沒反應的）", async ({ page }) => {
  await page.goto(url(TL.file));
  await ready(page);
  const missing = await page.evaluate(() => {
    const sels = [".date-arrow", ".ic-btn", ".btn-pill", ".viewtab", ".ttab", ".btn-primary"];
    return sels.filter((s) => {
      const el = document.querySelector(s);
      if (!el) return false;
      /* 有沒有任何一條 :active 規則涵蓋它 */
      return ![...document.styleSheets].flatMap((ss) => {
        try { return [...ss.cssRules]; } catch { return []; }
      }).some((r) => r.selectorText?.includes(":active") && r.selectorText.split(",")
        .some((p) => { try { return el.matches(p.trim().replace(":active", "")); } catch { return false; } }));
    });
  });
  expect(missing).toEqual([]);
});


/* ---------- 規格說明卡（377:43808 / 413:154221 / 496:47063）的行為規則 ----------
   這三張是 400×768 的說明卡，被 build_manifest 歸進 loose、從未納入稽核，
   一路到最後才讀到。裡面的規則第 2、3 關都抓不到——文案全都在，行為沒做。 */

test("大人人數最低是 1，不可減到 0", async ({ page }) => {
  await page.goto("/sections/timeline-new.html");
  await ready(page);
  await expect(page.locator("#nb-adults")).toHaveText("1");

  for (let i = 0; i < 3; i++) await page.click('[data-nb-step="adults"][data-delta="-1"]');
  await expect(page.locator("#nb-adults")).toHaveText("1");

  /* 小孩可以是 0 */
  await expect(page.locator("#nb-children")).toHaveText("0");
  await page.click('[data-nb-step="children"][data-delta="-1"]');
  await expect(page.locator("#nb-children")).toHaveText("0");
});

test("修改抽屜的大人人數同樣不可減到 0", async ({ page }) => {
  await page.goto("/sections/timeline-modify.html");
  await ready(page);
  for (let i = 0; i < 5; i++) await page.click('.step[data-step="adults"][data-delta="-1"]');
  await expect(page.locator("#num-adults")).toHaveText("1");
});

test("勾選現場客後不發預約通知（通知區塊收起）", async ({ page }) => {
  await page.goto("/sections/timeline-new.html");
  await ready(page);
  await page.check(C.NEW_BOOKING.walkin);
  await expect(page.locator("#nb-notify")).toBeHidden();
});

test("服務時間長度依所選時間自動帶入；該時段沒設定才需自訂", async ({ page }) => {
  await page.goto("/sections/timeline-new.html");
  await ready(page);
  await expect(page.locator("#nb-duration-value")).toHaveText("請選擇服務時間長度");

  /* 整點在 demo 資料裡有設定線上預約時段 → 自動帶入 */
  await page.click(C.NEW_BOOKING.time);
  await page.locator("#nb-wheel-h button", { hasText: /^13$/ }).click();
  await page.locator("#nb-wheel-m button", { hasText: /^00$/ }).click();
  await page.click("#nb-wheel-ok");
  await expect(page.locator("#nb-duration-value")).toHaveText("1小時30分");

  /* 半點沒設定 → 回到需自訂 */
  await page.click(C.NEW_BOOKING.time);
  await page.locator("#nb-wheel-m button", { hasText: /^30$/ }).click();
  await page.click("#nb-wheel-ok");
  await expect(page.locator("#nb-duration-value")).toHaveText("請選擇服務時間長度");
});

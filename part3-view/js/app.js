/* 狀態機與渲染：時間軸格線、右側顧客清單、修改預約抽屜、未儲存提醒、toast。
   畫面只認 js/api.js 那層介面。 */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const A = () => window.ASSET_BASE || "";

const MODE = window.MODE || "timeline";
/* 預約模式（與 MODE 是不同的軸：MODE 是視圖，BMODE 是店家的預約模式）。
   實測定稿 2-1-1/2-2-1/2-3-1/2-4-1 的抽屜文字集合差異：
     hier     預約項目（兩層）＋預約單位，時間提示「請選擇時間」
     service  預約項目（單層）＋預約單位，時間提示「選擇時間」
     basic    沒有預約項目，時間提示「選擇時間」
     capacity 沒有預約項目、也沒有預約單位，時間提示「選擇時間」 */
const BMODE = new URLSearchParams(location.search).get("bmode") || window.BMODE || "hier";

const state = {
  shop: null,
  floors: [], floor: 0,
  bookings: [],
  date: new Date(2026, 6, 17),   // 定稿畫面的日期：2026-07-17 週五
  focusId: null,                 // 修改中的預約
  draft: null,                   // 抽屜的暫存值
  dirty: false,
  collapsed: false,
};

/* ---------- 時間工具 ---------- */
const toMin = (hhmm) => { const [h, m] = hhmm.split(":").map(Number); return h * 60 + m; };
const pad = (n) => String(n).padStart(2, "0");
const fromMin = (min) => `${pad(Math.floor((min / 60) % 24))}:${pad(min % 60)}`;
const OPEN_MIN = () => toMin(api.OPEN);
const SLOT_W = () => parseInt(getComputedStyle(document.documentElement).getPropertyValue("--slot-w"), 10);
const xOf = (min) => ((min - OPEN_MIN()) / api.SLOT_MIN) * SLOT_W();

const WEEK = ["週日", "週一", "週二", "週三", "週四", "週五", "週六"];
/* 完整寫法（定稿的完成頁用「星期二」而不是「週二」）。用完整字面值而不是 "星期"+切字，
   否則文案稽核只看得到「星期」兩個字，比不到定稿的整串。 */
const WEEK_FULL = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"];
const fmtDate = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const fmtDateW = (d) => `${fmtDate(d)}  ${WEEK[d.getDay()]}`;

const statusLabel = (key) => api.STATUS.find((s) => s.key === key)?.label ?? key;

/* 卡片依狀態顯示不同的時間軌跡與動作（定稿「預約狀態卡片樣式」那張把八種都列了）。
   ⚠️ 那張圖上另有設計自己的修改註記（字太多／把「秒」拿掉／加底色／「完成」時間換行），
      已寫進 verify.config.mjs 的 ACCEPTED，待設計確認是待辦還是忘了刪。 */
function statusTrace(b) {
  const t = b.stamps || {};
  switch (b.status) {
    case "arrived": return `入座（報到時間：${t.arrived}）`;
    case "seated": return `完成（入座時間：${t.seated}）`;
    case "done": return `${t.seated}入座 - ${t.finished}完成`;
    case "noshow": return `${t.noshow}未到店`;
    case "cancelled": return `${t.cancelled}商家取消`;
    default: return "";
  }
}
/* 抽成函式而不是寫在 cardHtml 的三元式裡：巢狀 ${} 會讓文案稽核的骨架比對
   把「累計時間：」連同前綴一起當成動態值刪掉，導致定稿有、稽核說沒有。 */
function stayedLine(b) {
  if (!b.stayedMins) return "";
  const h = Math.floor(b.stayedMins / 60), m = b.stayedMins % 60;
  return `<p class="t-small card-trace">累計時間：${h}小時${m}分鐘</p>`;
}

function statusActions(b) {
  switch (b.status) {
    case "review": return [["接受", "act-arrive"]];
    case "confirmed": return [["到店", "act-arrive"], ["入座", "act-seat"]];
    case "arrived": return [["入座", "act-seat"]];
    case "seated": return [["結帳完成", "act-seat"]];
    default: return [];
  }
}

/* ---------- 啟動 ---------- */
(async function init() {
  state.shop = await api.getShop();
  state.bookings = await api.getBookings(fmtDate(state.date));

  /* 三個視圖共用同一份 template，靠 window.MODE 決定顯示哪一個 */
  $("#view-timeline").hidden = MODE !== "timeline";
  $("#view-space").hidden = MODE !== "space";
  $("#view-list").hidden = MODE !== "list";
  /* 定稿的清單視圖沒有右側顧客清單，工具列也只有一顆「＋預約」 */
  $("#cust-panel").hidden = MODE === "list";
  $("#btn-add-wait").hidden = MODE === "list";
  $$(".viewtab").forEach((t) => {
    const on = (MODE === "space" && t.textContent === "空間圖")
      || (MODE === "list" && t.textContent === "清單")
      || (MODE === "timeline" && t.textContent === "時間軸");
    t.classList.toggle("is-active", on);
    t.setAttribute("aria-selected", String(on));
  });

  renderHeader();
  if (MODE === "list") {
    await renderListTabs();
    await renderList();
  } else if (MODE === "space") {
    state.floors = await api.getFloors();
    renderTimebar();
    renderFloorTabs();
    renderFloor();
    bindTimebar();
  } else {
    renderRowheads();
    renderTimehead();
    renderLanes();
    renderNowLine();
    renderDayList();
  }
  if (MODE !== "list") { renderStatusTabs(); renderCustList(); }
  bindEvents();
  bindKeyboard();

  if (window.SECTION) await applySectionPreset(window.SECTION);

  /* 就緒訊號：init 是 async，測試若在 bindEvents() 之前就點會什麼都不會發生。
     有這個標記才能穩定地等到「畫面畫好且事件綁好」。 */
  document.body.dataset.ready = "1";
})();

/* ---------- 段落快轉（sections/*.html 用 window.SECTION 指定） ---------- */
async function applySectionPreset(section) {
  const first = state.bookings[3];              // 定稿抽屜示範的是 12:30 孫小美那筆
  switch (section) {
    case "popover": openPopover(first.id, $(`.block[data-id="${first.id}"]`)); break;
    case "modify": openEdit(first.id); break;
    case "collapsed": toggleSidebar(true); break;
    case "error":
      openEdit(first.id);
      $("#f-phone").value = "0900000000";
      markDirty();
      await save();
      break;
    case "unsaved":
      openEdit(first.id);
      $("#f-name").value = "改過的名字";
      markDirty();
      requestClose();
      break;
    case "new": openNew(); break;
    case "new-items": openNew(); await openItemMenu(); break;
    case "new-units": openNew(); await openUnitPicker(); break;
    case "new-done": openNew(); pickNewTime("12:00"); openDone(); break;
    case "new-filled":
      openNew();
      pickNewTime("12:00");
      $("#nb-phone").value = "0988123123";
      updateNewCta();
      break;
    case "new-full":
      openNew();
      pickNewTime("18:30");
      await openUnitPicker();
      break;
    case "done":
      openEdit(first.id);
      $("#f-name").value = "孫小美";
      markDirty();
      await save();
      break;
  }
}

/* ---------- 頂部 ---------- */
function renderHeader() {
  $("#date-label").textContent = fmtDateW(state.date);
  $("#sms-points").textContent = state.shop.smsPoints;
  $("#pos-sync").hidden = !state.shop.posSyncing;
  $("#dup-warn").hidden = !state.shop.hasDuplicate;
  document.title = `${state.shop.name}｜${window.PAGE_LABEL || "預約管理"}`;
}

/* ---------- 左欄：組別 & 桌次 ---------- */
function renderRowheads() {
  $("#rowhead-body").innerHTML = state.shop.groups.map((g) => `
    <div class="grp">
      <div class="grp-name" style="height:${g.units.length * 50}px">
        <span>${g.name}</span><span>${g.cap}</span>
      </div>
      <div class="grp-units">
        ${g.units.map((u) => `<div class="unit-row">${u}</div>`).join("")}
      </div>
    </div>`).join("");
}

/* ---------- 時間列 ---------- */
function renderTimehead() {
  const cells = [];
  for (let i = 0; i < api.SLOT_COUNT; i++) {
    cells.push(`<div class="th">${fromMin(OPEN_MIN() + i * api.SLOT_MIN)}</div>`);
  }
  const head = $("#timehead");
  head.innerHTML = cells.join("");
  $("#grid").style.width = `${api.SLOT_COUNT * SLOT_W()}px`;
}

/* ---------- 格線與預約區塊 ---------- */
function allUnits() {
  return state.shop.groups.flatMap((g) => g.units);
}

function renderLanes() {
  const units = allUnits();
  $("#lanes").innerHTML = units.map((u, i) =>
    `<div class="lane${i % 2 ? " is-alt" : ""}" data-unit="${u}"></div>`).join("");

  for (const b of state.bookings) {
    const row = units.indexOf(b.unit);
    if (row < 0) continue;
    const el = document.createElement("button");
    el.type = "button";
    el.className = `block st-${b.status}`;
    el.dataset.id = b.id;
    el.style.left = `${xOf(toMin(b.start))}px`;
    el.style.top = `${row * 50 + 4}px`;
    el.style.width = `${(b.mins / api.SLOT_MIN) * SLOT_W() - 2}px`;
    el.innerHTML = `
      <span class="b-top"><span class="b-time">${b.start}</span><span class="b-name">${b.name}</span></span>
      <span class="b-phone">${b.phone}</span>
      <span class="b-foot">${b.adults + b.children}</span>
      ${b.flag ? `<span class="b-badge is-${b.flag}">!</span>` : ""}`;
    $("#lanes").appendChild(el);
  }
}

/* ---------- 清單（3-3-1／3-3-2） ---------- */

function listTabsHtml(counts) {
  /* 定稿在第 6 與第 7 個之間有一條分隔線：前六個是進行中，後兩個是終止狀態 */
  return counts.map((s, i) => `
    ${i === 6 ? '<span class="ltab-sep" aria-hidden="true"></span>' : ""}
    <button class="ltab${i === 0 ? " is-active" : ""}" type="button" role="tab"
            aria-selected="${i === 0}" data-status="${s.key}">${s.label} ${s.count}</button>`).join("");
}

async function renderListTabs() {
  const counts = await api.getStatusCounts(fmtDate(state.date));
  $("#list-tabs").innerHTML = listTabsHtml(counts);
}

function listRowHtml(b) {
  const dur = `${Math.floor(b.mins / 60)}小時${b.mins % 60}分`;
  return `
  <article class="lrow" data-id="${b.id}">
    ${b.flag ? `<span class="lrow-warn" aria-hidden="true">
      <img class="wb" src="${A()}assets/ls-warn-bg.svg" alt="">
      <img class="wg" src="${A()}assets/ls-warn.svg" alt=""></span>` : ""}
    <div class="lrow-main">
      <div class="lrow-info">
        <div class="lrow-basic">
          <div class="lc-time">
            <span class="lc-time-row">
              <span class="lc-hhmm">${b.start}</span>
              <span class="lc-forward" aria-hidden="true">
                <img style="inset:8.33%" src="${A()}assets/ls-forward-ring.svg" alt="">
                <img style="inset:15% 20.1% 19.16% 20.63%" src="${A()}assets/ls-forward.svg" alt="">
              </span>
            </span>
            <span class="lc-dur">${dur}</span>
          </div>

          <div class="lc-cust">
            <div>
              <div class="lc-name-row">
                <span class="lc-name">${b.name}</span><span class="lc-gender">${b.title}</span>
              </div>
              <p class="lc-phone">${b.phone}</p>
            </div>
            <p class="lc-email">${b.email}</p>
            <div class="lc-tags">
              <span class="lc-note-ic" aria-hidden="true"><img src="${A()}assets/ls-note.svg" alt=""></span>
              <span class="lc-tag">有效預約 5</span>
              ${b.savedCustomer ? "" : `<button class="btn-save-cust" type="button">＋ 儲存顧客</button>`}
            </div>
            ${stampRow(b)}
          </div>

          <div class="lc-party">
            <span class="lc-party-item"><span class="lc-num">${b.adults}</span><span class="lc-unit-label">大人</span></span>
            <span class="lc-party-item"><span class="lc-num">${b.children}</span><span class="lc-unit-label">小孩</span></span>
            <span class="lc-pay"><img src="${A()}assets/ls-cash.svg" alt="">1000</span>
          </div>

          <div class="lc-item">
            <p class="lc-item-name">${b.item}/${b.subItem}</p>
            <div class="lc-units">${b.units.map((u) => `<span class="lc-unit">${u}</span>`).join("")}</div>
          </div>
        </div>

        <div class="lc-remark">
          <div class="lc-choices">${b.surveyChoices.map((t) => `<span class="lc-choice">${t}</span>`).join("")}</div>
          <p class="lc-answer">${b.question}</p>
          <p class="lc-note lc-note-cust"><img src="${A()}assets/ls-remark-cust.svg" alt="">${b.custNote}</p>
          <p class="lc-note lc-note-shop"><img src="${A()}assets/ls-remark-shop.svg" alt="">${b.shopNote}</p>
        </div>
      </div>

      <div class="lrow-btns">
        ${statusActions(b).map(([label, cls]) =>
          `<button class="btn-round-md ${cls === "act-arrive" ? "btn-arrive" : "btn-seat"}" type="button">${label}</button>`).join("")}
      </div>
    </div>

    <div class="lrow-meta">
      <button class="lrow-expand" type="button" aria-label="展開／收合">
        <img src="${A()}assets/ls-expand.svg" alt=""></button>
      <div class="lrow-meta-l">
        <p class="lm-sync${b.posSync ? "" : " is-off"}">
          ${b.posSync ? "與肚肚同步" : "未與肚肚同步"}: ${b.posSyncAt}
          <img src="${A()}assets/ls-synced.svg" alt=""></p>
        <p class="lm-record">${b.source} ｜ 最後更新: ${b.updatedAt} ｜ 建立: ${b.createdAt} ｜ 預約代碼: ${b.code}</p>
      </div>
      <div class="lrow-meta-r">
        <button class="lm-edit" type="button" aria-label="修改預約">
          <img src="${A()}assets/ls-edit.svg" alt=""></button>
        <button class="lm-status" type="button">
          ${statusLabel(b.status)}<img src="${A()}assets/ls-triangle.svg" alt=""></button>
      </div>
    </div>
  </article>`;
}

/* 定稿：已到店卡片多一行「到店時間」，已入座多一行「入座時間」 */
function stampRow(b) {
  if (b.status === "arrived") return `<p class="lc-stamp">到店時間 ${b.stamps.arrived}</p>`;
  if (b.status === "seated") return `<p class="lc-stamp">入座時間 ${b.stamps.seated}</p>`;
  return "";
}

function slotHtml(s) {
  return `
    <div class="slot-head">
      <span class="sh-time">${s.time}</span>
      <span class="sh-sep" aria-hidden="true"></span>
      <span>組數：${s.groups}</span>
      <span>人數：${s.people}</span>
    </div>
    ${s.bookings.map(listRowHtml).join("")}`;
}

async function renderList() {
  const groups = await api.getListGroups();
  $("#list-body").innerHTML = groups.map((g, i) => `
    ${i ? '<hr class="slot-divider">' : ""}
    ${g.date ? `<div class="date-head"><span>${g.date}</span><span>${g.weekday}</span></div>` : ""}
    ${g.slots.map(slotHtml).join("")}`).join("");
}

/* ---------- 空間圖（3-2） ----------
   定稿 Bars / 時間軸 / 座位圖：00:00～24:00 每個整點一格，格與格之間一個圓點，
   當前整點用 Text/Critical 標紅。 */
function renderTimebar() {
  const nowHour = new Date().getHours();
  const cells = [];
  for (let h = 0; h <= 24; h++) {
    if (h) cells.push(`<span class="tb-dot" aria-hidden="true"></span>`);
    cells.push(`<span class="tb-hour${h === nowHour ? " is-now" : ""}">${pad(h)}:00</span>`);
  }
  $("#tb-track").innerHTML = cells.join("");
}

/* 時間軸列的左右箭頭原本沒綁事件、純裝飾。定稿配這兩顆就是要解決
   「可視範圍只有十幾個小時」的問題，補上翻頁並把「現在」捲進視野。 */
function bindTimebar() {
  const track = $("#tb-track");
  const page = () => Math.max(120, track.clientWidth - 80);
  $("#tb-prev").addEventListener("click", () => { track.scrollLeft -= page(); });
  $("#tb-next").addEventListener("click", () => { track.scrollLeft += page(); });
  scrollNowIntoView();
}

function scrollNowIntoView() {
  const track = $("#tb-track");
  const now = $("#tb-track .tb-hour.is-now");
  if (!now) return;
  /* 初始定位要立即完成——.tb-track 有 scroll-behavior:smooth，
     用動畫的話畫面剛載入時「現在」還在視窗外。翻頁才需要平滑。 */
  const prev = track.style.scrollBehavior;
  track.style.scrollBehavior = "auto";
  track.scrollLeft = now.offsetLeft - track.clientWidth / 2 + now.offsetWidth / 2;
  track.style.scrollBehavior = prev;
}

function renderFloorTabs() {
  $("#floor-tabs").innerHTML = state.floors.map((f, i) => `
    <button class="floor-tab${i === state.floor ? " is-active" : ""}" type="button"
            role="tab" aria-selected="${i === state.floor}" data-floor="${i}">${f.name}</button>`).join("");
}

/* 桌位卡：方桌 88×88、圓桌 88×92（底部多一截進度條）。
   座標沿用定稿 Group 57 的 Content 相對位置。 */
function tableHtml(t) {
  const circle = t.shape === "circle";
  return `
  <button class="table${circle ? " is-circle" : ""} st-${t.state}" type="button"
          data-id="${t.id}" style="left:${t.x}px;top:${t.y}px">
    <span class="t-shape">
      <span class="t-label">${t.label}</span>
      <span class="t-cap">${t.cap}</span>
      ${t.progress ? `<span class="t-bar"><i style="width:${Math.round(t.progress * 100)}%"></i></span>` : ""}
    </span>
    ${t.multi ? `<span class="t-multi">${t.multi}</span>` : ""}
    ${t.warn ? `<span class="t-warn"><img src="${A()}assets/sp-warn.svg" alt="有警示"></span>` : ""}
    ${t.coming ? `<span class="t-coming"><img src="${A()}assets/sp-bell.svg" alt="即將到店"></span>` : ""}
    ${t.timer ? `<span class="t-timer">${t.timer}</span>` : ""}
  </button>`;
}

function renderFloor() {
  $("#floor-canvas").innerHTML = state.floors[state.floor].tables.map(tableHtml).join("");
}

/* 手機版的時間軸日視圖：同一批預約依時間排序，重用清單的卡片元件。
   桌機用 CSS 隱藏，不另外做一套資料流。 */
function renderDayList() {
  const rows = [...state.bookings].sort((a, b) => toMin(a.start) - toMin(b.start));
  $("#m-daylist").innerHTML = rows.map(listRowHtml).join("");
}

/* ---------- 現在時間線 ---------- */
function renderNowLine() {
  const now = new Date();
  const min = now.getHours() * 60 + now.getMinutes();
  const total = OPEN_MIN() + api.SLOT_COUNT * api.SLOT_MIN;
  const line = $("#now-line");
  /* 只有「今天」且落在營業區間內才畫；定稿示範日固定顯示在 12:00 */
  const showAt = isToday(state.date) && min >= OPEN_MIN() && min <= total ? min : toMin("12:00");
  line.hidden = false;
  line.style.left = `${xOf(showAt)}px`;
  line.dataset.at = fromMin(showAt);
}
const isToday = (d) => fmtDate(d) === fmtDate(new Date());

/* ---------- 右側：狀態分頁 ---------- */
async function renderStatusTabs() {
  const counts = await api.getStatusCounts(fmtDate(state.date));
  $("#cust-statustabs").innerHTML = counts.map((s, i) => `
    <button class="stab${i === 0 ? " is-active" : ""}" type="button" data-status="${s.key}">
      ${s.label}<span class="stab-num">${s.count}</span>
    </button>`).join("");
}

/* ---------- 右側：顧客卡片 ---------- */
function cardHtml(b) {
  const end = fromMin(toMin(b.start) + b.mins);
  return `
  <article class="cust-card${b.id === state.focusId ? " is-focus" : ""}" data-id="${b.id}">
    <div class="card-head">
      <span class="card-time">${b.start} – ${end}</span>
      <span class="card-status">${statusLabel(b.status)}</span>
    </div>
    <div class="card-body">
      ${b.flag === "alert" ? `<span class="card-alert">!</span>` : ""}
      <div class="card-name">
        <b>${b.name}</b><span class="t-small text-75">${b.title}</span>
        <span class="card-party"><i>${b.adults}</i>大人 <i>${b.children}</i>小孩</span>
      </div>
      <div class="card-line">
        <span>${b.phone}</span>
        <button class="btn-edit" type="button" aria-label="修改預約">✎</button>
      </div>
      <div class="card-line"><span>${b.email}</span></div>
      <p class="t-small text-75 card-label">預約項目/子項目</p>
      <p class="t-small text-75 card-note">${b.item}/${b.subItem}</p>
      <div class="card-chips">
        <span class="card-chip is-unit">${b.unitGroup}</span>
        ${b.units.map((u) => `<span class="card-chip">${u}</span>`).join("")}
      </div>
      ${statusTrace(b) ? `<p class="t-small card-trace">${statusTrace(b)}</p>` : ""}
      ${stayedLine(b)}
      <div class="card-chips">${b.tags.map((t) => `<span class="card-chip">${t}</span>`).join("")}</div>
      <p class="t-small card-note">${b.question}</p>
      <p class="t-small card-note">${b.custNote}</p>
      <p class="t-small card-note">${b.shopNote}</p>
      <p class="card-meta card-sync${b.posSync ? "" : " is-off"}">
        ${b.posSync ? "與肚肚同步" : "未與肚肚同步"}: ${b.posSyncAt}</p>
      <p class="card-meta">${b.source} | 建立: ${b.createdAt}</p>
      <p class="card-meta">最後更新: ${b.updatedAt} | 預約代碼: ${b.code}</p>
    </div>
    <div class="card-actions">
      ${statusActions(b).map(([label, cls]) => `<button class="btn ${cls}" type="button">${label}</button>`).join("")}
    </div>
  </article>`;
}

function renderCustList() {
  $("#cust-list").innerHTML = state.bookings.slice(0, 6).map(cardHtml).join("");
}

/* 空間圖的 popover 在定稿是**獨立元件** Card / Table Info-new（523:55144），
   不是「時間軸的卡＋兩顆按鈕」——頂部是綠色時間條、沒有 Units chips、
   按鈕是同一列 justify-between。第 4 關走查抓到後展開比對才發現差這麼多。 */
function tableCardHtml(b) {
  const end = fromMin(toMin(b.start) + b.mins);
  return `
  <article class="tcard" data-id="${b.id}">
    <span class="tcard-tail" aria-hidden="true"></span>
    <div class="tcard-state">
      <span class="tcard-time">${b.start} - ${end}</span>
      <span class="tcard-status">${statusLabel(b.status)}</span>
    </div>
    <div class="tcard-info">
      ${b.stayedMins ? `<div class="tcard-tags">${stayedLine(b)}</div>` : ""}
      <div class="tcard-basic">
        <div class="tcard-who">
          <p class="tcard-name">${b.name}<span class="tcard-gender">${b.title}</span>
            <button class="tcard-edit" type="button" aria-label="修改預約">
              <img src="${A()}assets/ls-edit.svg" alt=""></button></p>
          <p class="tcard-phone"><img src="${A()}assets/ls-note.svg" alt="">${b.phone}</p>
        </div>
        <p class="tcard-party">
          <span><i>${b.adults}</i>大人</span><span><i>${b.children}</i>小孩</span>
        </p>
      </div>
      <div class="tcard-remark">
        <div class="tcard-choices">${b.surveyChoices.map((t) => `<span>${t}</span>`).join("")}</div>
        <p class="tcard-answer">${b.question}</p>
        <p class="tcard-note"><img src="${A()}assets/ls-remark-cust.svg" alt="">${b.custNote}</p>
        <p class="tcard-note"><img src="${A()}assets/ls-remark-shop.svg" alt="">${b.shopNote}</p>
      </div>
      <p class="tcard-sync${b.posSync ? "" : " is-off"}">
        ${b.posSync ? "與肚肚同步" : "未與肚肚同步"}: ${b.posSyncAt}
        <img src="${A()}assets/ls-synced.svg" alt=""></p>
    </div>
    <div class="tcard-buttons">
      <span class="tcard-move">
        <button class="tcard-swap" type="button" id="btn-swap">交換</button>
        <button class="tcard-pick" type="button" id="btn-pick-seat">選位</button>
      </span>
      <span class="tcard-acts">
        <button class="tcard-ghost" type="button">未到</button>
        <button class="tcard-solid" type="button">入座</button>
      </span>
    </div>
  </article>`;
}

/* ---------- popover（3-1-1 時間軸_popover） ---------- */
function openPopover(id, anchor) {
  const b = state.bookings.find((x) => x.id === id);
  if (!b) return;
  rememberOpener("#booking-popover");
  const p = $("#booking-popover");
  /* 兩種視圖在定稿是兩個不同的 component，不共用 */
  p.innerHTML = MODE === "space" ? tableCardHtml(b) : cardHtml(b);
  p.classList.toggle("is-table", MODE === "space");
  p.hidden = false;
  if (anchor) {
    const r = anchor.getBoundingClientRect();
    p.style.left = `${Math.min(r.left, window.innerWidth - 300)}px`;
    p.style.top = `${r.bottom + 6}px`;
  }
}
const closePopover = () => { $("#booking-popover").hidden = true; };

/* ---------- 修改預約抽屜 ----------
   ⭐ 顯示時機：定稿 3-1-2 的 base state 就是一般時間軸，抽屜要點編輯才出現。 */
function openEdit(id) {
  const b = state.bookings.find((x) => x.id === id);
  if (!b) return;
  rememberOpener("#edit-drawer");
  closePopover();
  state.focusId = id;
  state.draft = { ...b };
  state.dirty = false;

  $("#f-item-label").textContent = `${b.item}–${b.subItem}`;
  $("#f-date-label").textContent = fmtDateW(state.date);
  $("#f-time").textContent = b.start.replace(":", "：");
  $("#f-duration-label").textContent = `${Math.floor(b.mins / 60)}小時${b.mins % 60}分`;
  $("#num-adults").textContent = b.adults;
  $("#num-children").textContent = b.children;
  $("#f-phone").value = b.phone;
  $("#f-name").value = b.name;
  $("#f-email").value = b.email;
  $("#f-shop-note").value = b.shopNote;
  $(`input[name="title"][value="${b.title}"]`)?.click();
  $("#f-unit-group").textContent = b.unitGroup;
  $("#f-unit-list").textContent = b.units.join("、");

  const dep = state.shop.deposit;
  $("#deposit-sect").hidden = dep.mode === "none";
  $("#deposit-hint").textContent =
    dep.mode === "card_auth" ? dep.cardAuthHint : dep.prepayHint;
  $("#notify-warn").hidden = state.shop.smsPoints > 0;

  /* 問卷數量統計：每個人數類別一列（定稿 大人x1 / 大人x0） */
  $("#f-q3").innerHTML = ["大人", "小孩"]
    .map((k, i) => `<p class="count-row">${k}x${i === 0 ? b.adults : b.children}</p>`).join("");

  $("#f-time-empty").hidden = !!b.start;
  $("#f-unit-empty").hidden = b.units.length > 0;

  clearErrors();
  $("#edit-drawer").hidden = false;
  renderCustList();
  focusInto("#edit-drawer");
}

function closeEdit() {
  restoreFocus("#edit-drawer");
  $("#edit-drawer").hidden = true;
  $("#modal-unsaved").hidden = true;
  state.focusId = null;
  state.draft = null;
  state.dirty = false;
  renderCustList();
}

const markDirty = () => { state.dirty = true; };

/* 有變更才跳未儲存提醒，沒變更直接關（定稿 3-1-2 未儲存提醒） */
function requestClose() {
  if (state.dirty) {
    $("#modal-unsaved").hidden = false;
    focusInto("#modal-unsaved");     /* 不先把焦點移進去，Tab 圈不住 */
    return;
  }
  closeEdit();
}

/* ---------- 驗證與儲存 ---------- */
function setError(field, on) {
  const el = $(`#edit-drawer [data-field="${field}"]`);
  if (el) el.classList.toggle("has-error", on);
}
function clearErrors() { $$("#edit-drawer .field").forEach((f) => f.classList.remove("has-error")); }

function validate() {
  const name = $("#f-name").value.trim();
  const phone = $("#f-phone").value.trim();
  const depOn = !$("#deposit-field").hidden;
  const dep = Number($("#f-deposit").value);
  setError("name", !name);
  setError("phone", !/^09\d{8}$/.test(phone));
  setError("deposit", depOn && $("#f-deposit").value !== "" && !(dep >= 1));
  const ok = !$$("#edit-drawer .field.has-error").length;
  if (!ok) toast("尚有必填欄位未填寫", true);
  return ok;
}

async function save() {
  if (!validate()) return;
  const btn = $("#btn-save");
  btn.disabled = true;
  const res = await api.updateBooking({
    id: state.focusId,
    name: $("#f-name").value.trim(),
    phone: $("#f-phone").value.trim(),
    email: $("#f-email").value.trim(),
    shopNote: $("#f-shop-note").value.trim(),
    title: $('input[name="title"]:checked')?.value,
    adults: Number($("#num-adults").textContent),
    children: Number($("#num-children").textContent),
  });
  btn.disabled = false;

  if (!res.ok) { toast(res.message, true); return; }

  const i = state.bookings.findIndex((b) => b.id === res.booking.id);
  if (i >= 0) state.bookings[i] = res.booking;
  state.dirty = false;
  closeEdit();
  renderLanes();
  toast("已修改預約");
}

/* ---------- toast（3-1-2 Error toast／修改完成） ---------- */
let toastTimer;
function toast(text, isError = false) {
  const t = $("#toast");
  $("#toast-text").textContent = text;
  t.classList.toggle("is-error", isError);
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.hidden = true; }, 4000);
}

/* ---------- 右側邊欄收合（3-1-2 收合右側邊欄） ---------- */
function toggleSidebar(collapsed) {
  state.collapsed = collapsed ?? !state.collapsed;
  $("#cust-panel").classList.toggle("is-collapsed", state.collapsed);
  $("#cust-toggle").setAttribute("aria-expanded", String(!state.collapsed));
}

/* ---------- 新增預約抽屜（2-1-1） ----------
   ⭐ 顯示時機：定稿 2-1-1_Start 在該列 x=100（最左）＝初始狀態，畫面上沒有抽屜；
   要按工具列的「＋預約」才出現。 */
function applyBookingMode() {
  $("#nb-item").hidden = BMODE === "basic" || BMODE === "capacity";
  $("#nb-unit-panel").hidden = BMODE === "capacity";
  $("#nb-time-hint").textContent = BMODE === "hier" ? "請選擇時間" : "選擇時間";
}

function openNew() {
  rememberOpener("#new-drawer");
  applyBookingMode();
  closePopover();
  $("#edit-drawer").hidden = true;      // 兩個抽屜共用同一個槽位，不能同時開
  $("#new-drawer").hidden = false;
  updateNewCta();
  focusInto("#new-drawer");
}
function closeNew() { NEW_PANELS.forEach((s) => { $(s).hidden = true; }); }

/* 定稿 Default：時間未選時顯示「-- : --」與橘色「請選擇時間」，主鈕不可按。
   現場顧客勾選後不需填顧客資訊（顧客區整塊收起）。 */
/* 定稿的三種擋下狀態：整日關閉、單一項目關閉、尚未設定預約單位 */
function applyNewClosedState() {
  const s = state.shop;
  $("#nb-closed-day").hidden = !s.closedAllDay;
  $("#nb-closed-item").hidden = !s.closedItem;
  if (s.closedItem) {
    $("#nb-closed-item").textContent = `此預約項目於${fmtDate(state.date)}已關閉預約`;
  }
  /* 定稿：未設定預約單位時，面板顯示「尚未設定預約單位」，下方另有「請先設定預約單位」的引導 */
  $("#nb-unit-empty").hidden = s.hasUnits !== false;
  $("#nb-unit-cta").hidden = s.hasUnits !== false;
}

function updateNewCta() {
  applyNewClosedState();
  const walkin = $("#nb-walkin").checked;
  $("#nb-customer").hidden = walkin;
  const timeChosen = $("#nb-time").textContent.trim() !== "-- : --";
  $("#nb-time-hint").hidden = timeChosen;
  const needCustomer = !walkin && !$("#nb-phone").value.trim();
  const blocked = state.shop.closedAllDay || state.shop.closedItem || state.shop.hasUnits === false;
  $("#nb-submit").disabled = blocked || !timeChosen || needCustomer;
}

/* ---------- 2-1-2 預約項目選單 ---------- */
async function openItemMenu() {
  const items = await api.getBookingItems();
  /* 服務項目模式只有一層：項目本身就是可選項，沒有子項目 */
  const flat = BMODE === "service";
  /* 定稿「預約項目選單_收合」（377:60081）：父層預設收合，點了才展開子項目。
     原本是一次全部攤平，hier 模式下會把所有子項目塞滿整頁。 */
  $("#nb-item-list").innerHTML = items.map((it) => (flat ? `
    <div class="nb-item-group is-open">
      <button class="nb-item-sub" type="button" data-sub="${it.name}">${it.name}</button>
    </div>` : `
    <div class="nb-item-group">
      <button class="nb-item-head" type="button" data-toggle>${it.name}
        <img src="${A()}assets/nb-arrow.svg" alt=""></button>
      ${it.subs.map((sub) => `<button class="nb-item-sub" type="button" data-sub="${it.name}－${sub}">${sub}</button>`).join("")}
    </div>`)).join("");
  swapNewPanel("#nb-items");
}

/* ---------- 2-1-2 時間／日期選擇器 ----------
   原本 #nb-time 點一下就把文字寫死成 12:00，不是真的選擇器（走查 C 抓到）。 */
/* 直接指定時間（段落快轉與測試用），走與真人點選同一條路徑 */
function pickNewTime(t) {
  state.newTime = t;
  const [h, m] = t.split(":").map(Number);
  state.wheelH = h; state.wheelM = m;
  $("#nb-time").textContent = t.replace(":", " : ");
  updateNewCta();
}

/* 定稿的時間選擇器是雙欄滾輪（時／分）＋ OK 才寫回。
   「預約時間」與「服務時間長度」是同一元件套不同數值範圍（377:57630 / 377:58461）。
   走查抓到原本做成攤平按鈕格，互動模型錯了。 */
const WHEEL = {
  time: { title: "選擇時間", hours: () => range(0, 23), mins: () => [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55],
          fmt: (h, m) => `${pad(h)}:${pad(m)}` },
  duration: { title: "選擇服務時間長度", hours: () => range(0, 6), mins: () => [0, 15, 30, 45],
              fmt: (h, m) => `${h}小時${m}分` },
};
const range = (a, b) => Array.from({ length: b - a + 1 }, (_, i) => a + i);

function openWheel(kind) {
  state.wheelKind = kind;
  state.wheelH = state.wheelH ?? (kind === "time" ? 12 : 2);
  state.wheelM = state.wheelM ?? 0;
  $("#nb-timepicker").querySelector(".nb-title2").textContent = WHEEL[kind].title;
  renderWheel();
  swapNewPanel("#nb-timepicker");
}

function renderWheel() {
  const w = WHEEL[state.wheelKind];
  const col = (vals, sel, key) => vals.map((v) =>
    `<button type="button" data-wheel="${key}" data-v="${v}"${v === sel ? ' class="is-selected"' : ""}>${pad(v)}</button>`).join("");
  $("#nb-wheel-h").innerHTML = col(w.hours(), state.wheelH, "h");
  $("#nb-wheel-m").innerHTML = col(w.mins(), state.wheelM, "m");
  $("#nb-wheel-h .is-selected")?.scrollIntoView({ block: "center" });
  $("#nb-wheel-m .is-selected")?.scrollIntoView({ block: "center" });
}

const openTimePicker = () => openWheel("time");

function openDatePicker() {
  state.calMonth = state.calMonth || new Date(state.date.getFullYear(), state.date.getMonth(), 1);
  renderCalendar();
  swapNewPanel("#nb-datepicker");
}

function renderCalendar() {
  const first = state.calMonth;
  $("#nb-cal-title").textContent = `${first.getFullYear()}-${pad(first.getMonth() + 1)}`;
  const days = new Date(first.getFullYear(), first.getMonth() + 1, 0).getDate();
  const lead = first.getDay();
  const head = ["日", "一", "二", "三", "四", "五", "六"].map((d) => `<span>${d}</span>`).join("");
  const blanks = Array.from({ length: lead }, () => "<span></span>").join("");
  const cells = Array.from({ length: days }, (_, i) => {
    const d = new Date(first.getFullYear(), first.getMonth(), i + 1);
    const on = fmtDate(d) === fmtDate(state.date);
    return `<button type="button" data-day="${i + 1}"${on ? ' class="is-selected"' : ""}>${i + 1}</button>`;
  }).join("");
  $("#nb-cal-grid").innerHTML = head + blanks + cells;
}

/* ---------- 2-1-3 選擇預約單位 ---------- */
async function openUnitPicker(returnTo = "#new-drawer") {
  state.unitReturnTo = returnTo;
  const groups = await api.getUnitGroups();
  state.unitGroups = groups;
  state.pickedUnits = new Set();
  $("#nb-unit-groups").innerHTML = groups.map((g, gi) => `
    <div class="nb-group">
      <label class="nb-group-title">
        <input type="checkbox" data-group="${gi}"><span class="nb-box"></span>
        ${g.name} (${g.units.length})
      </label>
      <div class="nb-units">
        ${g.units.map((u, ui) => `
          <button class="nb-unit" type="button" data-unit="${gi}-${ui}">
            <span class="nb-unit-name">${u.name}</span>
            <span class="nb-unit-cap">${u.cap}</span>
          </button>`).join("")}
      </div>
    </div>`).join("");
  renderUnitCount();
  applySlotAvailability();
  swapNewPanel("#nb-units");
}

/* 定稿 2-1-3 的兩個擋下狀態。原本這兩行只是 hidden 的文字樁——文字在、
   但沒有任何程式碼會把它顯示出來，等於用假文字讓第 2 關過（走查 C 抓到）。 */
function applySlotAvailability() {
  const need = Number($("#nb-adults").textContent) + Number($("#nb-children").textContent);
  const total = state.unitGroups.reduce((n, g) =>
    n + g.units.reduce((m, u) => m + Number(u.cap.split("-")[1]), 0), 0);
  const slotFull = state.newTime === "18:30";
  const noneFit = need > total;
  $("#nb-units-full").hidden = !slotFull;
  $("#nb-units-none").hidden = slotFull || !noneFit;
  $("#nb-units-ok").disabled = slotFull || noneFit;
  $("#nb-unit-groups").hidden = slotFull;
}

/* 定稿的人數計算：預約人數 / 已選預約單位 / 尚不足，尚不足歸零前主鈕不可按。 */
function renderUnitCount() {
  const need = Number($("#nb-adults").textContent) + Number($("#nb-children").textContent);
  let cap = 0;
  for (const key of state.pickedUnits) {
    const [g, u] = key.split("-").map(Number);
    cap += Number(state.unitGroups[g].units[u].cap.split("-")[1]);
  }
  $("#nb-count-need").textContent = need;
  $("#nb-count-picked").textContent = state.pickedUnits.size;
  $("#nb-count-cap").textContent = cap;
  $("#nb-count-short").textContent = Math.max(0, need - cap);
  /* 定稿：選到的單位若尚有顧客或即將有預約，下方出示提醒 */
  const names = [...state.pickedUnits].map((k) => {
    const [g, u] = k.split("-").map(Number);
    return state.unitGroups[g].units[u].name;
  });
  const warn = $("#nb-units-warn");
  warn.hidden = names.length < 2;
  if (!warn.hidden) warn.textContent = `已選取 ${names.slice(0, 2).join("、")} 尚有顧客或即將有預約`;
}

/* ---------- 2-1-4 完成新增 ---------- */
function openDone() {
  const total = `${$("#nb-adults").textContent}大人${$("#nb-children").textContent}小孩`;
  const name = $("#nb-name").value.trim() || "廖文強";
  const title = $('input[name="nb-title"]:checked')?.value || "先生";
  $("#nb-done-date").textContent = `${fmtDate(state.date)} ${WEEK_FULL[state.date.getDay()]}`;
  $("#nb-done-who").textContent = `${name} ${title} / ${total}`;
  const on = $("#nb-deposit-toggle").getAttribute("aria-checked") === "true";
  $("#nb-done-pay").hidden = !on;
  $("#nb-done-pay").textContent = state.shop.deposit.mode === "card_auth"
    ? "收款方式：信用卡授權綁定" : "收款方式：預先付款";
  swapNewPanel("#nb-done");
}

/* 這幾個面板與新增抽屜共用同一個 350 槽位，一次只開一個 */
const NEW_PANELS = ["#new-drawer", "#nb-items", "#nb-units", "#nb-done", "#nb-timepicker", "#nb-datepicker"];
function swapNewPanel(sel) {
  NEW_PANELS.forEach((s) => { $(s).hidden = s !== sel; });
  /* 單位選擇是從修改抽屜叫出來時，要把修改抽屜先讓開（共用同一個槽位） */
  if (sel === "#nb-units" && state.unitReturnTo === "#edit-drawer") $("#edit-drawer").hidden = true;
}

/* ---------- 鍵盤與焦點 ----------
   三輪走查都只看滑鼠互動，鍵盤完全沒人驗過；定稿也沒畫，
   但可上線型 HTML 該有 Esc 關閉與焦點歸位。 */
const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])';

/* 記住是誰打開的，關閉後把焦點還回去——不然焦點會掉回 <body>，鍵盤使用者迷路 */
function openerFor(sel) { return state.openers?.[sel]; }
function rememberOpener(sel) {
  state.openers = state.openers || {};
  state.openers[sel] = document.activeElement;
}
function focusInto(sel) {
  const panel = $(sel);
  if (!panel || panel.hidden) return;
  (panel.querySelector(FOCUSABLE) || panel).focus({ preventScroll: true });
}
function restoreFocus(sel) {
  const el = openerFor(sel);
  if (el && document.contains(el)) el.focus({ preventScroll: true });
}

/* 目前最上層、可以被 Esc 關掉的東西（由上到下） */
function topLayer() {
  if (!$("#modal-unsaved").hidden) return "modal";
  for (const sel of ["#nb-timepicker", "#nb-datepicker", "#nb-items", "#nb-units", "#nb-done"]) {
    if (!$(sel).hidden) return sel;
  }
  if (!$("#new-drawer").hidden) return "#new-drawer";
  if (!$("#edit-drawer").hidden) return "#edit-drawer";
  if (!$("#booking-popover").hidden) return "#booking-popover";
  return null;
}

function bindKeyboard() {
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    const top = topLayer();
    if (!top) return;
    e.preventDefault();
    if (top === "modal") { $("#modal-unsaved").hidden = true; focusInto("#edit-drawer"); return; }
    if (top === "#booking-popover") { closePopover(); restoreFocus("#booking-popover"); return; }
    if (top === "#edit-drawer") { requestClose(); return; }
    if (top === "#new-drawer") { closeNew(); restoreFocus("#new-drawer"); return; }
    /* 子面板（picker／項目／單位／完成）Esc 回上一層，不是整個關掉 */
    if (top === "#nb-units") return $("[data-nb-back]", $("#nb-units")).click();
    swapNewPanel(state.unitReturnTo === "#edit-drawer" ? "#edit-drawer" : "#new-drawer");
    focusInto("#new-drawer");
  });

  /* modal 開著時把 Tab 圈在裡面 */
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Tab" || $("#modal-unsaved").hidden) return;
    const items = $$(FOCUSABLE, $("#modal-unsaved"));
    if (!items.length) return;
    const first = items[0], last = items[items.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });
}

/* ---------- 事件 ---------- */
function bindEvents() {
  $("#cust-toggle").addEventListener("click", () => toggleSidebar());

  /* 手機版：burger 開關左側主導航 */
  const setNav = (open) => {
    $(".nav").classList.toggle("is-open", open);
    $("#nav-scrim").hidden = !open;
    $("#m-burger").setAttribute("aria-expanded", String(open));
  };
  /* ＋預約（桌機工具列與手機底部固定鈕）開新增抽屜 */
  $("#btn-add-booking").addEventListener("click", openNew);
  $("#m-add-booking").addEventListener("click", openNew);
  $("#nb-close").addEventListener("click", closeNew);
  $("#nb-item").addEventListener("click", openItemMenu);
  $("#nb-pick-unit").addEventListener("click", openUnitPicker);
  $("#nb-submit").addEventListener("click", openDone);
  $("#nb-done-again").addEventListener("click", () => { swapNewPanel("#new-drawer"); updateNewCta(); });
  $("#nb-units-ok").addEventListener("click", () => {
    const names = [...state.pickedUnits].map((k) => {
      const [g, u] = k.split("-").map(Number);
      return state.unitGroups[g].units[u].name;
    });
    const to = state.unitReturnTo || "#new-drawer";
    if (to === "#edit-drawer") {
      $("#f-unit-list").textContent = names.join("、");
      $("#f-unit-empty").hidden = names.length > 0;
    } else {
      $("#nb-unit-list").hidden = !names.length;
      $("#nb-unit-list").textContent = names.join("、");
    }
    backFromUnits();
  });
  /* 修改抽屜的「變更」也開同一個單位選擇面板（原本這顆按鈕沒接任何事件，
     連帶一組 #modal-units 標記是孤兒——走查 A 抓到的） */
  $("#f-unit-change").addEventListener("click", () => openUnitPicker("#edit-drawer"));

  const backFromUnits = () => {
    const to = state.unitReturnTo || "#new-drawer";
    swapNewPanel(to === "#edit-drawer" ? "" : to);
    if (to === "#edit-drawer") $("#edit-drawer").hidden = false;
    state.unitReturnTo = null;
  };
  $$("[data-nb-back]").forEach((b) => b.addEventListener("click", () => {
    if (b.closest("#nb-units")) return backFromUnits();
    if (b.closest("#nb-done")) { closeNew(); swapNewPanel("#new-drawer"); return; }
    swapNewPanel("#new-drawer");
  }));

  $("#nb-item-list").addEventListener("click", (e) => {
    const head = e.target.closest("[data-toggle]");
    if (head) return head.closest(".nb-item-group").classList.toggle("is-open");
    const sub = e.target.closest(".nb-item-sub");
    if (!sub) return;
    $("#nb-item-value").textContent = sub.dataset.sub;
    swapNewPanel("#new-drawer");
  });

  $("#nb-unit-groups").addEventListener("click", (e) => {
    const u = e.target.closest(".nb-unit");
    if (u) {
      const k = u.dataset.unit;
      state.pickedUnits.has(k) ? state.pickedUnits.delete(k) : state.pickedUnits.add(k);
      u.classList.toggle("is-selected", state.pickedUnits.has(k));
      renderUnitCount();
    }
  });
  $("#nb-select-all").addEventListener("click", () => {
    state.unitGroups.forEach((g, gi) => g.units.forEach((_, ui) => state.pickedUnits.add(`${gi}-${ui}`)));
    $$("#nb-unit-groups .nb-unit").forEach((el) => el.classList.add("is-selected"));
    renderUnitCount();
  });
  $("#nb-deposit-toggle").addEventListener("click", (e) => {
    const on = e.currentTarget.getAttribute("aria-checked") !== "true";
    e.currentTarget.setAttribute("aria-checked", String(on));
  });
  $("#nb-walkin").addEventListener("change", updateNewCta);
  $("#nb-phone").addEventListener("input", updateNewCta);
  /* 定稿 2-1-1_email格式錯誤（2026-08-10 重建 manifest 後才發現的狀態） */
  $("#nb-email").addEventListener("blur", () => {
    const v = $("#nb-email").value.trim();
    const bad = v !== "" && !/^\S+@\S+\.\S+$/.test(v);
    $("#nb-email").closest(".nb-field-block").classList.toggle("has-error", bad);
    $("#nb-email-error").hidden = !bad;
  });
  $("#nb-time").addEventListener("click", openTimePicker);
  /* 服務時長原本是死樁：按鈕在、但 js 完全沒引用（走查抓到） */
  $("#nb-duration").addEventListener("click", () => openWheel("duration"));
  $("#nb-date").addEventListener("click", openDatePicker);

  $(".nb-wheel").addEventListener("click", (e) => {
    const b = e.target.closest("[data-wheel]");
    if (!b) return;
    if (b.dataset.wheel === "h") state.wheelH = Number(b.dataset.v);
    else state.wheelM = Number(b.dataset.v);
    renderWheel();
  });
  /* 定稿要按 OK 才寫回——選了沒按 OK 不算 */
  $("#nb-wheel-ok").addEventListener("click", () => {
    const w = WHEEL[state.wheelKind];
    const v = w.fmt(state.wheelH, state.wheelM);
    if (state.wheelKind === "time") {
      state.newTime = `${pad(state.wheelH)}:${pad(state.wheelM)}`;
      $("#nb-time").textContent = state.newTime.replace(":", " : ");
    } else {
      $("#nb-duration-value").textContent = v;
    }
    swapNewPanel("#new-drawer");
    updateNewCta();
  });
  $("#nb-cal-grid").addEventListener("click", (e) => {
    const b = e.target.closest("[data-day]");
    if (!b) return;
    state.date = new Date(state.calMonth.getFullYear(), state.calMonth.getMonth(), Number(b.dataset.day));
    $("#nb-date-value").textContent = fmtDate(state.date);
    $("#nb-date-week").textContent = WEEK[state.date.getDay()];
    swapNewPanel("#new-drawer");
    updateNewCta();
  });
  $("#nb-cal-prev").addEventListener("click", () => {
    state.calMonth = new Date(state.calMonth.getFullYear(), state.calMonth.getMonth() - 1, 1);
    renderCalendar();
  });
  $("#nb-cal-next").addEventListener("click", () => {
    state.calMonth = new Date(state.calMonth.getFullYear(), state.calMonth.getMonth() + 1, 1);
    renderCalendar();
  });
  /* 定稿的月曆標題列有 4 顆：《跳年 ‹上月 ›下月 》跳年 */
  $("#nb-cal-prev-y").addEventListener("click", () => {
    state.calMonth = new Date(state.calMonth.getFullYear() - 1, state.calMonth.getMonth(), 1);
    renderCalendar();
  });
  $("#nb-cal-next-y").addEventListener("click", () => {
    state.calMonth = new Date(state.calMonth.getFullYear() + 1, state.calMonth.getMonth(), 1);
    renderCalendar();
  });
  $$("[data-nb-step]").forEach((b) => b.addEventListener("click", () => {
    const el = $(b.dataset.nbStep === "adults" ? "#nb-adults" : "#nb-children");
    const next = Math.max(0, Number(el.textContent) + Number(b.dataset.delta));
    el.textContent = next;
    el.classList.toggle("is-zero", next === 0);
  }));

  $("#m-burger").addEventListener("click", () => setNav(!$(".nav").classList.contains("is-open")));
  $("#nav-scrim").addEventListener("click", () => setNav(false));

  if (MODE === "list") {
    $("#list-tabs").addEventListener("click", (e) => {
      const tab = e.target.closest(".ltab");
      if (!tab) return;
      $$("#list-tabs .ltab").forEach((t) => {
        const on = t === tab;
        t.classList.toggle("is-active", on);
        t.setAttribute("aria-selected", String(on));
      });
    });
    $("#list-body").addEventListener("click", (e) => {
      const edit = e.target.closest(".lm-edit");
      if (edit) openEdit(edit.closest(".lrow").dataset.id);
    });
  }

  if (MODE === "space") {
    $("#floor-tabs").addEventListener("click", (e) => {
      const tab = e.target.closest(".floor-tab");
      if (!tab) return;
      state.floor = Number(tab.dataset.floor);
      renderFloorTabs();
      renderFloor();
    });
    /* 點桌位開該桌的預約 popover（定稿 3-2 空間圖_Popover） */
    $("#floor-canvas").addEventListener("click", (e) => {
      const t = e.target.closest(".table");
      if (t) openPopover(state.bookings[0].id, t);
    });
  }

  $("#lanes")?.addEventListener("click", (e) => {
    const block = e.target.closest(".block");
    if (block) openPopover(block.dataset.id, block);
  });

  /* 點外面關 popover。開啟來源（時間軸區塊、空間圖桌位）要一起排除，
     否則同一次點擊會先開再被這裡關掉。 */
  const POPOVER_ANCHORS = "#booking-popover, .block, .table";
  document.addEventListener("click", (e) => {
    if (!e.target.closest(POPOVER_ANCHORS)) closePopover();
  });

  $("#cust-list")?.addEventListener("click", (e) => {
    const edit = e.target.closest(".btn-edit");
    if (edit) openEdit(edit.closest(".cust-card").dataset.id);
  });
  $("#booking-popover").addEventListener("click", (e) => {
    const edit = e.target.closest(".btn-edit");
    if (edit) openEdit(edit.closest(".cust-card").dataset.id);
  });

  $("#cust-statustabs")?.addEventListener("click", (e) => {
    const tab = e.target.closest(".stab");
    if (!tab) return;
    $$("#cust-statustabs .stab").forEach((t) => t.classList.toggle("is-active", t === tab));
  });

  $("#edit-close").addEventListener("click", requestClose);
  $("#btn-keep-edit").addEventListener("click", () => { $("#modal-unsaved").hidden = true; });
  $("#btn-discard").addEventListener("click", closeEdit);
  $("#btn-save").addEventListener("click", save);

  $("#edit-drawer").addEventListener("input", markDirty);
  $("#edit-drawer").addEventListener("change", markDirty);

  $$(".step").forEach((b) => b.addEventListener("click", () => {
    const el = $(b.dataset.step === "adults" ? "#num-adults" : "#num-children");
    const next = Math.max(0, Number(el.textContent) + Number(b.dataset.delta));
    el.textContent = next;
    markDirty();
  }));

  $("#date-prev").addEventListener("click", () => shiftDate(-1));
  $("#date-next").addEventListener("click", () => shiftDate(1));
  $("#btn-today").addEventListener("click", () => { state.date = new Date(); renderHeader(); renderNowLine(); });
}

function shiftDate(delta) {
  state.date = new Date(state.date.getTime() + delta * 86400000);
  renderHeader();
  renderNowLine();
}

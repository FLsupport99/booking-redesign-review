/* 狀態機與渲染：時間軸格線、右側顧客清單、修改預約抽屜、未儲存提醒、toast。
   畫面只認 js/api.js 那層介面。 */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const A = () => window.ASSET_BASE || "";

const state = {
  shop: null,
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

  renderHeader();
  renderRowheads();
  renderTimehead();
  renderLanes();
  renderNowLine();
  renderStatusTabs();
  renderCustList();
  bindEvents();

  if (window.SECTION) await applySectionPreset(window.SECTION);
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

/* ---------- popover（3-1-1 時間軸_popover） ---------- */
function openPopover(id, anchor) {
  const b = state.bookings.find((x) => x.id === id);
  if (!b) return;
  const p = $("#booking-popover");
  p.innerHTML = cardHtml(b);
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
}

function closeEdit() {
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
  if (state.dirty) { $("#modal-unsaved").hidden = false; return; }
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

/* ---------- 事件 ---------- */
function bindEvents() {
  $("#cust-toggle").addEventListener("click", () => toggleSidebar());

  $("#lanes").addEventListener("click", (e) => {
    const block = e.target.closest(".block");
    if (block) openPopover(block.dataset.id, block);
  });

  document.addEventListener("click", (e) => {
    if (!e.target.closest("#booking-popover") && !e.target.closest(".block")) closePopover();
  });

  $("#cust-list").addEventListener("click", (e) => {
    const edit = e.target.closest(".btn-edit");
    if (edit) openEdit(edit.closest(".cust-card").dataset.id);
  });
  $("#booking-popover").addEventListener("click", (e) => {
    const edit = e.target.closest(".btn-edit");
    if (edit) openEdit(edit.closest(".cust-card").dataset.id);
  });

  $("#cust-statustabs").addEventListener("click", (e) => {
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

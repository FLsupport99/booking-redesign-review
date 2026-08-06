/* 顧客預約頁 — 1-1 ~ 1-7 完整 flow。
   MODE 由頁面在載入前設定：window.MODE = "basic" | "service" | "hier"
     basic   ①基本人數預約：只選人數/日期/時段
     service ②服務項目預約：先選預約項目，再選人數/日期/時段
     hier    ③階層項目預約：選父層項目 → 選子項目，再選人數/日期/時段
   資料一律走 api（js/api.js），畫面不直接碰任何端點。 */
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];

const MODE = window.MODE || "basic";
const HAS_ITEMS = MODE === "service" || MODE === "hier";
const HAS_SUB = MODE === "hier";

const state = {
  shop: null,
  adults: 2,
  children: 0,
  date: null,        // Date
  time: null,        // "18:30"
  tab: "all",
  slots: [],
  dpMonth: null,     // 日曆顯示的月份（Date, 1 號）
  item: null,        // { id, name }：service/hier 的父層項目
  subItem: null,     // { id, name }：hier 的子項目
  booking: null,
  lang: "zh",
  editing: false,    // 是否在 1-4 修改預約流程
};

const WEEK = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"];
const WEEK_EN = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const fmtDate = (d) => `${d.getFullYear()}/${String(d.getMonth() + 1).padStart(2, "0")}/${String(d.getDate()).padStart(2, "0")}`;
const fmtDateW = (d) => `${fmtDate(d)} ${(state.lang === "en" ? WEEK_EN : WEEK)[d.getDay()]}`;
const fmtMD = (d) => `${String(d.getMonth() + 1).padStart(2, "0")}/${String(d.getDate()).padStart(2, "0")}`;

/* 時段分類：午夜 00–04、上午 05–11、下午 12–16、晚上 17–23 */
function slotPeriod(t) {
  const h = parseInt(t, 10);
  if (h < 5) return "midnight";
  if (h < 12) return "morning";
  if (h < 17) return "afternoon";
  return "evening";
}

/* 1-7 中英切換：UI 字串字典（店家內容來自 API，不在此翻譯） */
const I18N = {
  findBooking: { zh: "查詢預約", en: "Find Booking" },
  bookNow: { zh: "立即預約", en: "Book Now" },
  langLabel: { zh: "EN", en: "繁中" },
  pickTitle: { zh: "選擇人數、日期與時段", en: "Party size, date & time" },
  itemTitle: { zh: "選擇預約項目", en: "Select a service" },
  toForm: { zh: "填寫預約資訊", en: "Booking details" },
  formTitle: { zh: "填寫預約資訊", en: "Booking details" },
  submit: { zh: "確認預約", en: "Confirm booking" },
  successTitle: { zh: "您已預約成功！", en: "Your booking is confirmed!" },
};
const t = (key) => (I18N[key] ? I18N[key][state.lang] : key);

/* ---------- init ---------- */
async function init() {
  const today = new Date();
  state.date = today;
  state.dpMonth = new Date(today.getFullYear(), today.getMonth(), 1);

  state.shop = await api.getShop();
  renderShop();
  bindEvents();
  if (HAS_ITEMS) renderItems();
  renderParty();
  renderDate();
  await loadSlots();
  applyModeLayout();
  if (window.SECTION) await applySectionPreset(window.SECTION);
}

/* 讓每個子流程（1-1 ~ 1-7）能單獨開一個檔案檢視：
   在同一份程式上把狀態快轉到該段落的起點。sections/*.html 用 window.SECTION 指定。 */
const DEMO_CONTACT = { name: "廖文強", phone: "0987654321", email: "test@mail.com", q1: "顧客填寫答案", note: "顧客填寫備註內容" };

async function applySectionPreset(section) {
  const pickFirstAvailable = () => {
    if (HAS_ITEMS) {
      state.item = state.shop.items[0];
      if (HAS_SUB) state.subItem = state.item.children[0];
      renderItems();
    }
    const slot = state.slots.find((s) => s.available && s.time !== "18:30");
    state.time = slot?.time || null;
    renderSlots();
  };
  const fillForm = () => {
    $("#f-name").value = DEMO_CONTACT.name;
    $("#f-phone").value = DEMO_CONTACT.phone;
    $("#f-email").value = DEMO_CONTACT.email;
    $("#f-q1").value = DEMO_CONTACT.q1;
    $("#f-note").value = DEMO_CONTACT.note;
    $("#f-agree").checked = true;
    $$(".chip").slice(0, 2).forEach((c) => c.classList.add("is-selected"));
  };
  const makeBooking = async () => {
    pickFirstAvailable();
    fillForm();
    const res = await api.createBooking(collectPayload());
    state.booking = { ...res.booking, status: "success" };
  };

  switch (section) {
    case "1-1": break;                                   // 預約頁本身
    case "1-2": pickFirstAvailable(); await openBranches(); break;
    case "1-3": pickFirstAvailable(); fillFormSummary(); showView("view-form"); break;
    case "1-4":
      await makeBooking(); renderSuccess(); fillForm(); enterModify(); break;
    case "1-5":
      await makeBooking();
      state.booking.status = "cancelled";
      renderSuccess(); showView("view-success"); break;
    case "1-6": $("#modal-lookup").hidden = false; break;
    case "1-7": toggleLang(); break;
  }
}

/* 依模式調整版面：basic 沒有項目欄、卡片維持雙欄；service/hier 顯示項目欄、卡片改直排 */
function applyModeLayout() {
  $("#item-panel").hidden = !HAS_ITEMS;
  $("#booking-card").classList.toggle("is-stacked", HAS_ITEMS);
  $("#sum-item-row").hidden = !HAS_ITEMS;
  if (HAS_ITEMS) {
    // 定稿的項目模式：標題收進卡片內，CTA 跨兩欄置底
    $("#booking-card").prepend($("#booking-title"));
    $("#booking-section").append($(".cta-block"));
  }
  renderPickerVisibility();
  updateCta();
}

/* 定稿的項目模式：選到項目（階層模式要選到子項目）之後，右側「選擇人數、日期與時段」才出現；
   在那之前項目清單滿版。basic 模式永遠顯示。 */
function itemChosen() {
  if (!HAS_ITEMS) return true;
  return HAS_SUB ? !!state.subItem : !!state.item;
}

function renderPickerVisibility() {
  if (!HAS_ITEMS) return;
  const show = itemChosen();
  $("#booking-main").hidden = !show;
  $(".cta-block").hidden = !show;
  $(".branch-search-card").hidden = !show;
  $("#booking-cols").classList.toggle("is-single", !show);
}

function renderShop() {
  const s = state.shop;
  document.title = `${s.name}｜${window.PAGE_LABEL || "線上訂位"}`;
  ["nav-shop-name", "shop-name", "side-shop-name", "form-shop-name", "ok-shop-name", "mod-shop-name"]
    .forEach((id) => { const el = $("#" + id); if (el) el.textContent = s.name; });
  $("#shop-address").textContent = s.address;
  $("#shop-map").href = s.mapUrl;
  $("#shop-phone").textContent = s.phone;
  $("#shop-phone").href = "tel:" + s.phone.replace(/-/g, "");
  $("#shop-hours").textContent = s.hours;
  $("#shop-desc").textContent = s.description;
  $("#shop-announce").textContent = s.announcement;
  $("#shop-notice").innerHTML = s.notice.map((n) => `<li>${n}</li>`).join("");
  $("#party-hint").textContent = s.party.hint;
  $("#party-over").textContent = s.party.over;
  $("#deposit-text").textContent = s.deposit.text;
  $("#deposit-summary").textContent = s.deposit.summary;

  /* 訂金規則（1-3a 預先付款 / 1-3b 信用卡授權）：三處連動 */
  const dep = s.deposit;
  const notice = $("#deposit-notice");
  notice.hidden = !dep.notice?.length;
  notice.innerHTML = (dep.notice || []).map((n) => `<li>${n}</li>`).join("");

  const terms = $("#deposit-terms");
  terms.hidden = !dep.terms?.length;
  $("#deposit-terms-title").textContent = dep.termsTitle || "";
  $("#deposit-terms-list").innerHTML = (dep.terms || []).map((x) => `<li>${x}</li>`).join("");
  $("#ok-address").textContent = s.address;
  $("#mod-address").textContent = s.address;

  const A = window.ASSET_BASE || "";
  $("#other-info-list").innerHTML = s.otherInfo.map((x) => `
    <div class="acc-item">
      <button class="acc-head" type="button">${x}<img src="${A}assets/icon-arrow.svg" alt="" class="ic20 arrow-down"></button>
      <div class="acc-body">（${x}內容由店家後台設定）</div>
    </div>`).join("");

  $("#branch-menu").innerHTML = s.branches.map((b) =>
    `<li class="${b === s.name ? "is-current" : ""}">${b}</li>`).join("");

  $("#menu-carousel").innerHTML = s.menus.map((m) =>
    `<figure class="menu-item"><img src="${m}" alt="菜單"></figure>`).join("");

  $("#share-carousel").innerHTML = [1, 2, 3, 4].map((i) => `
    <div class="share-card">
      <img class="cover" src="${A}assets/share${i}.png" alt="">
      <div class="share-user"><img src="${A}assets/avatar${i}.png" alt=""><p class="t-title">胖寶</p></div>
      <p class="t-body text-75 share-text">Lorem ipsum dolor sit amet consectetur. In tortor lacus malesuada aliquet gravida sagittis sit. Lectus maecenas congue velit tellus.</p>
      <p class="t-body text-75">2026-06-26</p>
    </div>`).join("");
}

/* ---------- 預約項目（service / hier） ---------- */
function renderItems() {
  $("#item-list").innerHTML = state.shop.items.map((it) => {
    const selected = state.item?.id === it.id;
    const subs = HAS_SUB ? `
      <div class="sub-list">
        <p class="sub-hint">選擇子項目</p>
        ${it.children.map((c) => `
          <div class="sub-row">
            <p>${c.name}</p>
            <button class="btn-sub${state.subItem?.id === c.id ? " is-selected" : ""}" type="button" data-sub="${c.id}">
              ${state.subItem?.id === c.id ? "✓ 已選擇" : "選擇"}
            </button>
          </div>`).join("")}
      </div>` : "";
    return `<div class="item-card${selected ? " is-selected" : ""}" data-item="${it.id}">
      <button class="item-head" type="button"><span class="item-radio"></span>${it.name}</button>
      ${subs}
    </div>`;
  }).join("");
}

/* ---------- 人數 ---------- */
function renderParty() {
  $("#num-adults").textContent = state.adults;
  $("#num-children").textContent = state.children;
  const total = state.adults + state.children;
  const { max } = state.shop.party;
  $$(".stepper-btn").forEach((b) => {
    const delta = +b.dataset.delta;
    const isAdult = b.dataset.step === "adults";
    if (delta > 0) b.disabled = total >= max;
    else b.disabled = isAdult ? state.adults <= 1 : state.children <= 0;
  });
  updateSubnav();
}

/* ---------- 日期 ---------- */
function renderDate() {
  $("#date-label").textContent = fmtDateW(state.date);
  renderDatepicker();
  updateSubnav();
}

function renderDatepicker() {
  const m = state.dpMonth;
  $("#dp-title").textContent = `${String(m.getMonth() + 1).padStart(2, "0")}月 ${m.getFullYear()}`;
  const first = new Date(m.getFullYear(), m.getMonth(), 1);
  const days = new Date(m.getFullYear(), m.getMonth() + 1, 0).getDate();
  const today = new Date(); today.setHours(0, 0, 0, 0);
  let html = "";
  for (let i = 0; i < first.getDay(); i++) html += `<button class="dp-day is-other" disabled></button>`;
  for (let d = 1; d <= days; d++) {
    const cur = new Date(m.getFullYear(), m.getMonth(), d);
    const disabled = cur < today;
    const selected = fmtDate(cur) === fmtDate(state.date);
    html += `<button class="dp-day${selected ? " is-selected" : ""}" ${disabled ? "disabled" : ""} data-day="${d}">${d}</button>`;
  }
  $("#dp-grid").innerHTML = html;
}

/* ---------- 時段 ---------- */
async function loadSlots() {
  $("#slot-grid").innerHTML = `<p class="t-body text-75">載入時段中…</p>`;
  const { slots } = await api.getAvailability({
    date: fmtDate(state.date), adults: state.adults, children: state.children,
    itemId: state.item?.id, subItemId: state.subItem?.id,
  });
  state.slots = slots;
  state.time = null;
  renderSlots();
}

function renderSlots() {
  const list = state.slots.filter((s) => state.tab === "all" || slotPeriod(s.time) === state.tab);
  $("#slot-grid").innerHTML = list.map((s) =>
    `<button class="slot${s.time === state.time ? " is-selected" : ""}" ${s.available ? "" : "disabled"} data-time="${s.time}">${s.time}</button>`
  ).join("") || `<p class="t-body text-75">此時段區間無可預約時間</p>`;
  updateCta();
  updateSubnav();
}

/* 進入填寫資訊的條件：時段必選；service 要選項目；hier 還要選子項目 */
function canProceed() {
  if (!state.time) return false;
  if (HAS_ITEMS && !state.item) return false;
  if (HAS_SUB && !state.subItem) return false;
  return true;
}
function updateCta() { $("#btn-to-form").disabled = !canProceed(); }

function itemLabel() {
  if (!HAS_ITEMS) return "";
  const parts = [state.item?.name, HAS_SUB ? state.subItem?.name : null].filter(Boolean);
  return parts.join(" · ");
}

function updateSubnav() {
  const parts = [];
  if (HAS_ITEMS && state.item) parts.push(itemLabel());
  parts.push(`${state.adults}大${state.children}小`);
  if (state.date) parts.push(fmtMD(state.date));
  if (state.time) parts.push(state.time);
  $("#subnav-summary").textContent = parts.join(" · ");
}

/* ---------- View 切換 + 路由 ----------
   用 hash 路由（#/form、#/success、#/modify）而非 history pathname：
   這份是靜態檔，GitHub Pages／直接雙擊開檔都沒有 SPA fallback，pathname 路由會 404。 */
const VIEWS = ["view-booking", "view-form", "view-success", "view-modify"];
const ROUTE_OF = { "view-booking": "", "view-form": "form", "view-success": "success", "view-modify": "modify" };
const VIEW_OF = { "": "view-booking", form: "view-form", success: "view-success", modify: "view-modify" };
let syncingHash = false;

function showView(id) {
  VIEWS.forEach((v) => { $("#" + v).hidden = v !== id; });
  window.scrollTo({ top: 0, behavior: "instant" });
  $("#subnav").hidden = true;
  const target = ROUTE_OF[id] ? `#/${ROUTE_OF[id]}` : "#/";
  if (location.hash === target) return;
  if (id === "view-booking" && !location.hash) return;   // 首次載入不硬塞 hash
  syncingHash = true;
  location.hash = target;
}

/* 上一頁／直接貼網址：沒有對應狀態就退回預約頁，不讓人看到空的成功頁 */
function onHashChange() {
  if (syncingHash) { syncingHash = false; return; }
  const key = location.hash.replace(/^#\/?/, "");
  const view = VIEW_OF[key];
  if (state.editing && view !== "view-modify") exitModify();
  if (!view) return showView("view-booking");
  if ((view === "view-success" || view === "view-modify") && !state.booking) return showView("view-booking");
  if (view === "view-form" && !canProceed()) return showView("view-booking");
  if (view === "view-modify" && !state.editing) return enterModify();
  showView(view);
}

function fillFormSummary() {
  if (HAS_ITEMS) $("#sum-item").textContent = itemLabel();
  $("#sum-party").textContent = `${state.adults}大人${state.children}小孩`;
  $("#sum-date").textContent = fmtDateW(state.date);
  $("#sum-time").textContent = state.time;

  const dep = state.shop.deposit;
  const on = dep.mode && dep.mode !== "none";
  $("#sum-deposit").hidden = !on;
  if (on) {
    $("#sum-amount").textContent = `NT$${dep.perPerson * (state.adults + state.children)}`;
    $("#sum-deposit-text").textContent = dep.text;
    $("#sum-deposit-warn").textContent = dep.summaryWarn || "";
  }
}

/* ---------- 表單驗證 ---------- */
function validateForm() {
  let ok = true;
  const req = [
    ["name", () => $("#f-name").value.trim()],
    ["phone", () => /^09\d{8}$|^\d{2,3}-?\d{6,8}$/.test($("#f-phone").value.trim())],
    ["email", () => /^\S+@\S+\.\S+$/.test($("#f-email").value.trim())],
    ["agree", () => $("#f-agree").checked],
  ];
  req.forEach(([key, test]) => {
    const field = $(`#booking-form [data-field="${key}"]`);
    const bad = !test();
    field.classList.toggle("has-error", bad);
    $(".field-error", field).hidden = !bad;
    if (bad) ok = false;
  });
  return ok;
}

function collectPayload() {
  return {
    shop: state.shop.name,
    mode: MODE,
    itemId: state.item?.id, itemName: state.item?.name,
    subItemId: state.subItem?.id, subItemName: state.subItem?.name,
    itemLabel: itemLabel(),
    date: fmtDate(state.date), dateLabel: fmtDateW(state.date), time: state.time,
    adults: state.adults, children: state.children,
    name: $("#f-name").value.trim(),
    title: $('input[name="title"]:checked').value,
    phone: $("#f-phone").value.trim(),
    email: $("#f-email").value.trim(),
    q1: $("#f-q1").value.trim(),
    q2: $$(".chip.is-selected").map((c) => c.dataset.chip).join("、"),
    q3: $("#f-q3").value,
    note: $("#f-note").value.trim(),
  };
}

function btnLoading(btn, on, labelWhenDone) {
  btn.disabled = on;
  $(".spinner", btn).hidden = !on;
  if (labelWhenDone) $(".btn-label", btn).textContent = on ? "處理中" : labelWhenDone;
}

/* ---------- 1-3 送出預約 ---------- */
async function submitBooking() {
  if (!validateForm()) {
    $(".has-error")?.scrollIntoView({ behavior: "smooth", block: "center" });
    return;
  }
  const btn = $("#btn-submit");
  btnLoading(btn, true, t("submit"));
  const res = await api.createBooking(collectPayload());
  btnLoading(btn, false, t("submit"));

  if (!res.ok && res.error === "FULL") {
    $("#full-date").textContent = `${state.date.getMonth() + 1}月${state.date.getDate()}日`;
    $("#full-time").textContent = state.time;
    $("#modal-full").hidden = false;
    return;
  }
  state.booking = { ...res.booking, status: "success" };
  renderSuccess();
  showView("view-success");
  if (state.shop.showLineFriendReminder) $("#modal-line").hidden = false;
}

/* ---------- 成功／查詢結果／已取消 共用畫面 ---------- */
const STATUS_TEXT = {
  success: "您已預約成功！",
  pending_review: "您的預約待店家審核",
  pending_payment: "您的預約待付款",
  cancelled: "",   // 定稿的「完成取消」頁沒有大標，狀態由卡片內 badge 呈現
  ended: "",
};

function renderSuccess() {
  const b = state.booking;
  const status = b.status || "success";
  const title = STATUS_TEXT[status] ?? STATUS_TEXT.success;
  $("#success-title").textContent = title;
  $("#success-title").hidden = !title;
  $("#ok-date").textContent = b.dateLabel;
  $("#ok-time").textContent = b.time;
  $("#ok-party").textContent = `${b.adults}大人 + ${b.children}小孩`;
  const itemRow = $("#ok-item");
  itemRow.hidden = !b.itemLabel;
  itemRow.textContent = b.itemLabel || "";
  $("#ok-code").textContent = b.code;
  $("#ok-name").textContent = b.name;
  $("#ok-phone").textContent = b.phone;
  $("#ok-email").textContent = b.email;

  const inactive = status === "cancelled" || status === "ended";
  $("#view-success").classList.toggle("is-cancelled", inactive);
  $("#cancel-badge").hidden = !inactive;
  $("#cancel-badge").textContent = status === "cancelled" ? "您的預約已取消" : "此預約已結束";
  $("#ok-arrive-note").hidden = inactive;
  $("#ok-actions").hidden = inactive;      // 已取消／已結束不給修改與取消
  $("#card-notes").hidden = inactive;

  const rows = [
    ["問卷問答題題目", b.q1], ["問卷選擇題", b.q2], ["問卷數量統計", b.q3], ["特殊需求/備註", b.note],
  ].filter(([, v]) => v);
  $("#ok-notes").innerHTML = rows.length
    ? rows.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join("")
    : `<p class="t-body text-75">無</p>`;
}

/* ---------- 1-4 修改預約：把既有的選擇卡與表單搬進修改頁，避免兩套 DOM ---------- */
const moved = [];
function moveNode(node, target) {
  moved.push({ node, parent: node.parentNode, next: node.nextSibling });
  target.appendChild(node);
}
function restoreMoved() {
  while (moved.length) {
    const { node, parent, next } = moved.pop();
    parent.insertBefore(node, next);
  }
}

function enterModify() {
  state.editing = true;
  // 項目模式：修改時也要能重選預約項目（定稿 1-4 修改預約_重選預約項目）
  if (HAS_ITEMS) moveNode($("#item-panel"), $("#modify-selection"));
  moveNode($("#booking-card"), $("#modify-selection"));
  moveNode($("#booking-form"), $("#modify-form-slot"));
  showView("view-modify");
}

function exitModify() {
  state.editing = false;
  restoreMoved();
}

/* ---------- 1-6 查詢預約 ---------- */
async function doLookup() {
  const phone = $("#lk-phone").value.trim();
  const code = $("#lk-code").value.trim();
  let ok = true;
  [["lk-phone", phone], ["lk-code", code]].forEach(([id, v]) => {
    const field = $(`[data-field="${id}"]`);
    field.classList.toggle("has-error", !v);
    $(".field-error", field).hidden = !!v;
    if (!v) ok = false;
  });
  if (!ok) return;

  const btn = $("#btn-do-lookup");
  btnLoading(btn, true, "查詢");
  const res = await api.lookupBooking({ phone, code });
  btnLoading(btn, false, "查詢");

  if (!res.ok) { $("#modal-nodata").hidden = false; return; }
  $("#modal-lookup").hidden = true;
  state.booking = { status: "success", ...res.booking };
  renderSuccess();
  showView("view-success");
}

/* ---------- 1-2 其他分店 ---------- */
async function openBranches() {
  $("#modal-branches").hidden = false;
  $("#branches-summary").textContent =
    `${state.adults}大${state.children}小 · ${fmtDateW(state.date)}`;
  $("#branch-cards").innerHTML = `<p class="t-body text-75">載入中…</p>`;
  const { branches } = await api.getBranchAvailability({
    date: fmtDate(state.date), adults: state.adults, children: state.children,
  });
  $("#branch-cards").innerHTML = branches.map((b) => `
    <div class="branch-card">
      <div class="branch-card-head">
        <span class="name">${b.name}</span>
        <span class="addr"><img src="${window.ASSET_BASE || ""}assets/icon-location.svg" alt="" class="ic18">${b.address}</span>
      </div>
      <div class="slot-grid">
        ${b.slots.map((s) => `<button class="slot" ${s.available ? "" : "disabled"} data-branch="${b.name}" data-btime="${s.time}">${s.time}</button>`).join("")}
      </div>
    </div>`).join("");
}

/* ---------- 1-7 中英切換 ---------- */
function toggleLang() {
  state.lang = state.lang === "zh" ? "en" : "zh";
  document.documentElement.lang = state.lang === "en" ? "en" : "zh-TW";
  $("#lang-label").textContent = t("langLabel");
  $$("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  $("#booking-title").textContent = t("pickTitle");
  $("#item-panel") && ($(".item-panel-title").textContent = t("itemTitle"));
  $("#btn-to-form").textContent = t("toForm");
  $(".form-title").textContent = t("formTitle");
  $(".btn-label", $("#btn-submit")).textContent = t("submit");
  $("#success-title").textContent = t("successTitle");
  renderDate();
}

/* ---------- events ---------- */
function bindEvents() {
  /* 捲過 banner 才顯示 subnav */
  new IntersectionObserver(([e]) => {
    $("#subnav").hidden = e.isIntersecting || $("#view-booking").hidden;
  }, { threshold: 0 }).observe($(".banner"));

  document.addEventListener("click", (e) => {
    const scrollBtn = e.target.closest("[data-scroll]");
    if (scrollBtn) $(scrollBtn.dataset.scroll)?.scrollIntoView({ behavior: "smooth" });

    /* 通用關閉 modal */
    const closer = e.target.closest("[data-close]");
    if (closer) $(closer.dataset.close).hidden = true;
    if (e.target.classList.contains("modal-mask")) e.target.hidden = true;

    /* 其他分店下拉（頁首店名旁） */
    if (e.target.closest("#btn-branch")) $("#branch-menu").hidden = !$("#branch-menu").hidden;
    else if (!e.target.closest(".branch-menu")) $("#branch-menu").hidden = true;
    const branchItem = e.target.closest(".branch-menu li");
    if (branchItem && !branchItem.classList.contains("is-current")) {
      state.shop.name = branchItem.textContent;
      renderShop();
      if (HAS_ITEMS) renderItems();
      renderParty(); loadSlots();
      $("#branch-menu").hidden = true;
    }

    /* accordion */
    const accHead = e.target.closest(".acc-head");
    if (accHead) accHead.closest(".acc-item").classList.toggle("is-open");

    /* 預約項目（service / hier） */
    const itemHead = e.target.closest(".item-head");
    if (itemHead) {
      const id = itemHead.closest(".item-card").dataset.item;
      const it = state.shop.items.find((x) => x.id === id);
      state.item = state.item?.id === id ? null : it;
      state.subItem = null;
      renderItems(); renderPickerVisibility(); loadSlots();
    }
    const subBtn = e.target.closest(".btn-sub");
    if (subBtn) {
      const sid = subBtn.dataset.sub;
      const sub = state.item?.children.find((c) => c.id === sid);
      state.subItem = state.subItem?.id === sid ? null : sub;
      renderItems(); renderPickerVisibility(); loadSlots();
    }

    /* 人數 */
    const step = e.target.closest(".stepper-btn");
    if (step && !step.disabled) {
      state[step.dataset.step] = Math.max(0, state[step.dataset.step] + +step.dataset.delta);
      if (state.adults < 1) state.adults = 1;
      renderParty(); loadSlots();
    }

    /* 日期 */
    if (e.target.closest("#date-input")) {
      const dp = $("#datepicker");
      dp.hidden = !dp.hidden;
      $("#date-input").classList.toggle("is-open", !dp.hidden);
    } else if (!e.target.closest(".datepicker")) {
      $("#datepicker").hidden = true;
      $("#date-input").classList.remove("is-open");
    }
    const nav = e.target.closest(".dp-nav");
    if (nav) {
      state.dpMonth = new Date(state.dpMonth.getFullYear(), state.dpMonth.getMonth() + +nav.dataset.dp, 1);
      renderDatepicker();
    }
    const day = e.target.closest(".dp-day[data-day]");
    if (day && !day.disabled) {
      state.date = new Date(state.dpMonth.getFullYear(), state.dpMonth.getMonth(), +day.dataset.day);
      $("#datepicker").hidden = true;
      $("#date-input").classList.remove("is-open");
      renderDate(); loadSlots();
    }

    /* 時段 */
    const tab = e.target.closest(".time-tab");
    if (tab) {
      state.tab = tab.dataset.tab;
      $$(".time-tab").forEach((x) => x.classList.toggle("is-active", x === tab));
      renderSlots();
    }
    const slot = e.target.closest(".slot[data-time]");
    if (slot && !slot.disabled) {
      state.time = slot.dataset.time === state.time ? null : slot.dataset.time;
      renderSlots();
    }

    /* 1-2：選了其他分店的時段 → 切換分店並帶入時段 */
    const bslot = e.target.closest(".slot[data-btime]");
    if (bslot && !bslot.disabled) {
      state.shop.name = bslot.dataset.branch;
      renderShop();
      $("#modal-branches").hidden = true;
      loadSlots().then(() => {
        state.time = bslot.dataset.btime;
        renderSlots();
        $("#booking-section").scrollIntoView({ behavior: "smooth" });
      });
    }

    /* carousel */
    const car = e.target.closest(".car-btn");
    if (car) {
      const el = $(car.dataset.car === "menu" ? "#menu-carousel" : "#share-carousel");
      el.scrollBy({ left: 292 * +car.dataset.dir, behavior: "smooth" });
    }

    /* 問卷選擇題（多選） */
    const chip = e.target.closest(".chip");
    if (chip) chip.classList.toggle("is-selected");
  });

  /* 1-1 → 1-3 */
  $("#btn-to-form").addEventListener("click", () => { fillFormSummary(); showView("view-form"); });
  $("#btn-change").addEventListener("click", () => showView("view-booking"));
  $("#btn-submit").addEventListener("click", submitBooking);

  /* 預約已滿 */
  $("#btn-full-ok").addEventListener("click", () => {
    $("#modal-full").hidden = true;
    showView("view-booking");
    loadSlots().then(() => $("#booking-section").scrollIntoView());
  });

  /* 1-2 */
  $("#btn-other-branch").addEventListener("click", openBranches);

  /* 1-6 */
  $("#btn-search-booking").addEventListener("click", () => { $("#modal-lookup").hidden = false; });
  $("#btn-do-lookup").addEventListener("click", doLookup);

  /* 1-7 */
  $("#btn-lang").addEventListener("click", toggleLang);

  /* 1-4 */
  $("#btn-modify").addEventListener("click", () => {
    // 用既有預約回填表單，再進修改頁
    const b = state.booking;
    $("#f-name").value = b.name; $("#f-phone").value = b.phone; $("#f-email").value = b.email;
    $("#f-q1").value = b.q1 || ""; $("#f-note").value = b.note || "";
    enterModify();
  });
  $("#btn-modify-back").addEventListener("click", () => { exitModify(); renderSuccess(); showView("view-success"); });
  $("#btn-do-modify").addEventListener("click", () => {
    if (!validateForm()) { $(".has-error")?.scrollIntoView({ behavior: "smooth", block: "center" }); return; }
    $("#edit-date").textContent = fmtDateW(state.date);
    $("#edit-time").textContent = state.time || state.booking.time;
    $("#edit-party").textContent = `${state.adults}大人${state.children}小孩`;
    $("#modal-confirm-edit").hidden = false;
  });
  $("#btn-confirm-edit").addEventListener("click", async () => {
    $("#modal-confirm-edit").hidden = true;
    const res = await api.updateBooking({ ...collectPayload(), code: state.booking.code });
    exitModify();
    state.booking = { ...res.booking, status: "success" };
    renderSuccess();
    showView("view-success");
  });

  /* 1-5 取消 */
  $("#btn-cancel").addEventListener("click", () => { $("#modal-cancel").hidden = false; });
  $("#btn-cancel-no").addEventListener("click", () => { $("#modal-cancel").hidden = true; });
  $("#btn-cancel-yes").addEventListener("click", async () => {
    await api.cancelBooking(state.booking.code);
    $("#modal-cancel").hidden = true;
    state.booking = { ...state.booking, status: "cancelled" };
    renderSuccess();
    showView("view-success");
  });

  window.addEventListener("hashchange", onHashChange);

  /* 輸入即清除該欄錯誤 */
  document.addEventListener("input", (e) => {
    const field = e.target.closest(".field");
    if (field?.classList.contains("has-error")) {
      field.classList.remove("has-error");
      $(".field-error", field).hidden = true;
    }
  });
}

init();

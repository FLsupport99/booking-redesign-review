/* 驗收管線的單一設定檔。build / copy-check / smoke 三關共用，腳本本身不含常數。
   Part 3／Part 4 要沿用這套流程時，複製一份這個檔改內容即可，tools/ 與 tests/ 不需要動。 */

/* ---------- 產出物結構（build 用） ---------- */

export const TITLE_PREFIX = "顧客預約頁";

export const MODES = [
  { key: "basic", file: "1-基本人數預約.html", label: "① 基本人數預約", hasItems: false, hasSub: false },
  { key: "service", file: "2-服務項目預約.html", label: "② 服務項目預約", hasItems: true, hasSub: false },
  { key: "hier", file: "3-階層項目預約.html", label: "③ 階層項目預約", hasItems: true, hasSub: true },
];

export const SECTIONS = [
  { id: "1-1", name: "顧客預約頁" },
  { id: "1-2", name: "查看其他分店時段" },
  { id: "1-3", name: "填寫資訊" },
  { id: "1-4", name: "修改預約" },
  { id: "1-5", name: "取消預約" },
  { id: "1-6", name: "查詢預約" },
  { id: "1-7", name: "中英切換" },
];

/* ---------- 第 3 關：行為斷言（smoke 用） ---------- */

/* 每個 section 快轉後應該停在哪個 view */
export const EXPECT_VIEW = {
  "1-1": "view-booking",
  "1-2": "view-booking",
  "1-3": "view-form",
  "1-4": "view-modify",
  "1-5": "view-success",
  "1-6": "view-booking",
  "1-7": "view-booking",
};

/* 快轉後應該同時打開的 modal */
export const EXPECT_MODAL = {
  "1-2": "#modal-branches",
  "1-6": "#modal-lookup",
};

export const ALL_VIEWS = ["view-booking", "view-form", "view-success", "view-modify"];

/* 網址參數變體：只在 basic 模式各掃一次。
   expect 用 [selector, "visible" | "hidden"] 表示，不寫成 callback，
   這樣同一份設定將來也能餵給非 HTML 的實作。 */
export const VARIANTS = [
  { q: "?state=closed", label: "未開放預約", expect: [["#booking-section", "hidden"]] },
  { q: "?state=null", label: "什麼都沒設定", expect: [[".announce", "hidden"]] },
  { q: "?state=no-party", label: "隱藏人數選項", expect: [["#party-col", "hidden"]] },
  { q: "?deposit=card_auth", label: "信用卡授權", expect: [["#deposit-notice", "visible"]] },
  { q: "?deposit=none", label: "不收訂金", expect: [[".cta-deposit", "hidden"]] },
];

/* 圖片必須真的載得起來（抓 QR、icon 換檔名後忘了更新這類） */
export const REQUIRED_IMAGES = [".line-block .line-qr"];

/* ---------- 顯示時機（Part 2 比對後補的斷言，見 REVIEW-CHECKLIST.md） ---------- */

/* 項目模式：選到項目（hier 要選到子項目）之前，右側選擇區不得出現。
   實作在 js/app.js 的 renderPickerVisibility()。 */
export const PICKER_GATE = {
  gatedSelectors: ["#booking-main", ".cta-block", ".branch-search-card"],
  itemSelector: ".item-card[data-item]",
  subSelector: ".btn-sub[data-sub]",
};

/* 預約成功後的 LINE 加好友 popup（Part 2 曾整塊漏做） */
export const SUCCESS_POPUP = "#modal-line";

/* hash 路由：view → hash。用 hash 而非 pathname，因為靜態託管沒有 SPA fallback（js/app.js:363）。 */
export const VIEW_HASH = {
  "view-booking": "#/",
  "view-form": "#/form",
  "view-success": "#/success",
  "view-modify": "#/modify",
};

/* 沒有對應狀態就直接貼網址時，必須退回預約頁——不能讓人看到空的成功頁（js/app.js:382）。 */
export const DEEPLINK_FALLBACK = ["#/form", "#/success", "#/modify"];

/* 送出預約用的假資料。phone／email 要通過 validateForm() 的格式檢查（js/app.js:412）。 */
export const FORM_FIXTURE = {
  "#f-name": "測試顧客",
  "#f-phone": "0987654321",
  "#f-email": "test@mail.com",
  "#f-q1": "顧客填寫答案",
};
/* 同意條款是樣式化 checkbox：真正的 input 被 .check-box 蓋住，要點 label（跟真人一樣）。 */
export const FORM_AGREE = '[data-field="agree"] label.check';
export const FORM_AGREE_INPUT = "#f-agree";
export const FORM_SUBMIT = "#btn-submit";

/* ---------- 第 2 關：文案對定稿（copy-check 用） ---------- */

export const figma = {
  FILE_KEY: "AQilb21aXkXybY5c1wDFq8",

  /* 稽核範圍：定稿中「畫面文字最完整」的節點，一頁一個。 */
  TARGETS: [
    { id: "871:5340", name: "① 1-1 基本人數預約" },
    { id: "1064:30158", name: "① 1-3 填寫資訊" },
    { id: "1498:33396", name: "① 1-3 預約成功" },
    { id: "1023:24314", name: "① 1-2 其他分店" },
    { id: "1331:25552", name: "① 1-6 查詢預約" },
    { id: "1272:19670", name: "① 1-4 修改預約" },
    { id: "1847:18646", name: "② 1-1 服務項目預約" },
    { id: "1637:65824", name: "③ 1-1 階層項目預約" },
    { id: "1234:46579", name: "① 1-3 待審核" },
    { id: "1122:32909", name: "① 1-3a 待付款" },
    { id: "1225:43754", name: "① 1-3a 付款完成" },
    { id: "1272:18141", name: "① 1-3a 待審核+待付款" },
    { id: "1122:33308", name: "① 1-3b 待綁卡" },
    { id: "1225:43911", name: "① 1-3b 綁卡完成" },
    { id: "1023:25823", name: "① 1-1 未開放預約" },
  ],

  /* 實作端的文案來源：模板 + 兩支 js（JS 產生的字也算） */
  SOURCE_FILES: ["src/template.html", "js/app.js", "js/api.js"],

  /* 這些是「資料」不是 UI 文案：店家自填內容、假資料、時間數字。不列入稽核。 */
  IGNORE_PATTERNS: [
    /^[\d\s:/年月日()~－–-]+$/,            // 純數字／時間／日期
    /^NT\$/, /^\$/,                         // 金額
    /lorem ipsum/i,
    /^找活燒烤/, /^台北市/, /^02-/, /^每週/,  // 店家資料
    /^[A-Za-z@._-]+$/,                      // email／英數 id
    /^(胖寶|廖文強|答案[A-C]|大人x\d|測項|Sitemap)$/,
    /^(精緻主廚特餐|自助吧吃到飽|星空酒吧|早午時光|精緻午茶|晚安佳餚)$/, // 項目假資料
    /^(已回答問題|備註內容文字|顧客填寫答案|顧客填寫備註內容)$/,          // 表單填寫範例
    /\d+大人|\d+大\d+小/,                                              // 人數摘要（動態組字）
  ],

  /* 已知刻意不同或本輪範圍外，附理由；有理由才准放行。
     ⚠️ 不要為了讓它變綠而亂加豁免——每一條都要有理由。 */
  ACCEPTED: {
    "English": "語言鈕在中文版顯示 EN（定稿另一張圖為 English，取較短者）",
    "答案A、答案Ｂ": "定稿全形Ｂ為筆誤，實作用半形 B",
    "填寫聯絡資訊": "定稿 1-6 內嵌的另一版標題，主線一律用「填寫預約資訊」",
  },
};

/* Part 3 ②「預約管理視圖」驗收設定。三關共用，腳本在 ../verify-kit/。
   本階段只做時間軸（3-1-1 + 3-1-2）；空間圖與清單之後補進 MODES。 */

export const TITLE_PREFIX = "預約管理";

/* 本專案的「MODES」是三個視圖。每個視圖有自己的狀態清單（不是 customer-booking 那種共用矩陣）。 */
export const MODES = [
  {
    key: "list",
    file: "3-清單.html",
    label: "③ 清單",
    sections: [{ id: "modify", name: "清單_修改預約" }],
  },
  {
    key: "space",
    file: "2-空間圖.html",
    label: "② 空間圖",
    sections: [{ id: "popover", name: "空間圖 popover" }],
  },
  {
    key: "timeline",
    file: "1-時間軸.html",
    label: "① 時間軸",
    sections: [
      { id: "popover", name: "預約 popover" },
      { id: "modify", name: "修改預約" },
      { id: "collapsed", name: "收合右側邊欄" },
      { id: "error", name: "Error toast" },
      { id: "unsaved", name: "未儲存提醒" },
      { id: "done", name: "修改完成" },
    ],
  },
];

/* ---------- 第 3 關：行為斷言 ---------- */

export const ALL_VIEWS = ["view-timeline", "view-space", "view-list"];

/* ⭐ 顯示時機：3-1-2 的 base state 就是一般時間軸，修改抽屜要點編輯才出現。
   （定稿 3-1-2_Start 在該列 x=100 最左＝初始狀態，與 3-1-1 時間軸同畫面。） */
export const EDIT_GATE = {
  drawer: "#edit-drawer",
  openBtn: ".cust-card.is-focus .btn-edit, .cust-card .btn-edit",
  closeBtn: "#edit-close",
  focusedCard: ".cust-card.is-focus",
};

/* 右側邊欄收合（定稿 3-1-2_收合右側邊欄 是獨立 frame） */
export const SIDEBAR = { root: "#cust-panel", toggle: "#cust-toggle", grid: "#grid-scroll" };

/* 未儲存提醒：有變更才跳，沒變更直接關（定稿 3-1-2_未儲存提醒） */
export const UNSAVED = {
  modal: "#modal-unsaved",
  keep: "#btn-keep-edit",
  discard: "#btn-discard",
  dirtyField: "#f-name",
};

export const TOAST = "#toast";
export const POPOVER = "#booking-popover";
export const NOW_LINE = "#now-line";

/* 清單（3-3-1／3-3-2） */
export const LIST = {
  view: "#view-list",
  tabs: "#list-tabs",
  tab: ".ltab",
  body: "#list-body",
  row: ".lrow",
  slotHead: ".slot-head",
  edit: ".lm-edit",
};

/* 空間圖（3-2） */
export const SPACE = {
  view: "#view-space",
  timebar: "#timebar",
  floorTabs: "#floor-tabs",
  canvas: "#floor-canvas",
  table: ".table",
};

export const REQUIRED_IMAGES = [];

/* ---------- 第 2 關：文案對定稿 ---------- */

export const figma = {
  FILE_KEY: "XphLPcM7qUdcVO6EwjYJy9",

  /* frames 來自 tools/manifest_p3.json。只掃這些 frame 底下的文字——
     定稿畫布上有設計自己的修改註記（「字太多」「加底色」…），它們不在 frame 內，自然排除。 */
  TARGETS: [
    {
      id: "506:90181", name: "3-1-1 時間軸",
      frames: ["496:44515", "496:47067", "506:88239"],
    },
    {
      id: "526:91348", name: "3-1-2 時間軸_修改預約",
      frames: ["526:82399", "523:48065", "523:62594", "526:86701", "526:89600", "526:93202"],
    },
    {
      id: "506:90182", name: "3-2 空間圖",
      frames: ["500:50579", "500:51442"],
    },
    {
      id: "506:90183", name: "3-3-1 清單",
      frames: ["472:56764", "496:43355", "506:53956", "506:54444",
               "506:54932", "506:55420", "506:55908", "506:56396"],
    },
    {
      id: "526:94768", name: "3-3-2 清單_修改預約",
      frames: ["526:65145", "526:71171", "526:92447"],
    },
  ],

  SOURCE_FILES: ["src/template.html", "js/app.js", "js/api.js"],

  /* 工具列圖示：這三個是本檔案內的 instance，REST 匯得出來（npm run icons）。
     ⚠️ 導航列圖示的 component master 在**外部 library**，REST 一律回 null——
        那批是用 get_design_context 取回的資產 URL 下載的，見 assets/README.md。 */
  ICONS: {
    "fn-search": "496:44526",
    "fn-announcement": "496:44529",
    "fn-export": "496:44532",
  },

  /* 「資料」不是 UI 文案：顧客名、桌號、示意時間戳、假 email。 */
  IGNORE_PATTERNS: [
    /^[\d\s:/年月日()~－–—.-]+$/,                 // 純數字／時間／日期
    /^NT\$/, /^\$/,
    /lorem ipsum/i,
    /^[A-Za-z0-9@._-]+$/,                         // email／英數 id（含帶數字的假信箱）
    /^(鄂瑜|蔡|暮|吳恩氣|熊|陳樂|孫小美|河智昊|鹿|廖文強|楊|邱|程樂樂)$/,  // 假顧客名
    /^Allison Ekstrom Bothman$/,                   // 假顧客名（長名字換行示意）
    /^[FOB]\d?$/, /^[FOB] 區$/, /^群組[A-Z]$/, /^桌次\d/, /^Unit \d/, /^單位\d/,  // 桌次／組別假資料
    /^(精緻主廚特餐|早午時光|空間圖\d)/,            // 預約項目假資料
    /^(顧客備註|店家備註) /,                        // 備註示意內容
    /同步: 20|^自建 |^建立: |^最後更新/,            // 肚肚同步／稽核軌跡示意時間戳
    /^\d+(大人|小孩)$/,
  ],

  /* 已知刻意不同或本階段範圍外，附理由才准放行。
     下面五條是**設計留在定稿上的修改註記**，不是 UI 文案。它們在「右側邊欄顧客清單
     卡片樣式」那張規格板內，所以 frame 白名單擋不掉。
     ✅ 2026-08-09 Ian 確認：就是註記，不需處理，實作照定稿現況即可。 */
  ACCEPTED: {
    "預約狀態卡片樣式": "規格板的標題，不是畫面上的字",
    "字太多": "設計註記（待設計確認）",
    "把「秒」拿掉": "設計註記（待設計確認）——實作已不顯示秒",
    "加底色": "設計註記（待設計確認）",
    "「完成」時間換行": "設計註記（待設計確認）——實作用獨立一行呈現",
  },
};

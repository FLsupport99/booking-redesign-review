/* Part 3 ②「預約管理視圖」驗收設定。三關共用，腳本在 ../verify-kit/。
   本階段只做時間軸（3-1-1 + 3-1-2）；空間圖與清單之後補進 MODES。 */

export const TITLE_PREFIX = "預約管理";

/* 本專案的「MODES」是三個視圖。每個視圖有自己的狀態清單（不是 customer-booking 那種共用矩陣）。 */
export const MODES = [
  {
    key: "timeline",
    file: "1-時間軸.html",
    label: "① 時間軸",
    sections: [
      { id: "popover", name: "預約 popover" },
      { id: "new", name: "新增預約" },
      { id: "new-filled", name: "新增預約_填寫後" },
      { id: "new-items", name: "選擇預約項目" },
      { id: "new-units", name: "選擇預約單位" },
      { id: "new-done", name: "完成新增" },
      { id: "new-full", name: "時段已滿" },
      { id: "modify", name: "修改預約" },
      { id: "collapsed", name: "收合右側邊欄" },
      { id: "error", name: "Error toast" },
      { id: "unsaved", name: "未儲存提醒" },
      { id: "done", name: "修改完成" },
    ],
  },
  {
    key: "space",
    file: "2-空間圖.html",
    label: "② 空間圖",
    sections: [{ id: "popover", name: "空間圖 popover" }],
  },
  {
    key: "list",
    file: "3-清單.html",
    label: "③ 清單",
    sections: [{ id: "modify", name: "清單_修改預約" }],
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

/* 新增預約抽屜（2-1-1）。⭐ 定稿 2-1-1_Start 在該列 x=100 最左＝初始狀態，
   畫面上沒有抽屜；要按工具列的「＋預約」才出現。 */
/* 預約模式（?bmode=）對抽屜結構的影響——文案稽核抓不到這種差異 */
export const BOOKING_MODES = [
  { key: "hier", item: true, unit: true, hint: "請選擇時間" },
  { key: "service", item: true, unit: true, hint: "選擇時間" },
  { key: "basic", item: false, unit: true, hint: "選擇時間" },
  { key: "capacity", item: false, unit: false, hint: "選擇時間" },
];

export const NEW_BOOKING = {
  drawer: "#new-drawer",
  open: "#btn-add-booking",
  close: "#nb-close",
  submit: "#nb-submit",
  walkin: "#nb-walkin",
  customer: "#nb-customer",
  time: "#nb-time",
  timeHint: "#nb-time-hint",
  item: "#nb-item",
  unitPanel: "#nb-unit-panel",
  timePicker: "#nb-timepicker",
  datePicker: "#nb-datepicker",
  unitsFull: "#nb-units-full",
  unitsOk: "#nb-units-ok",
};

/* 修改抽屜的區塊順序（走查 A 抓到過一次錯位）與「變更」單位的互動 */
export const EDIT_DRAWER_ORDER = [".unit-card", "#survey-sect", "#deposit-sect"];
export const EDIT_UNIT_CHANGE = "#f-unit-change";

/* 鍵盤與焦點：三輪走查都只看滑鼠，定稿也沒畫，但可上線型 HTML 該有 */
export const A11Y = {
  focusable: 'a[href], button:not([disabled]), input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])',
};

export const TOAST = "#toast";
export const POPOVER = "#booking-popover";
/* 空間圖的 popover 在定稿是獨立元件 Card / Table Info-new，與時間軸的不同 */
export const TABLE_CARD = {
  root: ".tcard",
  state: ".tcard-state",
  swap: ".tcard-swap",
  pick: ".tcard-pick",
  units: ".card-chip.is-unit",
};
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
export const TIMEBAR = { track: "#tb-track", prev: "#tb-prev", next: "#tb-next", now: ".tb-hour.is-now" };

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
      id: "381:105355", name: "2-1-1 階層項目預約_新增預約",
      frames: ["377:61212", "377:45699", "377:60912", "377:61112", "377:63447",
               /* 377:63552（新增預約_開啟預約建立通知）在 Figma 已被刪除 */
               "377:63657",
               /* 2026-08-10 重建 manifest 後發現的新狀態圖 */
               "584:50922", "526:96835", "377:63857", "377:63757", "377:64568",
               "413:141904", "377:65056", "377:64952", "377:61012", "377:64852",
               "377:56176", "377:55462", "526:94904", "377:64054", "377:64370",
               "377:65162", "381:99303", "381:102125", "381:103536"],
    },
    {
      id: "413:154218", name: "2-2-1 服務項目預約_新增預約",
      frames: ["409:120959", "409:122733", "413:141140", "413:141247", "413:141351",
               "413:142256", "413:144621", "413:144793", "413:145507", "409:122392"],
    },
    {
      id: "413:154219", name: "2-2-2 服務項目預約_選擇預約項目",
      frames: ["413:124781", "413:142448", "413:142426", "413:142440"],
    },
    {
      id: "413:154220", name: "2-2-3 服務項目預約_完成新增",
      frames: ["413:136576", "413:152638", "413:152702", "413:152767", "413:152816", "413:152880"],
    },
    {
      id: "413:154224", name: "2-3-1 基本人數預約_新增預約",
      frames: ["413:122956", "413:123667", "413:143888", "413:143988", "413:144095",
               "413:144448", "413:147695", "413:148409", "413:123767"],
    },
    {
      id: "413:154225", name: "2-3-2 基本人數預約_完成新增",
      frames: ["413:138086", "413:138761", "413:153150", "413:153199", "413:153263", "413:138826"],
    },
    {
      id: "413:154226", name: "2-4-1 總量控管_新增預約",
      frames: ["413:134769", "413:135475", "413:150596", "413:152058", "413:152158",
               "413:152257", "413:135570"],
    },
    {
      id: "413:154227", name: "2-4-2 總量控管_完成新增",
      frames: ["413:139636", "413:140308", "413:153964", "413:154013", "413:154077", "413:140370"],
    },
    {
      id: "381:109846", name: "2-1-2 新增預約_Pickers",
      frames: ["377:56889", "377:59212", "377:57630", "377:58461", "377:59956",
               "377:59989", "377:60021", "377:60051",
               /* 2026-08-10：build_manifest 的尺寸門檻原本 200×200，
                  把這幾張窄/矮的互動狀態圖濾掉了，門檻降到 100 後才出現 */
               "377:58381", "377:58421", "377:60081",
               "381:105356", "381:108282", "381:106798"],
    },
    {
      id: "381:112760", name: "2-1-3 新增預約_選擇預約單位",
      frames: ["377:52554", "377:53265", "377:55324", "377:65762", "377:65838",
               "377:65911", "377:65984", "377:53949", "377:54640", "381:109847",
               "377:51153", "377:51867",
               /* 2026-08-10 重建 manifest 後發現 */
               "579:57956"],
    },
    {
      id: "381:115660", name: "2-1-4 新增預約_完成新增",
      frames: ["377:49800", "377:55397", "377:64787", "377:65708", "377:64671",
               "377:64737", "381:112762", "381:114254"],
    },
    {
      id: "399:120612", name: "2-1-5 階層項目預約_修改預約",
      frames: ["381:115661", "381:117005", "381:118681", "399:118925",
               "526:71883", "526:83967", "526:91349"],
    },
    {
      id: "506:90183", name: "3-3-1 清單",
      frames: [/* 桌機 8 種狀態 */
               "472:56764", "496:43355", "506:53956", "506:54444",
               "506:54932", "506:55420", "506:55908", "506:56396",
               /* 手機 8 種狀態（390） */
               "506:71969", "506:78447", "506:82694", "506:83115",
               "506:83536", "506:83957", "506:84378", "506:84799"],
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
    /^(林小美|葉大雄|章|江|賴|呂文|盧廣仲|兩津|林忠諭|白安|陸)$/,   // 顧客搜尋清單的假名單
    /^不吃辣$/,                                    // 問卷選項假資料
    /^[FOB]\d?$/, /^[FOB] 區$/, /^群組[A-Z]$/, /^桌次\d/, /^Unit \d/, /^單位\d/,  // 桌次／組別假資料
    /^(精緻主廚特餐|早午時光|空間圖\d)/,            // 預約項目假資料
    /^(顧客備註|店家備註) /,                        // 備註示意內容
    /同步: 20|^自建 |^建立: |^最後更新/,            // 肚肚同步／稽核軌跡示意時間戳
    /^\d+(大人|小孩)$/,
    /^[\uE000-\uF8FF\u{F0000}-\u{10FFFD}]+$/u,   // SF Symbols 私用區字元：定稿的 iOS 裝置外框，不是 app 文案
  ],

  /* 已知刻意不同或本階段範圍外，附理由才准放行。
     下面五條是**設計留在定稿上的修改註記**，不是 UI 文案。它們在「右側邊欄顧客清單
     卡片樣式」那張規格板內，所以 frame 白名單擋不掉。
     ✅ 2026-08-09 Ian 確認：就是註記，不需處理，實作照定稿現況即可。 */
  ACCEPTED: {
    /* 這行整條由姓名／稱謂／人數組成，沒有任何 4 字以上的固定文案可以當證據，
       比對工具無法驗證（不是實作缺漏——見 js/app.js 的 openDone）。
       組成的各部分（先生、大人、小孩）本身都仍有被稽核到。 */
    "廖文強 先生 / 2大人2小孩": "整行皆為動態值組成，無固定文案可比對",

    "預約狀態卡片樣式": "規格板的標題，不是畫面上的字",
    "字太多": "設計註記（待設計確認）",
    "把「秒」拿掉": "設計註記（待設計確認）——實作已不顯示秒",
    "加底色": "設計註記（待設計確認）",
    "「完成」時間換行": "設計註記（待設計確認）——實作用獨立一行呈現",
  },
};

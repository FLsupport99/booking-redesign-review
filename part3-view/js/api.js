/* API adapter — 上線時只改這一檔：把 mock 換成真端點。
   介面（與畫面解耦）：
     api.getShop()                 → { name, groups:[{name,cap,units:[...]}], hours, item }
     api.getBookings(dateISO)      → [Booking]
     api.updateBooking(payload)    → { ok, booking } | { ok:false, error, message }
     api.getStatusCounts(dateISO)  → [{ key, label, count }]
*/
const api = (() => {
  const delay = (ms) => new Promise((r) => setTimeout(r, ms));

  /* 桌次分組（定稿左欄：F 區 1-2 / O 區 10-20 / B 區 2-4） */
  const GROUPS = [
    { name: "F 區", cap: "(1-2)", units: ["F1", "F2", "F3", "F4", "F5", "F6"] },
    { name: "O 區", cap: "(10-20)", units: ["O1", "O2", "O3"] },
    { name: "B 區", cap: "(2-4)", units: ["B1", "B2", "B3"] },
  ];

  /* 時間軸範圍：09:30 起，每格 30 分鐘，共 30 格（到隔日 00:30） */
  const OPEN = "09:30", SLOT_MIN = 30, SLOT_COUNT = 30;

  /* 預約狀態。timeline 區塊與清單分頁共用同一組 key。 */
  const STATUS = [
    { key: "confirmed", label: "確認預約" },
    { key: "arrived", label: "已到店" },
    { key: "seated", label: "已入座" },
    { key: "done", label: "完成" },
    { key: "review", label: "待審核" },
    { key: "payment", label: "待付款/綁卡" },
    { key: "noshow", label: "未到店" },
    { key: "cancelled", label: "取消預約" },
  ];

  const B = (id, unit, start, mins, name, phone, adults, children, status, flag) =>
    ({ id, unit, start, mins, name, phone, adults, children, status, flag,
       title: "先生", email: "test@findlife.com.tw",
       item: "精緻主廚特餐", subItem: "早午時光",
       unitGroup: "群組A", units: ["桌次1", "桌次2"],
       tags: ["葷食", "商業午餐", "兒童椅x1"],
       question: "1. 問答題答案",
       /* 定稿清單那張的備註示意內容 */
       surveyChoices: ["葷食", "商業午餐", "兒童椅x1"],
       custNote: "有抽菸，希望能安排在庭院的位置",
       shopNote: "老闆朋友，特別招待甜品",
       savedCustomer: true,
       source: "自建", createdAt: "2022-01-01 12:00", updatedAt: "2022-01-01 12:00",
       code: "47989", posSync: true, posSyncAt: "2022-12-31 18:00",
       /* 狀態時間軌跡（定稿「預約狀態卡片樣式」：到店／入座／完成／未到店／商家取消各有一行） */
       stamps: { arrived: "2022-12-31 23:59", seated: "2022-12-31 23:59",
                 finished: "2022-12-31 23:59", noshow: "2022-12-31 23:59",
                 cancelled: "2022-12-31 23:59" },
       stayedMins: status === "done" || status === "seated" ? 148 : null });

  const BOOKINGS = [
    B("b1", "F1", "11:30", 120, "吳恩氣", "0912345678", 2, 0, "confirmed"),
    B("b2", "F2", "11:30", 120, "熊", "0978678567", 2, 0, "confirmed", "warn"),
    B("b3", "F3", "12:30", 120, "陳樂", "0912345678", 2, 0, "review"),
    B("b4", "F4", "12:30", 120, "孫小美", "0912345678", 2, 2, "confirmed", "alert"),
    B("b5", "F6", "10:30", 90, "河智昊", "0912345678", 2, 0, "done"),
    B("b6", "F6", "12:30", 120, "廖文強", "0912345678", 4, 0, "arrived"),
    B("b7", "O1", "10:00", 120, "鹿", "0912345678", 2, 0, "done"),
    B("b8", "O1", "13:00", 120, "楊", "0922123123", 2, 0, "arrived", "warn"),
    B("b9", "O2", "10:30", 90, "孫小美", "0988877777", 4, 0, "done", "alert"),
    B("b10", "O2", "13:00", 120, "邱", "0988877777", 2, 0, "arrived", "alert"),
    B("b11", "O3", "12:30", 120, "程樂樂", "0912345678", 2, 0, "confirmed"),
    B("b12", "B1", "12:00", 120, "鄂瑜", "0922123123", 2, 0, "seated", "warn"),
    B("b13", "B2", "12:00", 120, "熊", "0978678567", 2, 0, "seated"),
  ];

  /* 定稿清單的兩種變體：線上來源、尚未存成顧客、超長項目名 */
  Object.assign(BOOKINGS[5], {
    source: "線上", email: "support9999@findlife.com.tw",
    item: "預約項目的字數最多有十四個字", subItem: "子項目名稱",
  });
  Object.assign(BOOKINGS[1], { savedCustomer: false });

  /* 空間圖：樓層與桌位。座標是定稿 Content 內的絕對位置（Group 57），
     卡片 88×88（方）／88×92（圓，多一截進度條）。 */
  const FLOORS = [
    { key: "f1", name: "一樓", tables: [
      { id: "t1", label: "G8", cap: "(1-4)", shape: "rect", x: 92, y: 129, state: "empty" },
      { id: "t2", label: "G8", cap: "(1-4)", shape: "rect", x: 216, y: 129, state: "seated", multi: 2, warn: true, progress: .45 },
      { id: "t3", label: "G8", cap: "(1-4)", shape: "rect", x: 340, y: 129, state: "occupied", timer: "10:00", progress: .7 },
      { id: "t4", label: "G8", cap: "(1-4)", shape: "rect", x: 464, y: 129, state: "arrived", multi: 2, coming: true, progress: .3 },
      { id: "t5", label: "G8", cap: "(1-4人)", shape: "rect", x: 588, y: 129, state: "late", progress: 1 },
      { id: "t6", label: "G8", cap: "(1-4)", shape: "rect", x: 712, y: 129, state: "empty" },
      { id: "t7", label: "O1", cap: "(5-8)", shape: "circle", x: 92, y: 301, state: "seated", multi: 2, warn: true, coming: true, progress: .5 },
      { id: "t8", label: "O2", cap: "(5-8)", shape: "circle", x: 216, y: 301, state: "empty" },
      { id: "t9", label: "O2", cap: "(5-8)", shape: "circle", x: 340, y: 301, state: "occupied", timer: "10:20", progress: .8 },
      { id: "t10", label: "O2", cap: "(5-8)", shape: "circle", x: 464, y: 301, state: "arrived", progress: .35 },
      { id: "t11", label: "O2", cap: "(5-8)", shape: "circle", x: 588, y: 301, state: "seated", progress: .6 },
    ]},
    { key: "f2", name: "二樓", tables: [
      { id: "t12", label: "B1", cap: "(2-4)", shape: "rect", x: 92, y: 129, state: "empty" },
      { id: "t13", label: "B2", cap: "(2-4)", shape: "rect", x: 216, y: 129, state: "occupied", progress: .5 },
    ]},
  ];

  /* demo 劇本：把電話改成這支再儲存會回 Error toast（定稿 3-1-2 Error toast） */
  const ERROR_PHONE = "0900000000";

  const clone = (b) => JSON.parse(JSON.stringify(b));

  const slot = (time, list) => ({
    time,
    groups: list.length,
    people: list.reduce((n, b) => n + b.adults + b.children, 0),
    bookings: list,
  });

  return {
    OPEN, SLOT_MIN, SLOT_COUNT, STATUS,

    /* 清單：依日期→時段分組。定稿每個時段有「組數 N｜人數 N」表頭，
       跨日時多一列日期表頭。 */
    async getListGroups(status = "confirmed") {
      await delay(120);
      const rows = BOOKINGS.filter((b) => status === "all" || true).map(clone);
      const byTime = {};
      rows.forEach((b) => { (byTime[b.start] ||= []).push(b); });
      const times = Object.keys(byTime).sort();
      return [
        { date: null, slots: times.slice(0, 1).map((t) => slot(t, byTime[t])) },
        { date: "2026-08-01", weekday: "週六", slots: times.slice(1, 4).map((t) => slot(t, byTime[t])) },
        { date: "2026-08-01", weekday: "週六", slots: times.slice(4).map((t) => slot(t, byTime[t])) },
      ].filter((g) => g.slots.length);
    },

    /* 預約項目（2-1-2 選單）與預約單位群組（2-1-3）。名稱取自定稿的示意資料。 */
    async getBookingItems() {
      await delay(60);
      return [
        { name: "精緻主廚特餐", subs: ["早午時光", "精緻午茶", "晚安佳餚"] },
        { name: "自助吧吃到飽", subs: ["點心自助吧", "499超值吃到飽", "699海陸尊榮雙響"] },
        { name: "星空酒吧", subs: ["舞池暢飲", "獨立包廂"] },
        { name: "如果項目字數太多太長就用點點點點點點顯示", subs: [] },
      ];
    },

    async getUnitGroups() {
      await delay(60);
      return [
        { name: "群組G1", units: [
          { name: "單位A2", cap: "1-2" }, { name: "單位B2", cap: "1-2" },
          { name: "單位A2", cap: "1-4" }, { name: "單位B2", cap: "1-4" },
          { name: "如果字數太多了", cap: "5-6" },
        ]},
        { name: "預設群組", units: [
          { name: "單位A2", cap: "1-4" }, { name: "單位B2", cap: "1-4" },
          { name: "單位C2", cap: "1-2" }, { name: "單位D3", cap: "1-2" },
          { name: "單位E2", cap: "5-6" }, { name: "單位D4", cap: "1-2" },
          { name: "單位D2", cap: "1-2" },
        ]},
        { name: "字太多群組", units: [
          { name: "字太多的話", cap: "1-2" }, { name: "單位D2", cap: "1-2" },
          { name: "單位D3", cap: "1-2" }, { name: "單位D4", cap: "1-2" },
          { name: "單位E2", cap: "5-6" },
        ]},
      ];
    },

    async getFloors() {
      await delay(80);
      return JSON.parse(JSON.stringify(FLOORS));
    },

    async getShop() {
      await delay(80);
      return {
        name: "找活燒烤-北門店",
        groups: GROUPS,
        smsPoints: 1000,
        posSyncing: true,
        /* 新增預約的三種擋下情境（定稿 2-1-1 有各自一張） */
        closedAllDay: false,
        closedItem: false,
        hasUnits: true,
        hasDuplicate: true,
        /* 修改抽屜的訂金說明（定稿 3-1-2）。mode: "none" | "prepay" | "card_auth" */
        deposit: {
          mode: "prepay",
          prepayHint: "顧客可透過轉帳、信用卡、超商代碼完成訂金支付",
          cardAuthHint: "顧客需完成信用卡授權，若顧客因故爽約，您可於授權期限內請款收取違約金",
        },
      };
    },

    async getBookings() {
      await delay(120);
      return BOOKINGS.map(clone);
    },

    async getStatusCounts() {
      await delay(0);
      const n = (k) => BOOKINGS.filter((b) => b.status === k).length;
      return STATUS.map((s) => ({ ...s, count: s.key === "confirmed" ? 12
        : s.key === "arrived" ? 4 : s.key === "seated" ? 8 : n(s.key) }));
    },

    async updateBooking(payload) {
      await delay(400);
      if (payload.phone === ERROR_PHONE) {
        return { ok: false, error: "PHONE_BLOCKED", message: "此手機號碼無法使用，請確認後再試一次" };
      }
      const i = BOOKINGS.findIndex((b) => b.id === payload.id);
      if (i < 0) return { ok: false, error: "NOT_FOUND", message: "找不到這筆預約" };
      BOOKINGS[i] = { ...BOOKINGS[i], ...payload, updatedAt: "2022-01-01 12:00" };
      return { ok: true, booking: clone(BOOKINGS[i]) };
    },
  };
})();

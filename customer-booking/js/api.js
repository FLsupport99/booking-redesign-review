/* API adapter — 上線時只改這一檔：把 mock 實作換成真端點。
   介面（與畫面解耦）：
     api.getShop()                    → Shop
     api.getAvailability(query)      → { slots: [{ time, available }] }
     api.createBooking(payload)      → { ok, booking } | { ok:false, error:'FULL'|'BLOCKED' }
     api.cancelBooking(code)         → { ok }
   換真 API 範例：
     async getShop() { return (await fetch(`${BASE}/shops/${handle}`)).json(); }
*/
const api = (() => {
  const delay = (ms) => new Promise((r) => setTimeout(r, ms));

  const SHOP = {
    name: "找活燒烤-北門店",
    /* 空狀態開關（定稿 1-1 的 未開放預約／Null／隱藏人數選項 三張）
       reservationOpen:false → 側邊卡變「尚未開放預約」且不顯示選擇區
       showPartySize:false   → 不顯示人數欄
       needsReview:true      → 送出後進入「待審核」 */
    reservationOpen: true,
    showPartySize: true,
    needsReview: false,
    branches: ["找活燒烤-北門店", "找活燒烤-南港店", "找活燒烤-西門店"],
    address: "台北市信義區松高路11號2樓",
    mapUrl: "https://maps.google.com/?q=台北市信義區松高路11號2樓",
    phone: "02-2345-6789",
    hours: "每週一～五 11:00-22:00",
    social: { line: "#", instagram: "#", facebook: "#", web: "#" },
    description:
      "以台灣在地食材打造的創意料理，每日精選時令菜色，提供輕鬆愉快的用餐體驗。無論是家庭聚餐或商務宴客，都能找到適合的座位。",
    announcement: "限時優惠活動：三人同行一人免費",
    notice: [
      "僅接受現金付費。",
      "低消$250/人 （含8歲以上兒童一樣需符合店家低消之規則）。",
      "餐廳內空間擁擠局限，如需使用兒童座椅、餐具，請於預約時備註。",
      "訂位人數最多：6位。超過人數請來電詢問。",
      "用餐時間為90分鐘（依訂位時間算起，如無下一組訂位則無時間限制到打烊）。",
      "訂位保留15分鐘，15分鐘後有現場客人我們將讓出您的訂位桌。",
      "如遇天災或不可抗之因素或意外（如颱風、停水、停電），或無法履行上述之約定，我們將保留取消或更改預約之權利。",
    ],
    otherInfo: ["餐點服務", "內部環境", "店內交易方式", "停車資訊", "交通資訊", "其他說明"],
    party: { min: 1, max: 6, hint: "可接受 1-6 位訂位（含大人與小孩）", over: "*超過 6 人的訂位，請使用電話預約" },
    /* 訂金規則。mode: "none" | "prepay"（預先付款 1-3a）| "card_auth"（信用卡授權 1-3b）
       改 mode 就會切換預約頁的紅字提醒、表單的須知區塊與摘要卡金額列。 */
    deposit: {
      mode: "prepay",
      threshold: 1, perPerson: 100,
      text: "1人以上，需支付訂金：NT$100/人",
      textAlt: "1人含以上，需支付訂金：NT$100/人",   // 定稿在項目模式用這句
      summary: "NT$100/人",
      termsTitle: "訂金規則說明",
      terms: [
        "要求訂金：NT$100/人。",
        "請於 30 分鐘內完成訂金付款，逾時系統將自動取消預約。",
      ],
      notice: [],
      summaryWarn: "",
    },
    /* 1-3b 信用卡授權：把 deposit 換成這組即可（文案取自定稿 訂金規則_信用卡授權說明） */
    depositCardAuth: {
      mode: "card_auth",
      threshold: 1, perPerson: 100,
      text: "1人以上，需授權信用卡預綁訂金：NT$100/人",
      summary: "NT$100/人",
      // 預約頁：人數欄下方的紅字提醒
      notice: [
        "商家將以透過授權信用卡號的方式預綁訂金做為預約保證，但絕對不會向您先收取任何費用。",
        "若您當天未如期抵達，或是無故取消預約，商家才能對您綁定的信用卡進行扣款，收取取消費用。",
      ],
      // 填寫資訊頁：送出前的須知區塊
      termsTitle: "信用卡授權預綁訂金須知",
      terms: [
        "請於30分鐘內完成信用卡授權。超過期限未完成，預約將自動取消。",
        "信用卡授權的目的僅作為預約保證，此階段不會向您收取任何費用。",
        "授權金額即為本次預約的訂金保證金額。",
        "授權過程中，會進行一筆 1 元測試交易以確認卡片是否有效，不會實際扣款，敬請放心。",
        "未出席或非規定期限內取消預約，商家才得透過已授權的信用卡收取費用。",
        "若對於扣款有任何疑慮，請與商家進行聯繫。",
      ],
      summaryWarn: "*若未如期出席商家將有權進行扣款收取取消費用",
    },
    showLineFriendReminder: true,
    /* ASSET_BASE 讓 sections/ 底下的單段落檔案也能吃到同一批圖 */
    menus: [1, 2, 3, 4].map((i) => `${window.ASSET_BASE || ""}assets/menu${i}.png`),
    /* 預約項目（mode=service 用 items、mode=hier 用 items+children） */
    items: [
      { id: "chef", name: "精緻主廚特餐", children: [
        { id: "brunch", name: "早午時光" },
        { id: "tea", name: "精緻午茶" },
        { id: "dinner", name: "晚安佳餚" },
      ]},
      { id: "buffet", name: "自助吧吃到飽", children: [
        { id: "buffet-lunch", name: "午間自助吧" },
        { id: "buffet-dinner", name: "晚間自助吧" },
      ]},
      { id: "bar", name: "星空酒吧", children: [
        { id: "bar-set", name: "微醺套餐" },
      ]},
    ],
  };

  /* mock 時段表：18:30 留給「預約已滿」demo，12:00/12:30/18:00/19:00 為不可選 */
  const SLOTS = [
    "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30",
    "13:00", "13:30", "14:00", "14:30", "17:30", "18:00", "18:30",
    "19:00", "19:30", "20:00", "20:30", "21:00", "22:00", "23:00",
    "00:00", "01:00", "02:00",
  ];
  const UNAVAILABLE = new Set(["12:00", "12:30", "18:00", "19:00"]);

  let fullDemoDone = false; // 18:30 第一次送出回 FULL，之後成功（demo 用）

  return {
    /* 空狀態與訂金模式可用網址參數切換，方便逐張對定稿：
         ?state=closed     未開放預約
         ?state=null       店家什麼都沒設定
         ?state=no-party   隱藏人數選項
         ?state=review     送出後進入待審核
         ?deposit=card_auth|none  換訂金規則（預設 prepay） */
    async getShop() {
      await delay(120);
      const q = new URLSearchParams(location.search);
      const shop = { ...SHOP };
      const dep = q.get("deposit");
      if (dep === "card_auth") shop.deposit = SHOP.depositCardAuth;
      if (dep === "none") shop.deposit = { mode: "none", text: "", summary: "", terms: [], notice: [] };
      switch (q.get("state")) {
        case "closed": shop.reservationOpen = false; break;
        case "no-party": shop.showPartySize = false; break;
        case "review": shop.needsReview = true; break;
        case "null":
          Object.assign(shop, {
            branches: [shop.name], announcement: "", notice: [], otherInfo: [],
            menus: [], social: {}, description: "",
            deposit: { mode: "none", text: "", summary: "", terms: [], notice: [] },
          });
          break;
      }
      return shop;
    },

    async getAvailability({ date, adults, children }) {
      await delay(200);
      return { slots: SLOTS.map((t) => ({ time: t, available: !UNAVAILABLE.has(t) })) };
    },

    async createBooking(payload) {
      await delay(1400);
      if (payload.time === "18:30" && !fullDemoDone) {
        fullDemoDone = true;
        return { ok: false, error: "FULL" };
      }
      const dep = SHOP.deposit;
      const needPay = dep.mode && dep.mode !== "none";
      const booking = {
        code: String(Math.floor(10000 + Math.random() * 90000)),
        ...payload,
        /* 三個獨立欄位組合出定稿的十種狀態，不要用一個扁平 enum */
        lifecycle: "active",                                   // active | cancelled | ended
        review: SHOP.needsReview ? "pending" : null,           // pending | approved | null(免審核)
        payment: needPay
          ? { kind: dep.mode, state: "pending", amount: dep.perPerson * (payload.adults + payload.children),
              deadline: "2026-06-16 22:59", countdown: "29:59" }
          : null,
      };
      this._lastBooking = booking;
      return { ok: true, booking };
    },

    /* 完成付款／完成信用卡授權（前往付款、授權信用卡兩顆按鈕） */
    async settlePayment(code) {
      await delay(1200);
      const b = this._lastBooking;
      if (b) b.payment = { ...b.payment, state: "done" };
      return { ok: true, booking: b };
    },

    async cancelBooking(code) {
      await delay(300);
      return { ok: true };
    },

    /* 1-2 其他分店可預約時間 */
    async getBranchAvailability({ date, adults, children }) {
      await delay(250);
      return {
        branches: SHOP.branches.map((name, i) => ({
          name,
          address: SHOP.address,
          slots: SLOTS.slice(0, 10).map((t, j) => ({
            time: t, available: !UNAVAILABLE.has(t) && (i + j) % 7 !== 3,
          })),
        })),
      };
    },

    /* 1-6 查詢預約：先比對剛送出的那筆；查不到就用下表的固定測試碼，
       每個代碼對應定稿「查詢結果」的一種狀態，方便逐張比對。手機一律 0987654321。 */
    _lastBooking: null,
    _demoStates: {
      30690: { label: "預約成功" },
      30691: { label: "已取消", lifecycle: "cancelled" },
      30692: { label: "已結束", lifecycle: "ended" },
      30693: { label: "待審核", review: "pending" },
      30694: { label: "待付款", payment: { kind: "prepay", state: "pending" } },
      30695: { label: "付款完成", payment: { kind: "prepay", state: "done" } },
      30696: { label: "待綁卡", payment: { kind: "card_auth", state: "pending" } },
      30697: { label: "綁卡完成", payment: { kind: "card_auth", state: "done" } },
      30698: { label: "待審核+待付款", review: "pending", payment: { kind: "prepay", state: "pending" } },
      30699: { label: "待審核+待綁卡", review: "pending", payment: { kind: "card_auth", state: "pending" } },
    },
    async lookupBooking({ phone, code }) {
      await delay(400);
      const b = this._lastBooking;
      if (b && b.phone === phone && b.code === code) return { ok: true, booking: b };

      const demo = this._demoStates[code];
      if (phone === "0987654321" && demo) {
        const base = {
          code, dateLabel: "2026/06/16 星期二", time: "18:30",
          adults: 2, children: 2, name: "廖文強", phone, email: "test@mail.com",
          q1: "顧客填寫答案", q2: "答案A、答案B", q3: "大人x1", note: "顧客填寫備註內容",
          lifecycle: "active", review: null, payment: null,
        };
        const p = demo.payment
          ? { ...demo.payment, amount: 400, deadline: "2026-06-16 22:59", countdown: "29:59" }
          : null;
        return { ok: true, booking: { ...base, ...demo, payment: p, label: undefined } };
      }
      return { ok: false, error: "NOT_FOUND" };
    },

    /* 1-4 修改預約 */
    async updateBooking(payload) {
      await delay(1000);
      return { ok: true, booking: { ...payload } };
    },
  };
})();

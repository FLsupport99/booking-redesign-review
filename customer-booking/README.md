# booking-pilot — 顧客預約頁三種模式（可上線型 HTML）

Figma「2026 May. 顧客預約頁改版」定稿的**真 DOM** 實作：純 HTML/CSS/JS、零依賴、雙擊就能開。
不是圖片＋熱區的示意原型——真的 input、真的 datepicker、真的驗證與 loading，資料層抽成 API adapter，接上真端點即可運作。

## 三個交付檔（各代表一種預約模式）

| 檔案 | 模式 | 差異 |
|---|---|---|
| `1-基本人數預約.html` | ① 基本人數預約 | 只選人數、日期、時段 |
| `2-服務項目預約.html` | ② 服務項目預約 | 先選預約項目，再選人數/日期/時段 |
| `3-階層項目預約.html` | ③ 階層項目預約 | 選父層項目 → 選子項目，再選人數/日期/時段 |

`index.html` 是入口頁，列出三個模式與逐段檢視連結。

每個模式檔內含完整 1-1 ~ 1-7：

| 段落 | 內容 | 在畫面上怎麼進去 |
|---|---|---|
| 1-1 | 顧客預約頁 | 開檔即是 |
| 1-2 | 查看其他分店時段 | 「沒有適合的時段？看看其他分店」 |
| 1-3 | 填寫資訊（含預約已滿分支） | 選好時段 →「填寫預約資訊」 |
| 1-4 | 修改預約 | 成功頁 →「修改預約」 |
| 1-5 | 取消預約 | 成功頁 →「取消預約」 |
| 1-6 | 查詢預約 | 頁首「查詢預約」 |
| 1-7 | 中英切換 | 頁首「EN / 繁中」 |

## 逐段比對用的單檔（`sections/`）

`sections/<mode>-<section>.html` 共 21 個，同一份程式碼用 `window.SECTION` 把畫面快轉到該段落起點，
方便和工程師手刻的檔案一段一段對照。例：`sections/hier-1-4.html` = 階層模式的修改預約頁。

## Demo 劇本

- 時段 **18:30** 第一次送出會回「預約已滿」popup（後端滿位分支），其他時段直接成功
- `12:00 / 12:30 / 18:00 / 19:00` 為不可選時段
- 查詢預約測試碼：手機 `0987654321`、代碼 `30690`（或查剛送出的那筆）
- 表單空白直接送出可看驗證錯誤樣式

## 檔案結構

| 路徑 | 內容 |
|---|---|
| `src/template.html` | **唯一的畫面來源**，三個模式檔與 21 個單段落檔都從這裡產生 |
| `tools/build.mjs` | 產生器：`node tools/build.mjs` |
| `tools/smoke.html` | 一次載入 24 個檔案檢查 console error／破圖／預期畫面（瀏覽器打開即跑） |
| `tools/figma-copy-check.mjs` | 文案稽核：從 Figma 抓定稿文字逐條比對實作 |
| `css/tokens.css` | Design tokens——色彩/字級/圓角/陰影抽自 Figma variables，畫面不出現字面色值 |
| `css/main.css` | 版面與元件樣式（hover/focus/disabled/error 狀態、RWD 斷點 760px） |
| `js/api.js` | **API adapter**——目前是 mock；上線只改這一檔 |
| `js/app.js` | 狀態機與渲染：模式切換、項目/子項目、人數、datepicker、時段、驗證、view 切換 |
| `assets/` | 從 Figma 匯出的 icon 與圖（菜單／分享照為示意圖，正式從 API 來） |
| `docs/` | 與 Figma 原稿比對用的實測截圖 |

> 改畫面請改 `src/template.html` 後跑 `node tools/build.mjs`，不要直接改根目錄那三個產出檔。

## 接真 API

`js/api.js` 定義下列介面，畫面只認這層：

```js
api.getShop()                  // 店家資料（含 items：預約項目／子項目）
api.getAvailability(query)     // { slots:[{time, available}] }；query 含 date/adults/children/itemId/subItemId
api.createBooking(payload)     // { ok, booking } 或 { ok:false, error:'FULL' }
api.updateBooking(payload)     // 1-4
api.cancelBooking(code)        // 1-5
api.lookupBooking({phone,code})// 1-6
api.getBranchAvailability(q)   // 1-2
```

把 mock 實作換成 `fetch(BASE + ...)` 即可。**欄位名需由後端定案後對齊**——這是上線前唯一未決的部分。

## 與工程師手刻版（`menushop_demo`）的已知差異

2026-08-06 逐頁比對後對齊的項目：項目模式的顯示時機（選到項目前不顯示人數/日期/時段）、
hash 路由、預約成功的 LINE 加好友 popup、訂金規則三處連動、手機版頁首搜尋鈕收成 icon。

仍不同、且**我方照定稿、對方需修正**的文案：可預約時段（對方寫時間）、上午（早上）、
星期二（週二）、MENU美食客分享（美食家）、到店提醒句、必填星號與頁尾的多餘空格、
表單殘留 placeholder「Text」。

架構差異（不需對齊）：對方用 pathname 路由需要 SPA fallback；本專案是靜態檔，改用 hash 路由。

## 目前範圍外

- 1-3a／1-3b 的後續狀態（待審核、待付款、待綁卡的結果頁）；訂金規則本身已可切換
- 1-6 查詢結果的完整狀態機（已做：成功／已取消；未做：待審核、待付款、已結束等）
- 空狀態：未開放預約、Null（店家什麼都沒設定）、隱藏人數選項
- 1-7 只翻譯 UI 字串，店家內容（公告、須知）需由 API 提供雙語
- LINE QR 為裝飾假碼

## 驗收流程（改完一定要跑完三關）

改任何畫面或文案後，依序跑：

| # | 關卡 | 指令／做法 | 過關標準 |
|---|---|---|---|
| 1 | 重新產生 | `node tools/build.mjs` | 24 個檔案產出無誤 |
| 2 | **文案對定稿** | `node tools/figma-copy-check.mjs` | `=== 全部相符 ===` |
| 3 | 流程與破圖 | 瀏覽器開 `tools/smoke.html` | `24/24 passed` |

再加一關人工：**逐頁對照 Figma 原稿截圖**（`../gallery_assets/`、`../modes_assets/`），
確認版面結構與顯示時機。目前已建立的對照證據在 `docs/`。

### 為什麼要有第 2 關

第一版是「看圖重畫」，肉眼會漏掉單字級落差（可預約**時段**寫成**時間**、**上午**寫成**早上**、
**美食客**寫成**美食家**、全形／半形斜線）。`figma-copy-check.mjs` 直接從 Figma REST 抓 8 個代表節點的
所有文字，逐條檢查實作是否使用同一個字，抓的就是這類錯誤。

刻意不同的字要寫進腳本的 `ACCEPTED`（附理由）；店家自填內容、假資料寫進 `IGNORE_PATTERNS`。
**不要為了讓它變綠而亂加豁免**——每一條豁免都要有理由。

### spec 從哪裡來

一律用 Figma MCP `get_design_context` 取節點的實際字級／間距／色碼，**不要看圖目測重畫**；
定稿 PNG 只用來取樣語意色（`--danger #CE4949`、`--accent-orange #EB5514`）與核對版面。

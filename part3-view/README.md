# Part 3 ② 預約管理視圖 — 時間軸（可上線型 HTML）

Figma「2026 Jul. 預約系統操作優化」Part3 自建預約定稿（file `XphLPcM7qUdcVO6EwjYJy9`）的**真 DOM** 實作：
純 HTML/CSS/JS、零依賴、雙擊就能開。資料層抽成 API adapter，接上真端點即可運作。

## 為什麼不是接 `sim.html`

`sim.html` 已經有 Part3 的模擬器，但它是**設計 review 用的簡化版**。
用本專案的文案稽核對它跑過一次（定稿 686 條）：扣掉假資料與設計註記後，
還缺約 30 條 UI 文案，而且集中在三整塊功能——**未儲存提醒 modal、表單驗證訊息、訂金說明區塊**，
另缺一組預約狀態動作（接受／請款／商家取消／交換／選位／結帳完成／儲存顧客）。

拿它當交付基礎等於一開始就欠三塊，因此另刻一份。
`sim.html` 只當結構參考，**不當 ground truth**——token 值一律回 Figma 校正。

## 本階段範圍

3-1-1 時間軸（3 frames）＋ 3-1-2 時間軸_修改預約（6 frames）。
空間圖（3-2）、清單（3-3-1／3-3-2，含 8 張手機版）尚未開始。

| 檔案 | 內容 |
|---|---|
| `1-時間軸.html` | 交付檔 |
| `sections/timeline-<state>.html` | 逐狀態快轉檔（popover／modify／collapsed／error／unsaved／done） |

## Demo 劇本

- 點右側顧客卡片的 ✎ 開修改抽屜；點時間軸區塊開 popover
- 抽屜內**有變更**才會在關閉時跳「尚未儲存這筆預約」；沒變更直接關
- 手機號碼填 `0900000000` 再儲存 → Error toast
- 儲存成功 → 「已修改預約」toast，右側卡片外框在修改期間是黃色粗框（定稿的 focus 樣式）

## 檔案結構

| 路徑 | 內容 |
|---|---|
| `src/template.html` | **唯一的畫面來源**，交付檔與段落檔都從這裡產生 |
| `verify.config.mjs` | 驗收管線的單一設定檔（產出結構／Figma 節點／豁免／斷言選擇器） |
| `css/tokens.css` | Design tokens，抽自 Figma variables，畫面不出現字面色值 |
| `css/main.css` | 版面與元件 |
| `js/api.js` | **API adapter**——目前是 mock；上線只改這一檔 |
| `js/app.js` | 狀態機與渲染 |
| `tests/smoke.spec.mjs` | 第 3 關斷言 |

> 改畫面請改 `src/template.html` 後跑 `npm run build`，不要直接改產出檔。

## 驗收流程

第一次先 `npm install && npx playwright install chromium`，之後：

```sh
npm run verify        # build → copy-check → smoke
```

| # | 關卡 | 過關標準 |
|---|---|---|
| 1 | 重新產生 | `built 7 files` |
| 2 | 文案對定稿 | `=== 全部相符 ===`（定稿 340 條） |
| 3 | 行為與顯示時機 | `14 passed` |

第 4 關人工三視角走查見 [`../customer-booking/REVIEW-CHECKLIST.md`](../customer-booking/REVIEW-CHECKLIST.md)。

腳本在 `../verify-kit/`，與 `customer-booking/` 共用；本專案只有 config 與 tests。

### 顯示時機（本階段的 ⭐）

定稿 3-1-2 只有 5/17 個 section 帶 `_Start` 後綴，但 `../tools/manifest_p3.json` 記了座標，
實測 **同列最左 = 初始狀態**（`3-1-2_Start` 在 x=100、非 Start 版在 x=1164）。
據此判定：**3-1-2 的 base state 就是一般時間軸，修改抽屜要點編輯才出現**，已寫成斷言。

新增畫面或狀態時，必須同步補上對應的顯示時機斷言。

## ⚠️ 待設計確認

定稿畫布上有 **9 條設計自己留的修改註記**，其中 5 條落在本階段刻到的地方
（寫在 `verify.config.mjs` 的 `ACCEPTED`，附理由）：

> 預約狀態卡片樣式、字太多、把「秒」拿掉、加底色、「完成」時間換行

目前照定稿**現況**實作。若那些是待辦而非「已完成、註記忘了刪」，這幾處要重做。
（其中「外框變黃色加粗，表示 focus」已確認做進定稿了。）

另外兩處與 FL-Agent 前端規範（`ai-ui-rules.md`）不同，本專案照定稿，見 `css/tokens.css` 檔頭：

- 定稿字級 token 帶 letter-spacing 3%～5%（規範是繁中內文不設）
- Caption／Button-sm／H3 的 line-height 是 100%（規範是內文 ≥1.4）

## 已知差異

定稿 3-3-1 清單那張的左側主導航是**深色**，時間軸與空間圖是**淺色**。
本階段照時間軸做淺色；等清單批次時要跟設計確認哪個是最新。

# 接力任務：後台模擬器「時段設定」模組

> ✅ 2026-07-23 更新：「第一批 基本人數 3-x」已完成並上線（見 sim.html 的 viewSlots/viewSlotForm）。
> 剩餘＝下方三個批次，各自獨立、可平行；每批的既有程式範本就是 3-x 的實作。

> 給任何接手的 session／cloud agent。目標：把 `sim.html` 的模擬器加上「預約時段與規則」模組，
> 手感標準＝現有「預約單位」模組（真的能打字、儲存、防呆、假資料會動）。

## Repo 內既有材料（不需要 Figma 權限）

| 材料 | 位置 |
|---|---|
| 設計稿 PNG（時段設定全部畫面） | `../algo_assets/`，檔名＝node id；對照 `../algo_assets/manifest.json`（id→畫面名稱，3-x=基本人數、4-x=服務項目、5-x=階層項目、6-x=總量控管） |
| 每個畫面的文字層原文（標籤/placeholder/錯誤訊息） | `tools/time_texts.json`（key=`畫面名稱\|nodeId`） |
| 元件 CSS / mock API / router 模式 | `../sim.html`（照抄「預約單位」模組的寫法） |
| 月曆、timepicker、時段重疊檢查等現成互動元件 | `../exception_rules.html`（5 月手工 prototype，可拆用） |

## 範圍（第一批：基本人數預約 3-x）

1. **#/slots 清單頁**（3-1 預約時段-基本人數預約）：時段規則 rows＋展開明細、查看預約單位 modal、Null 空狀態
2. **新增時段**（3-2）：名稱自動流水；「選擇時間範圍」（起訖＋間隔→自動計算時段 pills 預覽、重複時段 error 3-2a）；「自訂時間」（timepicker＋加入時間清單、重複 error 3-2b）；「自訂預約單位」（群組→單位勾選樹＋總容納人數自動加總 3-2c）；輸入錯誤 states 照設計
3. **編輯時段**（3-3）＋**刪除時段 popup**（3-4）
4. 資料模型建議：`db.slots = [{id,name,type:'auto'|'custom',start,end,interval,times[],unitScope:'all'|[unitIds],cap}]`，容量與「預約單位」模組的 units 連動
5. viewRules 的「預約時段與規則」row 接到 #/slots

之後批次：4-x 服務項目（多一層項目清單管理）、5-x 階層項目（父子兩層）、6-x 總量控管（人數上限制）。

## 規範

- 文案一律用 `time_texts.json` 原文，不要自己改寫
- 驗證：`python3 -m http.server` 起本地站，實際走完 CRUD＋錯誤狀態，無 console error 才算完成
- RWD 斷點 760px，手機版照設計 390 版型
- 直接 commit+push main（此 repo 慣例），commit 訊息照 git log 風格


## 批次規範（雲端 routine 專用，三批共通）

**啟動即自證**：開工第一件事，在 `tools/RUN_LOG.md` append 一行 `batch <N> started <UTC時間>`，立刻 commit + push。push 失敗就改開 PR；連 PR 都失敗，把完整錯誤訊息寫進最終回覆後再繼續做（至少留下診斷）。

**里程碑推送**：每完成一個畫面群就 commit + push 一次（清單頁一次、表單一次、驗證修正一次），不要憋到最後。push 被拒就 `git pull --rebase` 再推。

**共通實作原則**：
- 讀 sim.html 現況：`viewSlots`/`viewSlotForm` 是 3-x 的完整範本；路由在 `route()`；mock api 與 helpers（slotTimes/slotCap/slotConflicts）都可複用或泛化
- 依 `db.mode` 分流：`#/slots` 進來後，basic→現有畫面；其他模式照各批次規格
- 設計稿：algo_assets/ ＋ manifest.json 查畫面；文案：tools/time_texts.json 照抄
- 驗證：node --check 抽出的 inline script（注意本機可能是舊 node，避免 ?? 與 optional chaining 之外的新語法——現有程式碼就是相容基準）＋逐流程推演
- 只改 sim.html 與 tools/RUN_LOG.md

## 批次 2：服務項目預約（4-x）

`db.mode==='service'` 時 `#/slots` 顯示「預約項目」層：
- 4-1 項目清單（含 Null、每項目顯示時段數）＋ 4-2 新增項目（名稱、重複名防呆）
- 4-3 編輯項目清單（排序/刪除、刪光提醒、儲存時提醒）＋ 4-4 編輯項目名稱（Form/Placeholder/錯誤/儲存提示）
- 4-5 每個項目自己的時段清單＋新增時段（沿用 3-x 表單，掛在 item 下）＋ 4-6 編輯/刪除時段
- 資料模型：`db.items = [{id, name, slots:[slotId...]}]`（或 slot 增加 itemId 欄位），時段表單邏輯全部複用

## 批次 3：階層項目預約（5-x）

同批次 2 但兩層：父層項目（5-1~5-4）＋子項目（5-5、5-6），時段掛在「父層+子項目」組合（5-7~5-9）。
資料模型建議 `db.items`（父）＋ `db.subitems = [{id, pid, name}]`。畫面照 5-x 設計稿。

## 批次 4：總量控管（6-x）

`db.mode==='capacity'`：結構最接近 3-x，但「設定預約承接量」區塊改為**人數上限**（無預約單位勾選樹，6-2 設計稿為準），清單卡顯示上限而非單位數。大部分可從 3-x 表單刪改而來。

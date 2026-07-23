# 接力任務：後台模擬器「時段設定」模組

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

# 設計稿匯出／組頁管線（增量更新用）

流程（下次設計完工要整合時）：
1. 用 figma MCP `use_figma` 盤點目標頁面 section/frame（含 x,y,w,h），更新 `manifest_*.json`
   - 與 `../modes_assets/manifest.json`、`../algo_assets/manifest.json` 的 frames 比對，只處理新增/變更的 node
2. 匯出（擇一）：
   - **首選 REST**（2026-07-23 起可用）：`~/FL-Agent/FL-Salesapp/.env` 的 `FIGMA_TOKEN`（Ian 的 PAT），
     `GET /v1/images/:fileKey?ids=<逗號分隔多個id>&format=png&scale=1` → 批次拿 URL 下載；
     不吃 MCP 額度、無 4096px 限制。專案檔案清單：`GET /v1/projects/238052935/files`
   - 備援 MCP：`get_screenshot` 參數 `{maxDimension: 16384, contentsOnly: true}` → 回傳 URL 用 curl 下載
   - ⚠️ 不要用 `download_assets`：其匯出被硬限制在 4096px，超寬 section 會被縮圖
   - ⚠️ MCP 讀取額度：Pro 方案 200 次/天、15 次/分（use_figma/get_metadata/get_screenshot 都算）
   - section 輸出四周各多 40px 邊距（w+80），`build_galleries.py` 的 render_geometry 已處理
3. 裁切＋組頁：`uv run --with pillow python3 build_galleries.py`
   - 讀 scratchpad `exports2/sections|loose/*.png`（路徑寫在腳本開頭，重跑前調整）
   - 產出 assets png + gallery html + assets/manifest.json
4. commit + push → GitHub Pages 約 1 分鐘自動重建

備註：兩個來源 Figma 檔案
- AQilb21aXkXybY5c1wDFq8「2026 May. 顧客預約頁改版」（頁①已在 design_gallery、頁②③在 modes_gallery）
- AO8eUsYE6NQuELdiqGrG9E「2025 Oct. 系統架構演算法優化」（algo_gallery）

## 點擊式互動原型管線（2026-07-23 新增）

前提：設計師在 Figma 有拉 prototype 連線（實測密度：預約單位 81% 畫面有連線、例外 64%、預約模式只有回頭線 32%——太稀疏的模組做出來會像死路，先確認密度再做）。

1. 抽連線：`node tools/extract_proto.js <fileKey> <pageNodeId> <manifest路徑> <groupKey> <輸出.json>`
   （吃 FL-Salesapp/.env 的 FIGMA_TOKEN，REST 不耗 MCP 額度；輸出含每畫面熱區%座標與目標）
2. 產播放器：`python3 tools/build_proto.py <proto.json> <標題> <assets目錄名> <輸出.html>`
   （畫面圖直接用 gallery 匯好的 assets PNG，先確保該模組的圖都在）
3. 頁首/入口加連結 → commit + push

試作品：proto_unit.html（預約單位）。proto_mode.json / proto_exc.json 已抽好備用。

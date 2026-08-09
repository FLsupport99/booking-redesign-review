# assets/ 來源

| 檔案 | 來源 | 為什麼 |
|---|---|---|
| `fn-*.svg` | Figma REST（`npm run icons`，node id 在 `verify.config.mjs` 的 `figma.ICONS`） | 這幾個是本檔案內的 instance，REST 匯得出來 |
| `nav-*.svg`、`logo.png` | `get_design_context`（節點 `496:45019`）回傳的資產 URL | 導航列圖示的 component master 在**外部 library**，REST `/v1/images` 一律回 `null`，只有這條路拿得到 |

⚠️ `get_design_context` 的資產 URL **7 天過期**，所以檔案直接落地進 repo，不要改成遠端連結。
要重抓就重新對 `496:45019` 叫一次 `get_design_context`。

⚠️ 這些 SVG 的顏色是 Figma 烘進去的（active `fill="white"`、inactive 再加 `fill-opacity="0.6"`）。
**不要改成 `currentColor`**：透過 `<img>` 載入時無法繼承頁面 color，
帶 `<mask fill="white">` 的圖示（顧客、設定）會整張變透明。要 hover 換色請改 inline SVG。

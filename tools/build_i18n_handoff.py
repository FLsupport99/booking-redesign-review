#!/usr/bin/env python3
"""
產生 i18n.html — 改版 UI 文案交付／前端說明頁。

資料來源：
  ~/FL-Agent/Shop-translate/output/給前端_既有字串改名清單.tsv
版型：沿用 index.html / designs.html 的 token（#f4f5f6 底、#3FBA88 主色、PingFang TC）
用法：python3 tools/build_i18n_handoff.py
"""
import csv, html, os, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = pathlib.Path(os.path.expanduser("~/FL-Agent/Shop-translate/output/給前端_既有字串改名清單.tsv"))
OUT = ROOT / "i18n.html"
SHEET = "https://docs.google.com/spreadsheets/d/1qSVE3zADY7fw4FpSF95oA_WLEPRoF9WstBlvu89M0ZI/"

rows = list(csv.DictReader(SRC.open(encoding="utf-8"), delimiter="\t"))
rename = [r for r in rows if "決策1" in r["依據"]]
spell = [r for r in rows if "決策5" in r["依據"]]

def esc(s): return html.escape(str(s or ""))

def tbl(items):
    out = []
    for r in items:
        out.append(
            f'<tr><td><code>{esc(r["i18n key"])}</code></td>'
            f'<td>{esc(r["現行中文"])}</td><td>{esc(r["現行英文"])}</td></tr>'
        )
    return "\n".join(out)

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"PingFang TC","Noto Sans TC",sans-serif;background:#f4f5f6;color:#222;
     line-height:1.75;padding:40px 20px 64px;-webkit-font-smoothing:antialiased}
.wrap{max-width:860px;margin:0 auto}
.hd{text-align:center;margin-bottom:36px}
.hd h1{font-size:24px;font-weight:700;line-height:1.4}
.hd p{font-size:14px;color:#888;margin-top:8px}
section{background:#fff;border:1px solid #e5e5e5;border-radius:14px;padding:26px 28px;margin-bottom:20px}
section > h2{font-size:17px;font-weight:600;margin-bottom:14px}
section > h2 .n{color:#29A379;margin-right:8px}
h3{font-size:14px;font-weight:600;margin:20px 0 8px}
p,li{font-size:14px;color:#444}
ul,ol{margin:8px 0 8px 20px}
li{margin-bottom:4px}
table{width:100%;border-collapse:collapse;margin:12px 0;font-size:13px;font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #eee;vertical-align:top}
th{font-weight:600;color:#666;background:#fafafa;white-space:nowrap}
td:first-child{white-space:nowrap}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;
     background:#f4f5f6;border-radius:4px;padding:1px 5px;color:#29A379;word-break:break-all}
pre{background:#f9f9f9;border:1px solid #eee;border-radius:8px;padding:14px 16px;overflow-x:auto;margin:10px 0}
pre code{background:none;padding:0;color:#333;font-size:12.5px;line-height:1.7}
.note{background:#ECF8F3;border-left:3px solid #3FBA88;border-radius:0 8px 8px 0;padding:12px 16px;margin:12px 0;font-size:13.5px}
.warn{background:#fdf4e8;border-left:3px solid #F8BA4C;border-radius:0 8px 8px 0;padding:12px 16px;margin:12px 0;font-size:13.5px}
a{color:#29A379}
details{margin-top:12px;border-top:1px solid #eee;padding-top:12px}
summary{cursor:pointer;font-size:13.5px;color:#29A379;font-weight:500;list-style:none}
summary::-webkit-details-marker{display:none}
summary::before{content:"▸ ";}
details[open] summary::before{content:"▾ ";}
.tblwrap{overflow-x:auto}
.back{display:block;text-align:center;margin-top:32px;font-size:13px;color:#888;text-decoration:none}
.back:hover{color:#29A379}
footer{margin-top:28px;font-size:12px;color:#aaa;text-align:center;line-height:1.8}
@media(max-width:640px){body{padding:24px 14px 48px}section{padding:20px 18px}}
"""

BODY = f"""
<div class="wrap">
<div class="hd">
  <h1>改版 UI 文案交付 — 前端說明</h1>
  <p>Part 1–3 中英對照表怎麼看、i18n key 怎麼處理</p>
</div>

<section>
  <h2><span class="n">1</span>這次交付三個分頁</h2>
  <p>全部在 Google Sheet「MENU店+ 後台功能與翻譯清單_2026」：
     <a href="{SHEET}" target="_blank" rel="noopener">開啟試算表 →</a></p>
  <div class="tblwrap"><table>
    <tr><th>分頁</th><th>改版範圍</th><th>列數</th><th>i18n key 欄</th></tr>
    <tr><td><code>V3 設定_預約</code></td><td>Part 1：預約模式／單位／時段／例外規則</td><td>267</td><td>已填 21 列</td></tr>
    <tr><td><code>V3 預約前台</code></td><td>Part 2：顧客預約頁</td><td>321</td><td>全空（見第 5 節）</td></tr>
    <tr><td><code>V3 後台操作優化</code></td><td>Part 3：自建預約／候位／Settings</td><td>230</td><td>已填 101 列</td></tr>
  </table></div>
</section>

<section>
  <h2><span class="n">2</span>「i18n key」欄是什麼</h2>
  <p>這個字串在 <code>menushop_frontend/src/locales/</code> 裡的位置，格式是
     <code>namespace:巢狀路徑</code>。例：<code>bookingSystem:buttonStatus.cancel</code></p>
  <pre><code>locales/zh/bookingSystem.json  →  buttonStatus.cancel = "取消"
locales/en/bookingSystem.json  →  buttonStatus.cancel = "Cancel"</code></pre>
  <p>namespace 就是 <code>src/i18n.js</code> 註冊的那 11 個：common / bookingSystem / settings /
     queueSystem / couponSystem / bulletinSystem / customer / messages / report / dashboard / time。</p>

  <h3>這一欄有值 vs 空白</h3>
  <div class="tblwrap"><table>
    <tr><th>狀態</th><th>意思</th><th>你要做的事</th></tr>
    <tr><td><b>有 key</b></td><td>前端已經有一模一樣的中文，而且英文核對過與表上一致</td>
        <td><b>直接沿用</b>，不用新增。元件改成 <code>t("該 key")</code> 即可</td></tr>
    <tr><td><b>空白</b></td><td>前端沒有這個字串</td>
        <td><b>新命名一個 key</b>，同時寫進 <code>zh/</code> 和 <code>en/</code>，再把 key 回填到這一欄</td></tr>
  </table></div>
  <div class="note">已填的 key 是拿表上中文去比對 <code>locales/zh/*.json</code> 撈出來的，並逐筆確認英文也相同才填。
    撈得到但英文對不上的一律留空。</div>

  <h3>「討論」欄寫「開新 key，勿沿用前端」的列</h3>
  <p>這些字串<b>中文跟現有 key 一樣，但語境不同，不可以沿用</b>：</p>
  <ul>
    <li><code>已儲存變更</code> — 前端現有的是 <code>customer:editCustomerPopup.editSuccess</code>，英文其實是 "Customer edited"（顧客編輯成功）</li>
    <li><code>要求訂金</code> — 前端現有的是 "Deposit Amount"，跟這裡的 "Deposit Required" 不是同一件事</li>
  </ul>
  <div class="warn">這幾列請另外開新 key，不要圖方便接舊的。</div>
</section>

<section>
  <h2><span class="n">3</span>欄位怎麼看</h2>
  <div class="tblwrap"><table>
    <tr><th>欄</th><th>意思</th></tr>
    <tr><td>B 中文名稱 / C 英語名稱</td><td><b>已上線</b>的文案。這次改版沒動到的維持原樣</td></tr>
    <tr><td>F 預計變更-中文 / G 預計變更-英文</td><td><b>這次要實作的新文案</b> ← 你要落檔的是這兩欄</td></tr>
    <tr><td>E 類型</td><td>UI 元件類型（按鈕／欄位／Toast／Pop-up 說明…），幫助判斷放哪個 namespace</td></tr>
    <tr><td>H 討論</td><td>註記與需注意事項</td></tr>
    <tr><td>I i18n key</td><td>見第 2 節</td></tr>
  </table></div>
  <p><b>你只需要處理 F/G 兩欄有值的列。</b>落檔完成後回填 I 欄，PM 會再把值搬到 B/C 正式欄。</p>
</section>

<section>
  <h2><span class="n">4</span>兩個格式約定</h2>
  <h3>變數</h3>
  <p>表上用單大括號中文變數名，落檔時轉成 i18next 格式並取英文變數名，中英取一致：</p>
  <pre><code>表上：  可接受 {{最少}}-{{最多}} 位訂位      Accepts {{min}}-{{max}} guests
落檔：  可接受 {{{{min}}}}-{{{{max}}}} 位訂位    Accepts {{{{min}}}}-{{{{max}}}} guests</code></pre>
  <h3>換行</h3>
  <p>表上的 <code>⏎</code> 代表原設計稿的換行，落檔時轉成 <code>\\n</code> 或依元件需要處理。</p>
</section>

<section>
  <h2><span class="n">5</span><code>V3 預約前台</code> 為什麼 key 全空</h2>
  <p>顧客預約頁不在 <code>menushop_frontend</code> 這個 repo（它是後台，路由都是 <code>/dashboard/*</code>）。
     我們沒有那份程式碼，比對不出 key。這個分頁請依實際 repo 結構自行命名並回填。</p>
</section>

<section>
  <h2><span class="n">6</span>已定案的用語規則</h2>
  <div class="tblwrap"><table>
    <tr><th>項目</th><th>規則</th></tr>
    <tr><td>星期</td><td>三字母 <code>Mon</code> / <code>Tue</code> / <code>Wed</code> / <code>Thu</code> / <code>Fri</code> / <code>Sat</code> / <code>Sun</code></td></tr>
    <tr><td>時間單位</td><td><code>hour</code> / <code>minute</code>（完整字，不用 h / min）</td></tr>
    <tr><td>確定</td><td><code>Confirm</code>（<b>不是 OK</b>）</td></tr>
    <tr><td>確認類 Pop-up</td><td>短句 <code>Confirm save?</code> / <code>Confirm delete?</code>，不用 "Are you sure you want to…"</td></tr>
    <tr><td>儲存／取消／編輯／刪除／變更</td><td><code>Save</code> / <code>Cancel</code> / <code>Edit</code> / <code>Delete</code> / <code>Change</code></td></tr>
    <tr><td>預約模式名稱</td><td>基本人數預約=<code>Basic</code>、服務項目預約=<code>Service</code>、階層項目預約=<code>Category</code>、總量控管=<code>Capacity</code></td></tr>
    <tr><td>肚肚 POS</td><td><code>dudoo</code>（小寫 d，沿用既有 19 處拼法）</td></tr>
    <tr><td>排隊組別</td><td><code>Queue Type</code>（不是 Queue Group）</td></tr>
    <tr><td>欄位</td><td>用「欄位」不用「標籤」（避免與系統標籤功能混淆）</td></tr>
  </table></div>
</section>

<section>
  <h2><span class="n">7</span>⚠️ 這次還要改「既有」字串</h2>
  <p>除了落新文案，有兩件事需要動到現有的 <code>locales/*.json</code>，共 {len(rows)} 筆。</p>

  <h3>7-1　桌位圖改名為空間圖／Table Map → Floor Plan（{len(rename)} 筆）</h3>
  <p>改版把這個功能從「桌位圖設定」改名為「空間圖」，因為它現在管的不只桌位。<b>中英文都要改</b>：</p>
  <ul>
    <li>中文：<code>桌位圖</code> / <code>座位圖</code> → <code>空間圖</code></li>
    <li>英文：<code>Table Map</code> → <code>Floor Plan</code></li>
  </ul>
  <div class="warn"><code>Table Configuration</code>（桌位設定）<b>維持不變</b> —— 那是設定個別桌位，跟空間圖是兩件事，別一起改掉。</div>
  <details><summary>展開 {len(rename)} 筆完整清單</summary>
    <div class="tblwrap"><table>
      <tr><th>i18n key</th><th>現行中文</th><th>現行英文</th></tr>
      {tbl(rename)}
    </table></div>
  </details>

  <h3>7-2　<code>Queueing</code> 拼法統一為 <code>Queuing</code>（{len(spell)} 筆）</h3>
  <p>現行兩種拼法混用（Queuing 17 筆、Queueing {len(spell)} 筆），統一成 <code>Queuing</code>。</p>
  <details><summary>展開 {len(spell)} 筆完整清單</summary>
    <div class="tblwrap"><table>
      <tr><th>i18n key</th><th>現行中文</th><th>現行英文</th></tr>
      {tbl(spell)}
    </table></div>
  </details>
</section>

<section>
  <h2><span class="n">8</span>回報</h2>
  <p>落檔完成後請告知，我們會用腳本重新比對 <code>locales/*.json</code> 驗收，確認每一列都真的落地。</p>
</section>

<a class="back" href="index.html">← 回 Design Review 首頁</a>
<footer>內部交付文件 · 由 tools/build_i18n_handoff.py 產生<br>© 2026 FindLife Inc.</footer>
</div>
"""

OUT.write_text(
    "<!doctype html>\n"
    "<!-- 改版 UI 文案交付／前端說明 · 由 tools/build_i18n_handoff.py 產生，不要直接改 i18n.html -->\n"
    '<html lang="zh-Hant"><head><meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    "<title>UI 文案交付 — 前端說明</title>\n"
    f"<style>{CSS}</style></head><body>{BODY}</body></html>\n",
    encoding="utf-8",
)
print(f"✅ {OUT}  （改名 {len(rename)} 筆／拼法 {len(spell)} 筆）")

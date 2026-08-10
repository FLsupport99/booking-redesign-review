/* 文案比對核心。抽成獨立模組是為了能用 match.test.mjs 做回歸測試——
   這關的風險不是漏抓，是為了讓它變綠而一步步放寬，最後變成放水。
   任何放寬都必須讓 match.test.mjs 的「必須抓到」那一組仍然是紅的。 */

const VALUE_SET = "\\d\\s:/｜／、，；年月日()~－–—.,-";   // 數字、時間與純分隔符號
const VALUE_ONLY = new RegExp(`^[${VALUE_SET}]+$`);
const VALUE_CHARS_G = new RegExp(`[${VALUE_SET}]`, "g");

const MIN_CHUNK = 4;        // 有把握的片段長度（中文資訊密度高，4 字已相當專屬）
const MAX_GAPS = 4;
const MIN_COVERAGE = 0.5;   // 只計「內容字」，時間戳不稀釋證據

/* ${...} 用括號平衡移除。用 /\$\{[^}]*\}/ 會停在第一個 }，
   巢狀樣板字串會把前綴一起吃掉——踩過三次。 */
export function stripInterp(src) {
  let out = "", i = 0;
  while (i < src.length) {
    if (src[i] === "$" && src[i + 1] === "{") {
      let depth = 1;
      i += 2;
      while (i < src.length && depth) {
        if (src[i] === "{") depth++;
        else if (src[i] === "}") depth--;
        i++;
      }
    } else out += src[i++];
  }
  return out;
}

const content = (s) => s.replace(VALUE_CHARS_G, "");

/* sources: [{ path, text }]。
   ⚠️ 去標籤（<[^>]+>）只能對 HTML 做。對 JS 做會出事——`names.length < 2 … =>` 之間
   會被當成一個標籤整段吃掉，夾在中間的文案就從語料裡消失了（「已選取」就是這樣不見的）。 */
const stripTags = (t) => t.replace(/<[^>]+>/g, " ");
const isHtml = (p) => /\.html?$/i.test(p);

export function createMatcher(sources) {
  const list = Array.isArray(sources) ? sources : [{ path: "inline.html", text: sources }];
  const raw = list.map((s) => s.text).join("\n");
  const forCorpus = list.map((s) => (isHtml(s.path) ? stripTags(s.text) : s.text)).join("\n");
  const stripped = forCorpus.replace(/\s+/g, "");
  const srcSkeleton = content(stripInterp(forCorpus));

  /* 從 i 起算，實作裡找得到的最長片段（純數字/標點不算證據） */
  const chunkAt = (t, i) => {
    for (let j = t.length; j - i >= MIN_CHUNK; j--) {
      const c = t.slice(i, j);
      if (!VALUE_ONLY.test(c) && stripped.includes(c)) return j - i;
    }
    return 0;
  };

  /* 路徑三：分段組裝。定稿一個 text node 在實作裡是多個欄位拼出來的時候用，
     例如 `${b.item}/${b.subItem}`。空隙只有在「純值」或「本身也在實作裡且 ≥2 字」時放行，
     所以單字錯字（可預約時段→可預約時間，空隙是 1 個「段」）仍然擋得住。 */
  const assembled = (t) => {
    const chunks = [], gaps = [];
    let i = 0;
    while (i < t.length) {
      const n = chunkAt(t, i);
      if (n) { chunks.push(t.slice(i, i + n)); i += n; continue; }
      let k = i + 1;
      while (k < t.length && !chunkAt(t, k)) k++;
      gaps.push(t.slice(i, k));
      i = k;
    }
    if (!chunks.some((c) => c.length >= MIN_CHUNK)) return false;
    if (gaps.length > MAX_GAPS) return false;

    const need = content(t).length;
    const got = chunks.reduce((n, c) => n + content(c).length, 0);
    if (need && got / need < MIN_COVERAGE) return false;

    /* 空隙也必須有證據：整段能從「實作裡出現過的片段（≥2 字）＋純值字元」組裝出來。
       這樣「已選取 單位D4、E2 尚有…」中段的單位清單放得過，
       而「單位X9、Z1」這種實作裡不存在的元素放不過。
       每片至少 2 字，是為了不讓單字錯字（「段」）從空隙溜走。 */
    const GAP_MAX_LEN = 24, GAP_MAX_PIECES = 4;
    const gapOk = (g) => {
      if (VALUE_ONLY.test(g)) return true;
      if (g.length >= 2 && stripped.includes(g)) return true;
      if (g.length > GAP_MAX_LEN) return false;
      let i = 0, pieces = 0;
      while (i < g.length) {
        if (VALUE_ONLY.test(g[i])) { i++; continue; }
        let best = 0;
        for (let j = g.length; j - i >= 2; j--) {
          if (stripped.includes(g.slice(i, j))) { best = j - i; break; }
        }
        if (!best || ++pieces > GAP_MAX_PIECES) return false;
        i += best;
      }
      return true;
    };
    return gaps.every(gapOk);
  };

  return function implHas(s) {
    const flat = s.replace(/\s+/g, "");
    /* 路徑一：原文／去標籤去空白後直接出現 */
    if (raw.includes(s) || stripped.includes(flat)) return true;
    /* 路徑二：骨架。處理「一句話中間夾一個動態值」，例如 `組數：${n}`。
       沒有動態值的短字串維持 3 字門檻，否則「上午」這種 2 字錯字會被放過。 */
    const k = content(flat);
    const min = k.length < flat.length ? 2 : 3;
    if (k.length >= min && srcSkeleton.includes(k)) return true;
    return assembled(flat);
  };
}

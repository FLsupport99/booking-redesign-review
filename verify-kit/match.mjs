/* 文案比對核心。抽成獨立模組是為了能用 match.test.mjs 做回歸測試——
   這關的風險不是漏抓，是為了讓它變綠而一步步放寬，最後變成放水。
   任何放寬都必須讓 match.test.mjs 的「必須抓到」那一組仍然是紅的。 */

const VALUE_SET = "\\d\\s:/｜／年月日()~－–—.,-";
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

export function createMatcher(sourceText) {
  const raw = sourceText;
  const stripped = raw.replace(/<[^>]+>/g, "").replace(/\s+/g, "");
  const srcSkeleton = content(stripInterp(raw.replace(/<[^>]+>/g, "")));

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

    return gaps.every((g) => VALUE_ONLY.test(g) || (g.length >= 2 && stripped.includes(g)));
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

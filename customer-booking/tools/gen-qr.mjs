/* 產生 LINE 加好友的真 QR code（assets/line-qr.png）。
   內容取自 js/api.js 的 lineUrl，換連結後重跑一次即可。
   用法：node tools/gen-qr.mjs
   （會呼叫 uv 跑 python 的 qrcode 套件，並用 opencv 解碼驗證掃得出來） */
import { readFileSync, existsSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const api = readFileSync(resolve(ROOT, "js/api.js"), "utf8");
const m = api.match(/lineUrl:\s*"([^"]+)"/);
if (!m) { console.error("在 js/api.js 找不到 lineUrl"); process.exit(1); }
const url = m[1];
const out = resolve(ROOT, "assets/line-qr.png");

const py = `
import qrcode
qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
qr.add_data(${JSON.stringify(url)}); qr.make(fit=True)
qr.make_image(fill_color="#06C755", back_color="white").save(${JSON.stringify(out)})
import cv2
data, *_ = cv2.QRCodeDetector().detectAndDecode(cv2.imread(${JSON.stringify(out)}))
assert data == ${JSON.stringify(url)}, f"解碼結果不符：{data!r}"
print("OK", data)
`;

console.log("產生 QR：", url);
const res = execFileSync("uv", ["run", "--with", "qrcode", "--with", "pillow", "--with", "opencv-python-headless",
  "python3", "-c", py], { encoding: "utf8" });
console.log(res.trim());
console.log("已寫入", out, existsSync(out) ? "" : "(失敗)");

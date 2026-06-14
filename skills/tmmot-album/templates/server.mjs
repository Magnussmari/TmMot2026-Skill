// @orchestrator: Magnús Smárason | smarason.is  @created: 2026-06-12
// ka2.sumarhus.com — KA-2 á Eyjamótinu. Einn prósess, núll dependencies.
// PIN-hlið fyrir foreldrahópinn (HMAC-kex), allt efni bak við hliðið.
// noindex alls staðar — börn á opnu interneti eru ekki til umræðu.
//
//   node server.mjs        — keyra (PORT, default 4250)
import http from "node:http";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const DIR = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT || 4250);
const PIN = process.env.KA2_PIN;
const SECRET = process.env.KA2_SECRET;
if (!PIN || !SECRET) { console.error("KA2_PIN / KA2_SECRET vantar"); process.exit(1); }
const COOKIE = "ka2";
const DAYS = 30;
// Myndbönd foreldra lenda hér (bind-mount á VM → lifa af endurbyggingu gáms).
const UPLOADS = process.env.KA2_UPLOADS || path.join(DIR, "uploads");
fs.mkdirSync(UPLOADS, { recursive: true });
const MAX_UPLOAD = 800 * 1024 * 1024; // 800 MB
// Killswitch: síðan lokar sjálfkrafa viku eftir mótið — kveðjusíða, ekkert efni.
const CLOSE = new Date(process.env.KA2_CLOSE || "2026-06-19T23:59:00Z").getTime();
const closed = () => Date.now() > CLOSE;

const sign = (s) => crypto.createHmac("sha256", SECRET).update(s).digest("base64url");
const mint = () => {
  const p = Buffer.from(JSON.stringify({ e: Date.now() + DAYS * 864e5 })).toString("base64url");
  return `${p}.${sign(p)}`;
};
const verify = (t) => {
  const [p, s] = String(t || "").split(".");
  if (!p || !s) return false;
  try {
    if (!crypto.timingSafeEqual(Buffer.from(sign(p)), Buffer.from(s))) return false;
    return JSON.parse(Buffer.from(p, "base64url").toString()).e > Date.now();
  } catch { return false; }
};
const authed = (req) => {
  const m = /(?:^|;\s*)ka2=([^;]+)/.exec(req.headers.cookie || "");
  return m ? verify(decodeURIComponent(m[1])) : false;
};

// hófleg vörn: 8 tilraunir á 10 mín per IP
const tries = new Map();
const limited = (ip) => {
  const now = Date.now();
  const a = (tries.get(ip) || []).filter((t) => now - t < 600e3);
  tries.set(ip, a);
  return a.length >= 8;
};

const MIME = { ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript",
  ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg",
  ".mp4": "video/mp4", ".webm": "video/webm", ".woff2": "font/woff2", ".txt": "text/plain",
  ".pdf": "application/pdf" };

const send = (res, code, body, type = "text/html; charset=utf-8", extra = {}) =>
  res.writeHead(code, { "Content-Type": type, "X-Robots-Tag": "noindex, nofollow, noarchive",
    "Cache-Control": "no-store", "Referrer-Policy": "no-referrer", ...extra }).end(body);

const page = (f) => fs.readFileSync(path.join(DIR, "public", f), "utf8");
const data = () => fs.readFileSync(path.join(DIR, "data.json"), "utf8");

http.createServer((req, res) => {
  const url = new URL(req.url, "http://x");
  const ip = req.headers["cf-connecting-ip"] || req.socket.remoteAddress || "?";

  if (url.pathname === "/robots.txt")
    return send(res, 200, "User-agent: *\nDisallow: /\n", "text/plain");

  if (closed()) return send(res, 410, page("closed.html"));

  if (req.method === "POST" && url.pathname === "/pin") {
    if (limited(ip)) return send(res, 429, JSON.stringify({ ok: false, msg: "Of margar tilraunir — reyndu eftir smástund." }), "application/json");
    let body = "";
    req.on("data", (c) => { body += c; if (body.length > 256) req.destroy(); });
    req.on("end", () => {
      let pin = "";
      try { pin = String(JSON.parse(body).pin || "").trim(); } catch {}
      const a = crypto.createHash("sha256").update(pin).digest();
      const b = crypto.createHash("sha256").update(PIN).digest();
      if (crypto.timingSafeEqual(a, b)) {
        return send(res, 200, JSON.stringify({ ok: true }), "application/json", {
          "Set-Cookie": `${COOKIE}=${encodeURIComponent(mint())}; Path=/; Max-Age=${DAYS * 86400}; HttpOnly; Secure; SameSite=Lax` });
      }
      tries.get(ip).push(Date.now());
      send(res, 401, JSON.stringify({ ok: false, msg: "Rangt PIN — prófaðu aftur." }), "application/json");
    });
    return;
  }

  // ---- myndbanda-upphal foreldra — bak við PIN, beint streymi á disk ----
  if (req.method === "POST" && url.pathname === "/upload") {
    if (!authed(req)) return send(res, 401, JSON.stringify({ ok: false, msg: "Innskráning útrunnin — opnaðu síðuna aftur." }), "application/json");
    const raw = (url.searchParams.get("name") || "video").slice(0, 90);
    const ext = (path.extname(raw) || ".mp4").toLowerCase();
    if (![".mp4", ".mov", ".webm", ".m4v"].includes(ext))
      return send(res, 415, JSON.stringify({ ok: false, msg: "Aðeins myndbönd (mp4, mov, webm)." }), "application/json");
    const base = path.basename(raw, path.extname(raw)).replace(/[^\w\-]+/g, "_").slice(0, 50) || "video";
    const fn = `${Date.now()}-${crypto.randomBytes(3).toString("hex")}-${base}${ext}`;
    const dest = path.join(UPLOADS, fn);
    const ws = fs.createWriteStream(dest);
    let size = 0, done = false;
    const fail = (code, msg) => {
      if (done) return; done = true;
      ws.destroy(); fs.unlink(dest, () => {}); try { req.destroy(); } catch {}
      send(res, code, JSON.stringify({ ok: false, msg }), "application/json");
    };
    req.on("data", (c) => { size += c.length; if (size > MAX_UPLOAD) fail(413, "Skrá of stór (hámark 800 MB)."); });
    req.on("error", () => fail(400, "Villa við móttöku."));
    ws.on("error", () => fail(500, "Vistun mistókst."));
    ws.on("finish", () => { if (done) return; done = true;
      console.log(`[upphal] ${fn} (${(size / 1048576).toFixed(1)} MB)`);
      send(res, 200, JSON.stringify({ ok: true, file: fn }), "application/json"); });
    req.pipe(ws);
    return;
  }

  if (req.method !== "GET" && req.method !== "HEAD") return send(res, 405, "Nei");

  if (!authed(req)) return send(res, url.pathname === "/" ? 200 : 401, page("gate.html"));

  if (url.pathname === "/" ) {
    const html = page("index.html").replace("/*__DATA__*/null", data());
    return send(res, 200, html);
  }

  // gated static (myndefni/video)
  const safe = path.normalize(url.pathname).replace(/^(\.\.[/\\])+/, "");
  const file = path.join(DIR, "public", safe);
  if (file.startsWith(path.join(DIR, "public")) && fs.existsSync(file) && fs.statSync(file).isFile()) {
    const ext = path.extname(file).toLowerCase();
    res.writeHead(200, { "Content-Type": MIME[ext] || "application/octet-stream",
      "X-Robots-Tag": "noindex, nofollow", "Cache-Control": "private, max-age=300" });
    return fs.createReadStream(file).pipe(res);
  }
  send(res, 404, page("gate.html"));
}).listen(PORT, () => console.log(`KA-2 vakt á :${PORT}`));

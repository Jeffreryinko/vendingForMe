// 매일 업무 플래너 — Supabase 엣지 함수 (외부 라이브러리 없음)
//  op=push   : DB(1분 예약 작업)가 "지금 보낼 알림"을 넘겨주면 웹 푸시로 보냄      [x-tick-key 필요]
//  op=init   : 알림용 열쇠쌍(VAPID)을 처음 한 번 만들어 DB에 보관                  [x-tick-key 필요]
//  op=gtoken : 로그인한 사용자의 Google 캘린더 접근 토큰을 새로 받아 줌            [사용자 로그인 필요]
//              (함수 비밀값 GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET 이 있어야 동작)
const SB_URL = (globalThis.Deno && Deno.env.get("SUPABASE_URL")) || "https://mirbslsgmwfahwitpgsl.supabase.co";
const SB_KEY = "sb_publishable_bwp_34f04zXo3x-Pfcl5Wg_UwCJV5Pj"; // 공개용 키 (사이트에도 그대로 실려 있는 값)
const CONTACT = "mailto:planner@jeffreryinko.github.io";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info, x-tick-key",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { ...CORS, "Content-Type": "application/json" } });

async function rpc(name, args, bearer) {
  const res = await fetch(`${SB_URL}/rest/v1/rpc/${name}`, {
    method: "POST",
    headers: { apikey: SB_KEY, Authorization: `Bearer ${bearer || SB_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify(args || {}),
  });
  const text = await res.text();
  if (!res.ok) throw new Error(`rpc ${name} ${res.status}: ${text.slice(0, 200)}`);
  return text ? JSON.parse(text) : null;
}

// ── 바이트 도우미 ─────────────────────────────────────────────────────
const enc = new TextEncoder();
const b64u = (buf) => {
  const b = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
  let s = "";
  for (let i = 0; i < b.length; i++) s += String.fromCharCode(b[i]);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
};
const unb64u = (str) => {
  const s = String(str).replace(/-/g, "+").replace(/_/g, "/");
  const bin = atob(s + "=".repeat((4 - (s.length % 4)) % 4));
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
};
const concat = (...parts) => {
  const out = new Uint8Array(parts.reduce((n, p) => n + p.length, 0));
  let o = 0;
  for (const p of parts) { out.set(p, o); o += p.length; }
  return out;
};

// ── VAPID (RFC 8292) ─────────────────────────────────────────────────
export async function generateVapid() {
  const pair = await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign"]);
  const pub = b64u(await crypto.subtle.exportKey("raw", pair.publicKey));
  const priv = JSON.stringify(await crypto.subtle.exportKey("jwk", pair.privateKey));
  return { pub, priv };
}
async function vapidAuth(endpoint, vapid) {
  const key = await crypto.subtle.importKey("jwk", JSON.parse(vapid.priv), { name: "ECDSA", namedCurve: "P-256" }, false, ["sign"]);
  const head = b64u(enc.encode(JSON.stringify({ typ: "JWT", alg: "ES256" })));
  const body = b64u(enc.encode(JSON.stringify({
    aud: new URL(endpoint).origin, exp: Math.floor(Date.now() / 1000) + 12 * 3600, sub: CONTACT,
  })));
  const sig = await crypto.subtle.sign({ name: "ECDSA", hash: "SHA-256" }, key, enc.encode(`${head}.${body}`));
  return `vapid t=${head}.${body}.${b64u(sig)}, k=${vapid.pub}`;
}

// ── 메시지 암호화 (RFC 8291, aes128gcm) ───────────────────────────────
async function hkdf(salt, ikm, info, len) {
  const key = await crypto.subtle.importKey("raw", ikm, "HKDF", false, ["deriveBits"]);
  return new Uint8Array(await crypto.subtle.deriveBits({ name: "HKDF", hash: "SHA-256", salt, info }, key, len * 8));
}
export async function encryptPayload(sub, text) {
  const uaPub = unb64u(sub.p256dh);
  const authSecret = unb64u(sub.auth);
  const local = await crypto.subtle.generateKey({ name: "ECDH", namedCurve: "P-256" }, true, ["deriveBits"]);
  const localPub = new Uint8Array(await crypto.subtle.exportKey("raw", local.publicKey));
  const peer = await crypto.subtle.importKey("raw", uaPub, { name: "ECDH", namedCurve: "P-256" }, false, []);
  const shared = new Uint8Array(await crypto.subtle.deriveBits({ name: "ECDH", public: peer }, local.privateKey, 256));
  const ikm = await hkdf(authSecret, shared, concat(enc.encode("WebPush: info\0"), uaPub, localPub), 32);
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const cek = await hkdf(salt, ikm, enc.encode("Content-Encoding: aes128gcm\0"), 16);
  const nonce = await hkdf(salt, ikm, enc.encode("Content-Encoding: nonce\0"), 12);
  const aes = await crypto.subtle.importKey("raw", cek, "AES-GCM", false, ["encrypt"]);
  const plain = concat(enc.encode(text), new Uint8Array([2])); // 0x02 = 마지막 레코드 표시
  const cipher = new Uint8Array(await crypto.subtle.encrypt({ name: "AES-GCM", iv: nonce }, aes, plain));
  const header = concat(salt, new Uint8Array([0, 0, 16, 0]), new Uint8Array([localPub.length]), localPub); // rs = 4096
  return concat(header, cipher);
}

export async function sendPush(job, vapid) {
  const payload = JSON.stringify({ title: job.title, body: job.body, tag: job.tag, url: job.url });
  const body = await encryptPayload(job, payload);
  const res = await fetch(job.endpoint, {
    method: "POST",
    headers: {
      Authorization: await vapidAuth(job.endpoint, vapid),
      "Content-Encoding": "aes128gcm",
      "Content-Type": "application/octet-stream",
      TTL: "900",
      Urgency: "high",
    },
    body,
  });
  return res.status;
}

async function ensureVapid(key) {
  let ctx = await rpc("planner_fn_ctx", { p_key: key }); // 열쇠가 틀리면 여기서 오류
  if (!ctx.pub || !ctx.priv) {
    const v = await generateVapid();
    ctx = await rpc("planner_fn_set_vapid", { p_key: key, p_pub: v.pub, p_priv: v.priv });
  }
  return ctx;
}

async function opPush(req, body) {
  const key = req.headers.get("x-tick-key") || "";
  let vapid;
  try { vapid = await ensureVapid(key); } catch (_e) { return json({ error: "forbidden" }, 403); }
  if (body.op === "init") return json({ ok: true, pub: vapid.pub });
  const jobs = Array.isArray(body.jobs) ? body.jobs.slice(0, 500) : [];
  const gone = [];
  let sent = 0, failed = 0;
  await Promise.all(jobs.map(async (job) => {
    try {
      const status = await sendPush(job, vapid);
      if (status === 404 || status === 410) gone.push(job.endpoint);
      else if (status >= 200 && status < 300) sent++;
      else { failed++; console.error("push status", status, new URL(job.endpoint).host); }
    } catch (e) { failed++; console.error("push error", String(e)); }
  }));
  if (gone.length) { try { await rpc("planner_fn_prune", { p_key: key, p_endpoints: [...new Set(gone)] }); } catch (e) { console.error(String(e)); } }
  return json({ sent, failed, gone: gone.length });
}

async function opGtoken(req) {
  const bearer = (req.headers.get("authorization") || "").replace(/^Bearer\s+/i, "");
  if (!bearer || bearer === SB_KEY) return json({ error: "login" }, 401);
  const id = globalThis.Deno && Deno.env.get("GOOGLE_CLIENT_ID");
  const secret = globalThis.Deno && Deno.env.get("GOOGLE_CLIENT_SECRET");
  if (!id || !secret) return json({ error: "no_secret" });
  let refresh;
  try { refresh = await rpc("planner_google_get", {}, bearer); } catch (_e) { return json({ error: "login" }, 401); }
  if (!refresh) return json({ error: "not_connected" });
  const res = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ client_id: id, client_secret: secret, refresh_token: refresh, grant_type: "refresh_token" }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    if (data.error === "invalid_grant") { try { await rpc("planner_google_clear", {}, bearer); } catch (_e) { /* 무시 */ } return json({ error: "reauth" }); }
    return json({ error: "google", detail: String(data.error || res.status) });
  }
  return json({ access_token: data.access_token, expires_in: data.expires_in });
}

export async function handler(req) {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json({ error: "method" }, 405);
  let body = {};
  try { body = await req.json(); } catch (_e) { /* 빈 본문 */ }
  try {
    if (body.op === "push" || body.op === "init") return await opPush(req, body);
    if (body.op === "gtoken") return await opGtoken(req);
    return json({ error: "unknown op" }, 400);
  } catch (e) {
    console.error(String(e));
    return json({ error: "server" }, 500);
  }
}

if (globalThis.Deno) Deno.serve(handler);

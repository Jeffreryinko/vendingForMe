/* claude-shim.js — 아티팩트 전용 부품(window.claude.use)의 대체 부품("돼지코").
 *
 * 앱은 자기가 아직 claude.ai 안에 있는 줄 알고 그대로 동작합니다.
 *   db     → 읽기: ../data/<app>/<컬렉션>/… JSON 파일 (로봇이 채움)
 *             쓰기: 이 브라우저의 localStorage (읽은 기록·설정 등)
 *   sample → 없음(null). 앱은 null이면 즉석 요약 버튼을 숨기도록 이미 만들어져 있음.
 *   user   → 없음(null).
 *
 * 2단계(로그인+Supabase)로 갈 때는 아래 LocalStore 부분만 서버 저장소로 갈아끼우면 됩니다.
 */
(function () {
  "use strict";
  var APP = window.VFM_APP || (location.pathname.indexOf("/iyagi") >= 0 ? "iyagi" : "sisa");
  var BASE = window.VFM_DATA_BASE || ("../data/" + APP + "/");
  var CFG = window.VFM_SHIM || {};
  // 파일에서 읽는 컬렉션(로봇이 씀). 그 밖의 컬렉션은 전부 이 기기의 localStorage.
  var FILE_COLS = CFG.fileCollections || (APP === "sisa"
    ? { editions: "inline", feed: "ids", brief: "ids", tr: "ids" }
    : { stories: "inline" });
  var RETAIN = CFG.retainDays || (APP === "sisa" ? { events: 90, imp: 90, reports: 120 } : {});
  var LS_PREFIX = "vfm:" + APP + ":";

  /* ── localStorage 저장소 ── */
  function lsKey(col) { return LS_PREFIX + col; }
  function readLocal(col) {
    try { var raw = localStorage.getItem(lsKey(col)); return raw ? JSON.parse(raw) : {}; } catch (e) { return {}; }
  }
  function writeLocal(col, obj) {
    try { localStorage.setItem(lsKey(col), JSON.stringify(obj)); return true; }
    catch (e) { console.warn("[shim] localStorage 저장 실패", col, e); return false; }
  }
  function pruneLocal(col) {                       // 오래된 기록 정리 (보관 기간이 정해진 컬렉션만)
    var days = RETAIN[col]; if (!days) return;
    var obj = readLocal(col), cut = Date.now() - days * 864e5, changed = false;
    Object.keys(obj).forEach(function (id) {
      var d = obj[id] || {}; var t = d.at || d.updatedAt || d.day;
      var ms = t ? Date.parse(String(t).length === 10 ? t + "T00:00:00Z" : t) : NaN;
      if (!isNaN(ms) && ms < cut) { delete obj[id]; changed = true; }
    });
    if (changed) writeLocal(col, obj);
  }
  var listeners = {};                               // col → [fn]
  function notify(col) { (listeners[col] || []).forEach(function (fn) { try { fn(); } catch (e) { } }); }

  /* ── 파일 저장소 (캐시 포함) ── */
  var fileCache = {};
  function getJSON(path) {
    if (fileCache[path]) return fileCache[path];
    var p = fetch(BASE + path, { cache: "no-cache" }).then(function (r) {
      if (!r.ok) throw Object.assign(new Error("not-found"), { code: "not-found", status: r.status });
      return r.json();
    });
    fileCache[path] = p; p.catch(function () { delete fileCache[path]; });
    return p;
  }
  // _index.json: "inline" 모드면 [{id, ...data}] (작은 컬렉션), "ids" 모드면 ["id", …]
  function fileIndex(col) {
    return getJSON(col + "/_index.json").catch(function () { return []; });
  }
  function fileDoc(col, id) {
    return getJSON(col + "/" + id + ".json").then(function (d) { return { id: id, data: d }; });
  }
  function fileAll(col, filterId) {
    var mode = FILE_COLS[col];
    return fileIndex(col).then(function (idx) {
      if (mode === "inline") {
        return idx.map(function (d) { var o = Object.assign({}, d); var id = o.id; delete o.id; return { id: id, data: o }; });
      }
      var ids = idx.filter(function (id) { return !filterId || filterId(id); });
      return Promise.all(ids.map(function (id) { return fileDoc(col, id).catch(function () { return null; }); }))
        .then(function (arr) { return arr.filter(Boolean); });
    });
  }

  /* ── Firestore 비슷한 모양으로 감싸기 ── */
  function snapDoc(id, data) {
    return { id: id, exists: data !== undefined && data !== null, data: function () { return data; }, metadata: { fromCache: false } };
  }
  function snapColl(docs) {
    return { docs: docs, empty: docs.length === 0, size: docs.length, metadata: { fromCache: false },
             forEach: function (fn) { docs.forEach(fn); } };
  }
  function cmp(op, a, b) {
    switch (op) {
      case "==": case "eq": return a === b;
      case "!=": case "ne": return a !== b;
      case "<": case "lt": return a < b;
      case "<=": case "lte": return a <= b;
      case ">": case "gt": return a > b;
      case ">=": case "gte": return a >= b;
      case "in": return Array.isArray(b) && b.indexOf(a) >= 0;
      case "not-in": return Array.isArray(b) && b.indexOf(a) < 0;
      case "array-contains": return Array.isArray(a) && a.indexOf(b) >= 0;
    }
    return false;
  }

  function Query(col, wheres, order, lim) {
    this.col = col; this.wheres = wheres || []; this.order = order || null; this.lim = lim || 0;
  }
  Query.prototype.where = function (f, op, v) { return new Query(this.col, this.wheres.concat([[f, op, v]]), this.order, this.lim); };
  Query.prototype.orderBy = function (f, dir) { return new Query(this.col, this.wheres, { f: f, dir: dir || "asc" }, this.lim); };
  Query.prototype.limit = function (n) { return new Query(this.col, this.wheres, this.order, n); };
  Query.prototype._load = function () {
    var col = this.col, wheres = this.wheres, order = this.order, lim = this.lim;
    var local = readLocal(col);
    var fromFiles;
    if (FILE_COLS[col]) {
      // feed/tr/brief는 doc id가 "<판>__<언어>" 꼴이라, edition 조건이 있으면 그 판의 파일만 읽음
      var edW = wheres.filter(function (w) { return w[0] === "edition" && (w[1] === "==" || w[1] === "in"); })[0];
      var filter = edW ? function (id) { var ed = id.split("__")[0]; return edW[1] === "==" ? ed === edW[2] : edW[2].indexOf(ed) >= 0; } : null;
      fromFiles = fileAll(col, filter);
    } else fromFiles = Promise.resolve([]);
    return fromFiles.then(function (fdocs) {
      var map = {};
      fdocs.forEach(function (d) { map[d.id] = d.data; });
      Object.keys(local).forEach(function (id) { map[id] = local[id]; });   // 이 기기에서 쓴 것이 파일보다 우선
      var docs = Object.keys(map).map(function (id) { return snapDoc(id, map[id]); });
      wheres.forEach(function (w) { docs = docs.filter(function (d) { return cmp(w[1], (d.data() || {})[w[0]], w[2]); }); });
      if (order) {
        docs.sort(function (a, b) {
          var x = (a.data() || {})[order.f], y = (b.data() || {})[order.f];
          var r = x === y ? 0 : (x === undefined ? 1 : y === undefined ? -1 : (x < y ? -1 : 1));
          return order.dir === "desc" ? -r : r;
        });
      }
      if (lim) docs = docs.slice(0, lim);
      return snapColl(docs);
    });
  };
  Query.prototype.get = function () { return this._load(); };
  Query.prototype.onSnapshot = function (cb, errCb) {
    var self = this, alive = true;
    function run() { self._load().then(function (s) { if (alive) cb(s); }, function (e) { if (alive && errCb) errCb(e); }); }
    run();
    var fn = function () { run(); };
    (listeners[self.col] = listeners[self.col] || []).push(fn);
    return function unsubscribe() { alive = false; listeners[self.col] = (listeners[self.col] || []).filter(function (f) { return f !== fn; }); };
  };

  function DocRef(col, id) { this.col = col; this.id = id; }
  DocRef.prototype.get = function () {
    var col = this.col, id = this.id, local = readLocal(col);
    if (Object.prototype.hasOwnProperty.call(local, id)) return Promise.resolve(snapDoc(id, local[id]));
    if (!FILE_COLS[col]) return Promise.resolve(snapDoc(id, undefined));
    if (FILE_COLS[col] === "inline") {
      return fileAll(col).then(function (docs) { var hit = docs.filter(function (d) { return d.id === id; })[0]; return snapDoc(id, hit ? hit.data : undefined); });
    }
    return fileDoc(col, id).then(function (d) { return snapDoc(id, d.data); }, function () { return snapDoc(id, undefined); });
  };
  DocRef.prototype.set = function (data) {
    var local = readLocal(this.col); local[this.id] = JSON.parse(JSON.stringify(data || {}));
    var ok = writeLocal(this.col, local); notify(this.col);
    return ok ? Promise.resolve({ id: this.id }) : Promise.reject(Object.assign(new Error("storage-full"), { code: "storage-full" }));
  };
  DocRef.prototype.update = function (patch) {
    var self = this;
    return this.get().then(function (s) { return self.set(Object.assign({}, s.exists ? s.data() : {}, patch || {})); });
  };
  DocRef.prototype.delete = function () {
    var local = readLocal(this.col); delete local[this.id]; writeLocal(this.col, local); notify(this.col); return Promise.resolve();
  };

  function Collection(col) { Query.call(this, col); }
  Collection.prototype = Object.create(Query.prototype);
  Collection.prototype.doc = function (id) { return new DocRef(this.col, String(id)); };

  var db = { collection: function (col) { pruneLocal(col); return new Collection(col); } };

  /* ── window.claude ── */
  window.claude = {
    use: function (name) {
      if (name === "db") return Promise.resolve(db);
      return Promise.resolve(null);                 // sample, user 등은 서버 버전에 없음
    },
    shim: true
  };

  /* ── 공용 도구 (shell.js가 씀): 기록 내보내기/불러오기, 저장 용량 ── */
  window.vfm = window.vfm || {};
  window.vfm.app = APP;
  window.vfm.exportAll = function () {
    var out = { app: "vendingForMe", exportedAt: new Date().toISOString(), keys: {} };
    for (var i = 0; i < localStorage.length; i++) {
      var k = localStorage.key(i);
      if (/^(vfm:|sv_|iyagi-|vfm_)/.test(k)) out.keys[k] = localStorage.getItem(k);
    }
    return out;
  };
  window.vfm.importAll = function (obj) {
    if (!obj || obj.app !== "vendingForMe" || !obj.keys) throw new Error("자판기 내보내기 파일이 아니에요");
    var n = 0;
    Object.keys(obj.keys).forEach(function (k) { localStorage.setItem(k, obj.keys[k]); n++; });
    return n;
  };
  window.vfm.storageBytes = function () {
    var n = 0; for (var i = 0; i < localStorage.length; i++) { var k = localStorage.key(i); n += (k.length + (localStorage.getItem(k) || "").length) * 2; }
    return n;
  };
})();

/* ── 보던 자리 기억 ──
 * 다른 사이트에 갔다 오거나 앱이 메모리에서 내려갔다 다시 열릴 때, 처음 화면이 아니라 보던 화면(탭·글·스크롤)으로 돌아옵니다.
 * 주소 끝(#…)이 사라진 채 열리면 마지막으로 저장해 둔 자리로 되돌립니다 (12시간 안쪽). */
(function () {
  var APP = window.VFM_APP || "app", KEY = "vfm:pos:" + APP, MAX = 12 * 3600e3;
  function rd() { try { return JSON.parse(localStorage.getItem(KEY) || "null"); } catch (e) { return null; } }
  function wr() {
    var h = location.hash || "";
    if (h === "#home") return;                    // 뒤로가기 완충용 자리는 저장하지 않음
    try { localStorage.setItem(KEY, JSON.stringify({ h: h, y: Math.round(window.scrollY || 0), t: Date.now() })); } catch (e) { }
  }
  var pos = rd(), h0 = location.hash || "";
  var fresh = pos && pos.h && pos.h !== "#home" && Date.now() - pos.t < MAX;
  var atStart = h0 === "" || h0 === "#home" || h0 === "#today" || h0 === "#library";
  var restored = false;
  if (fresh && atStart && pos.h !== h0) { try { history.replaceState(history.state, "", location.pathname + location.search + pos.h); restored = true; } catch (e) { } }
  if (restored || (fresh && pos.h === h0)) {
    var tries = 0, go = function () {
      if (++tries > 12) return;
      if (document.documentElement.scrollHeight > pos.y + window.innerHeight * 0.5) window.scrollTo(0, pos.y); else setTimeout(go, 400);
    };
    window.addEventListener("load", function () { setTimeout(go, 600); });
  }
  window.addEventListener("hashchange", function () { setTimeout(wr, 50); });
  document.addEventListener("visibilitychange", function () { if (document.visibilityState === "hidden") wr(); });
  window.addEventListener("pagehide", wr);
  var tm; window.addEventListener("scroll", function () { clearTimeout(tm); tm = setTimeout(wr, 400); }, { passive: true });
})();

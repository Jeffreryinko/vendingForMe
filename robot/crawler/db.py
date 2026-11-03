"""DB 접근 계층.

- SupabaseDB : Supabase REST(PostgREST) 를 service_role 키로 호출 (GitHub Actions 에서 사용)
- LocalDB    : JSON 파일에 저장 (키 없이 내 PC/테스트에서 돌려볼 때 사용, --local 옵션)
두 클래스는 같은 메서드를 가지므로 수집기 코드는 어느 쪽인지 신경 쓰지 않습니다.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


class SupabaseDB:
    def __init__(self, url: str, service_key: str):
        self.base = url.rstrip("/") + "/rest/v1"
        self.h = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
        }

    # ── 공통 ──
    def _get(self, table, params):
        out, offset = [], 0
        while True:
            r = requests.get(f"{self.base}/{table}", headers={**self.h, "Range": f"{offset}-{offset + 999}"},
                             params=params, timeout=60)
            r.raise_for_status()
            rows = r.json()
            out += rows
            if len(rows) < 1000:
                return out
            offset += 1000

    def _post(self, table, rows, prefer="return=representation", params=None):
        r = requests.post(f"{self.base}/{table}", headers={**self.h, "Prefer": prefer},
                          params=params or {}, data=json.dumps(rows, ensure_ascii=False).encode(), timeout=60)
        if r.status_code >= 300:
            raise RuntimeError(f"POST {table} {r.status_code}: {r.text[:300]}")
        return r.json() if r.text else []

    def _patch(self, table, match, fields):
        r = requests.patch(f"{self.base}/{table}", headers={**self.h, "Prefer": "return=minimal"},
                           params=match, data=json.dumps(fields, ensure_ascii=False).encode(), timeout=60)
        if r.status_code >= 300:
            raise RuntimeError(f"PATCH {table} {r.status_code}: {r.text[:300]}")

    def _rpc(self, fn, args):
        r = requests.post(f"{self.base}/rpc/{fn}", headers=self.h,
                          data=json.dumps(args, ensure_ascii=False).encode(), timeout=120)
        if r.status_code >= 300:
            raise RuntimeError(f"RPC {fn} {r.status_code}: {r.text[:300]}")
        return r.json() if r.text else None

    # ── 수집처 ──
    def upsert_sources(self, rows):
        self._post("sources", rows, prefer="resolution=merge-duplicates,return=minimal",
                   params={"on_conflict": "id"})

    def update_source(self, sid, fields):
        self._patch("sources", {"id": f"eq.{sid}"}, fields)

    def list_sources(self):
        return self._get("sources", {"select": "*"})

    # ── 실행 기록 ──
    def start_run(self, slot):
        return self._post("crawl_runs", [{"slot": slot}])[0]["id"]

    def finish_run(self, run_id, stats, chars_deepl, chars_google):
        self._patch("crawl_runs", {"id": f"eq.{run_id}"},
                    {"finished_at": now_iso(), "stats": stats, "chars_deepl": chars_deepl, "chars_google": chars_google})

    def runs_since(self, iso):
        return self._get("crawl_runs", {"select": "*", "started_at": f"gte.{iso}", "order": "started_at"})

    def month_chars(self, month_start_iso):
        rows = self._get("crawl_runs", {"select": "chars_deepl,chars_google", "started_at": f"gte.{month_start_iso}"})
        return (sum(r["chars_deepl"] or 0 for r in rows), sum(r["chars_google"] or 0 for r in rows))

    # ── 글 ──
    def existing_items(self, source_id, hashes):
        found = {}
        for part in _chunks(list(hashes), 80):
            rows = self._get("items", {"select": "id,guid_hash", "source_id": f"eq.{source_id}",
                                       "guid_hash": "in.(" + ",".join(part) + ")"})
            found.update({r["guid_hash"]: r["id"] for r in rows})
        return found

    def insert_items(self, rows):
        out = []
        for part in _chunks(rows, 200):
            out += self._post("items", part, prefer="resolution=ignore-duplicates,return=representation",
                              params={"on_conflict": "source_id,guid_hash", "select": "id,source_id,guid_hash"})
        return out

    def bulk_update_items(self, rows):
        n = 0
        for part in _chunks(rows, 300):
            n += self._rpc("bulk_update_items", {"rows": part}) or 0
        return n

    def insert_snapshots(self, rows):
        for part in _chunks(rows, 500):
            self._post("item_snapshots", part, prefer="resolution=ignore-duplicates,return=minimal",
                       params={"on_conflict": "item_id,run_id"})

    def items_since(self, iso, kinds=None):
        p = {"select": "*", "first_seen_at": f"gte.{iso}", "order": "first_seen_at"}
        if kinds:
            p["kind"] = "in.(" + ",".join(kinds) + ")"
        return self._get("items", p)

    def untranslated_items(self, since_iso, limit=400):
        return self._get("items", {"select": "id,title,summary,lang,kind,first_rank,source_id",
                                   "translated_by": "is.null", "first_seen_at": f"gte.{since_iso}",
                                   "lang": "neq.ko", "order": "first_seen_at.desc", "limit": str(limit)})

    def snapshots_for_runs(self, run_ids):
        if not run_ids:
            return []
        return self._get("item_snapshots", {"select": "*", "run_id": "in.(" + ",".join(map(str, run_ids)) + ")"})

    # ── 사건 ──
    def replace_stories(self, day, stories):
        r = requests.delete(f"{self.base}/stories", headers=self.h, params={"day": f"eq.{day}"}, timeout=60)
        r.raise_for_status()
        if stories:
            self._post("stories", stories, prefer="return=minimal")

    def stories_for_day(self, day):
        return self._get("stories", {"select": "*", "day": f"eq.{day}"})

    # ── 기록·리포트 ──
    def events_between(self, start_iso, end_iso):
        return self._get("view_events", {"select": "*", "and": f"(created_at.gte.{start_iso},created_at.lt.{end_iso})",
                                         "order": "created_at"})

    def items_by_ids(self, ids):
        out = []
        for part in _chunks(sorted(set(ids)), 150):
            out += self._get("items", {"select": "*", "id": "in.(" + ",".join(map(str, part)) + ")"})
        return out

    def upsert_world_report(self, row):
        self._post("world_reports", [row], prefer="resolution=merge-duplicates,return=minimal",
                   params={"on_conflict": "day"})

    def upsert_user_report(self, row):
        self._post("user_reports", [row], prefer="resolution=merge-duplicates,return=minimal",
                   params={"on_conflict": "user_id,day"})

    def prune(self, keep_days=45):
        return self._rpc("prune_old_items", {"keep_days": keep_days})


class LocalDB:
    """키 없이 테스트할 때 쓰는 JSON 파일 저장소 (Supabase 와 같은 동작을 흉내)."""

    TABLES = ["sources", "crawl_runs", "items", "item_snapshots", "stories", "view_events",
              "world_reports", "user_reports"]

    def __init__(self, path: str):
        self.path = Path(path)
        self.d = json.loads(self.path.read_text()) if self.path.exists() else {t: [] for t in self.TABLES}
        for t in self.TABLES:
            self.d.setdefault(t, [])

    def save(self):
        self.path.write_text(json.dumps(self.d, ensure_ascii=False, indent=1, default=str))

    def _next_id(self, table):
        return max([r.get("id", 0) for r in self.d[table]] or [0]) + 1

    def upsert_sources(self, rows):
        by = {r["id"]: r for r in self.d["sources"]}
        for r in rows:
            by.setdefault(r["id"], {}).update(r)
        self.d["sources"] = list(by.values())

    def update_source(self, sid, fields):
        for r in self.d["sources"]:
            if r["id"] == sid:
                r.update(fields)

    def list_sources(self):
        return self.d["sources"]

    def start_run(self, slot):
        rid = self._next_id("crawl_runs")
        self.d["crawl_runs"].append({"id": rid, "slot": slot, "started_at": now_iso(), "stats": {},
                                     "chars_deepl": 0, "chars_google": 0})
        return rid

    def finish_run(self, run_id, stats, chars_deepl, chars_google):
        for r in self.d["crawl_runs"]:
            if r["id"] == run_id:
                r.update(finished_at=now_iso(), stats=stats, chars_deepl=chars_deepl, chars_google=chars_google)

    def runs_since(self, iso):
        return [r for r in self.d["crawl_runs"] if r["started_at"] >= iso]

    def month_chars(self, month_start_iso):
        rows = self.runs_since(month_start_iso)
        return (sum(r["chars_deepl"] for r in rows), sum(r["chars_google"] for r in rows))

    def existing_items(self, source_id, hashes):
        hs = set(hashes)
        return {r["guid_hash"]: r["id"] for r in self.d["items"] if r["source_id"] == source_id and r["guid_hash"] in hs}

    def insert_items(self, rows):
        out = []
        for r in rows:
            r = {**r, "id": self._next_id("items")}
            r.setdefault("first_seen_at", now_iso())
            r.setdefault("last_seen_at", r["first_seen_at"])
            self.d["items"].append(r)
            out.append({"id": r["id"], "source_id": r["source_id"], "guid_hash": r["guid_hash"]})
        return out

    def bulk_update_items(self, rows):
        by = {r["id"]: r for r in self.d["items"]}
        for u in rows:
            it = by.get(u["id"])
            if it:
                it.update({k: v for k, v in u.items() if v is not None and k != "id"})
        return len(rows)

    def insert_snapshots(self, rows):
        self.d["item_snapshots"] += rows

    def items_since(self, iso, kinds=None):
        return [r for r in self.d["items"] if r["first_seen_at"] >= iso and (not kinds or r["kind"] in kinds)]

    def untranslated_items(self, since_iso, limit=400):
        rows = [r for r in self.d["items"] if not r.get("translated_by") and r["first_seen_at"] >= since_iso]
        return rows[-limit:]

    def snapshots_for_runs(self, run_ids):
        s = set(run_ids)
        return [r for r in self.d["item_snapshots"] if r["run_id"] in s]

    def replace_stories(self, day, stories):
        self.d["stories"] = [s for s in self.d["stories"] if s["day"] != day]
        for s in stories:
            self.d["stories"].append({**s, "id": self._next_id("stories")})

    def stories_for_day(self, day):
        return [s for s in self.d["stories"] if s["day"] == day]

    def events_between(self, start_iso, end_iso):
        return [e for e in self.d["view_events"] if start_iso <= e["created_at"] < end_iso]

    def items_by_ids(self, ids):
        s = set(ids)
        return [r for r in self.d["items"] if r["id"] in s]

    def upsert_world_report(self, row):
        self.d["world_reports"] = [r for r in self.d["world_reports"] if r["day"] != row["day"]] + [row]

    def upsert_user_report(self, row):
        self.d["user_reports"] = [r for r in self.d["user_reports"]
                                  if not (r["day"] == row["day"] and r["user_id"] == row["user_id"])] + [row]

    def prune(self, keep_days=45):
        return 0


def get_db(local_path: str | None = None):
    if local_path:
        return LocalDB(local_path)
    url, key = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise SystemExit("SUPABASE_URL / SUPABASE_SERVICE_KEY 환경변수가 없습니다. 테스트는 --local data.json 으로 실행하세요.")
    return SupabaseDB(url, key)

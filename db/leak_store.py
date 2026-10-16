# -*- coding: utf-8 -*-
"""تشخیص نشت کانفیگ: ایندکس هش اثر انگشت، کانال‌های زیر نظر، پست‌های دیده‌شده و رویدادهای نشت.

فقط هش SHA-256 مقادیر محرمانه (UUID، پسورد، توکن اشتراک) در credential_index ذخیره می‌شود،
نه خود مقادیر. این جدول‌ها کاملاً مستقل از جدول‌های یوزربات و Business هستند."""

from datetime import datetime, timezone

LOOKUP_CHUNK = 400


class LeakStoreMixin:
    # ----- credential index ----------------------------------------------------
    def replace_credential_index(self, config_id: int, panel_server_id, username: str, user_id, entries: dict):
        """entries: {hash: kind}. اثر انگشت قبلی همان سرویس کامل جایگزین می‌شود."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM credential_index WHERE config_id=?", (config_id,))
            conn.executemany(
                "INSERT OR IGNORE INTO credential_index "
                "(hash, kind, panel_server_id, username, user_id, config_id, updated_at) "
                "VALUES (?,?,?,?,?,?,CURRENT_TIMESTAMP)",
                [(h, kind, panel_server_id, username, user_id, config_id) for h, kind in entries.items()],
            )

    def delete_credential_index(self, config_id: int):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM credential_index WHERE config_id=?", (config_id,))

    def purge_credential_index_except(self, active_config_ids):
        """ردیف‌های سرویس‌هایی که دیگر فعال نیستند (حذف/منقضی) را از ایندکس پاک می‌کند."""
        ids = [int(x) for x in active_config_ids]
        with self._get_conn() as conn:
            if not ids:
                conn.execute("DELETE FROM credential_index")
                return
            placeholders = ",".join("?" for _ in ids)
            conn.execute(f"DELETE FROM credential_index WHERE config_id NOT IN ({placeholders})", ids)

    def lookup_credential_hashes(self, hashes) -> list:
        hashes = list(hashes)
        rows = []
        with self._get_conn() as conn:
            for start in range(0, len(hashes), LOOKUP_CHUNK):
                chunk = hashes[start:start + LOOKUP_CHUNK]
                placeholders = ",".join("?" for _ in chunk)
                rows.extend(conn.execute(
                    f"SELECT * FROM credential_index WHERE hash IN ({placeholders})", chunk,
                ).fetchall())
        return rows

    def list_index_target_config_ids(self) -> list:
        """سرویس‌های فعال روی پنل‌های فعال که باید در ایندکس باشند."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT cc.id FROM custom_configs cc JOIN panel_servers ps ON ps.id = cc.panel_server_id "
                "WHERE cc.status='active' AND ps.is_active=1 ORDER BY cc.id"
            ).fetchall()
        return [r["id"] for r in rows]

    def get_credential_index_stats(self) -> dict:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS hashes, COUNT(DISTINCT config_id) AS configs, "
                "MAX(updated_at) AS last_update FROM credential_index"
            ).fetchone()
        return {"hashes": row["hashes"] or 0, "configs": row["configs"] or 0, "last_update": row["last_update"]}

    # ----- channels under watch -----------------------------------------------
    def list_leak_channels(self) -> list:
        with self._get_conn() as conn:
            return conn.execute("SELECT * FROM leak_channels ORDER BY title, channel_id").fetchall()

    def list_active_leak_channels(self) -> list:
        with self._get_conn() as conn:
            return conn.execute("SELECT * FROM leak_channels WHERE active=1").fetchall()

    def get_leak_channel(self, channel_id: int):
        with self._get_conn() as conn:
            return conn.execute("SELECT * FROM leak_channels WHERE channel_id=?", (channel_id,)).fetchone()

    def add_leak_channel(self, channel_id: int, title: str, username: str, last_post_id: int):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO leak_channels (channel_id, title, username, active, last_post_id) VALUES (?,?,?,1,?) "
                "ON CONFLICT(channel_id) DO UPDATE SET title=excluded.title, username=excluded.username, active=1",
                (channel_id, title or "", username or "", int(last_post_id or 0)),
            )

    def set_leak_channel_active(self, channel_id: int, active: bool):
        with self._get_conn() as conn:
            conn.execute("UPDATE leak_channels SET active=? WHERE channel_id=?", (1 if active else 0, channel_id))

    def remove_leak_channel(self, channel_id: int):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM leak_channels WHERE channel_id=?", (channel_id,))

    def set_leak_channel_last_post(self, channel_id: int, post_id: int):
        """فقط جلو می‌رود؛ هیچ‌وقت به عقب برنمی‌گردد."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE leak_channels SET last_post_id=MAX(last_post_id, ?) WHERE channel_id=?",
                (int(post_id), channel_id),
            )

    # ----- seen posts (جلوگیری از اسکن تکراری) -----------------------------------
    def mark_leak_post_seen(self, channel_id: int, post_id: int) -> bool:
        """True یعنی این پست تازه بود و ثبت شد؛ False یعنی قبلاً دیده شده."""
        with self._get_conn() as conn:
            cur = conn.execute(
                "INSERT OR IGNORE INTO leak_seen_posts (channel_id, post_id) VALUES (?,?)",
                (int(channel_id), int(post_id)),
            )
            if cur.rowcount == 0:
                return False
            conn.execute(
                "DELETE FROM leak_seen_posts WHERE created_at < datetime('now', '-30 days')"
            )
            return True

    # ----- events -----------------------------------------------------------------
    def create_leak_event(self, user_id: int, config_id: int, channel_id: int, channel_title: str,
                          post_link: str, matched_kind: str):
        """id رویداد جدید یا None اگر همین سرویس قبلاً در همین پست ثبت شده بود."""
        with self._get_conn() as conn:
            cur = conn.execute(
                "INSERT OR IGNORE INTO leak_events "
                "(user_id, config_id, channel_id, channel_title, post_link, matched_kind) VALUES (?,?,?,?,?,?)",
                (user_id, config_id, int(channel_id or 0), channel_title or "", post_link, matched_kind or ""),
            )
            return cur.lastrowid if cur.rowcount else None

    def get_leak_event(self, event_id: int):
        with self._get_conn() as conn:
            return conn.execute("SELECT * FROM leak_events WHERE id=?", (event_id,)).fetchone()

    def set_leak_event_status(self, event_id: int, status: str):
        resolved = None if status == "new" else datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._get_conn() as conn:
            conn.execute("UPDATE leak_events SET status=?, resolved_at=? WHERE id=?", (status, resolved, event_id))

    def mark_leak_event_warned(self, event_id: int) -> bool:
        """اخطار را روی رویداد ثبت می‌کند. True اگر تازه ثبت شد، False اگر قبلاً اخطار خورده بود."""
        with self._get_conn() as conn:
            cur = conn.execute(
                "UPDATE leak_events SET warn_count=1 WHERE id=? AND warn_count=0", (event_id,),
            )
            return cur.rowcount > 0

    def count_user_leak_warnings(self, user_id: int) -> int:
        """تعداد رویدادهایی از این کاربر که اخطار گرفته‌اند (شمارنده‌ی اخطار و مسدودسازی)."""
        with self._get_conn() as conn:
            return conn.execute(
                "SELECT COUNT(*) c FROM leak_events WHERE user_id=? AND warn_count>0", (user_id,),
            ).fetchone()["c"]

    def list_leak_events(self, limit: int = 10) -> list:
        with self._get_conn() as conn:
            return conn.execute(
                "SELECT * FROM leak_events ORDER BY id DESC LIMIT ?", (int(limit),),
            ).fetchall()

    def count_leak_events_by_status(self) -> dict:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT status, COUNT(*) c FROM leak_events GROUP BY status").fetchall()
        return {r["status"]: r["c"] for r in rows}

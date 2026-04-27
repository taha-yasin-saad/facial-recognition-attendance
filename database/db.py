import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Optional

from config import DB_PATH, RECOGNITION_COOLDOWN, MIN_HOURS_BEFORE_CHECKOUT, DOOR_ID
from database.models import (
    CREATE_USERS_TABLE, CREATE_ATTENDANCE_TABLE,
    CREATE_UNKNOWN_LOGS_TABLE, CREATE_ATTENDANCE_IDX, CREATE_ATTENDANCE_DATE_IDX,
)


def init_db():
    with get_conn() as conn:
        conn.execute(CREATE_USERS_TABLE)
        conn.execute(CREATE_ATTENDANCE_TABLE)
        conn.execute(CREATE_UNKNOWN_LOGS_TABLE)
        conn.execute(CREATE_ATTENDANCE_IDX)
        conn.execute(CREATE_ATTENDANCE_DATE_IDX)
        try:
            conn.execute("ALTER TABLE unknown_logs ADD COLUMN registered_as TEXT DEFAULT NULL")
        except Exception:
            pass


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Users ──────────────────────────────────────────────────────────────────────

def add_user(user_id: str, full_name: str, department: str,
             role: str = "", email: str = "", photo_path: str = None) -> bool:
    try:
        with get_conn() as conn:
            conn.execute(
                """INSERT INTO users (user_id, full_name, department, role, email, photo_path)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, full_name, department, role, email, photo_path),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def get_user(user_id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None


def get_all_users(department: str = None, active_only: bool = None) -> list[dict]:
    query = "SELECT * FROM users WHERE 1=1"
    params = []
    if department:
        query += " AND department = ?"
        params.append(department)
    if active_only is True:
        query += " AND is_active = 1"
    elif active_only is False:
        query += " AND is_active = 0"
    query += " ORDER BY full_name"
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


def update_user(user_id: str, **fields) -> bool:
    allowed = {"full_name", "department", "role", "email", "photo_path"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return False
    cols = ", ".join(f"{k} = ?" for k in updates)
    with get_conn() as conn:
        conn.execute(
            f"UPDATE users SET {cols} WHERE user_id = ?",
            list(updates.values()) + [user_id],
        )
    return True


def set_user_active(user_id: str, active: bool) -> bool:
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET is_active = ? WHERE user_id = ?",
            (1 if active else 0, user_id),
        )
    return True


def delete_user(user_id: str) -> bool:
    with get_conn() as conn:
        conn.execute("DELETE FROM attendance WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    return True


def get_active_user_ids() -> set[str]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT user_id FROM users WHERE is_active = 1"
        ).fetchall()
        return {r[0] for r in rows}


def get_departments() -> list[str]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT department FROM users ORDER BY department"
        ).fetchall()
        return [r[0] for r in rows]


# ── Attendance ─────────────────────────────────────────────────────────────────

def get_last_event_today(user_id: str) -> Optional[dict]:
    today = datetime.now().strftime("%Y-%m-%d")
    with get_conn() as conn:
        row = conn.execute(
            """SELECT * FROM attendance
               WHERE user_id = ? AND DATE(timestamp) = ?
               ORDER BY timestamp DESC LIMIT 1""",
            (user_id, today),
        ).fetchone()
        return dict(row) if row else None


def is_in_cooldown(user_id: str) -> bool:
    cutoff = (datetime.now() - timedelta(seconds=RECOGNITION_COOLDOWN)).isoformat()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM attendance WHERE user_id = ? AND timestamp >= ?",
            (user_id, cutoff),
        ).fetchone()
        return row is not None


def record_checkin(user_id: str, method: str = "face_recognition") -> dict:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO attendance (user_id, door_id, event_type, method, timestamp)
               VALUES (?, ?, 'check_in', ?, ?)""",
            (user_id, DOOR_ID, method, ts),
        )
    return {"event_type": "check_in", "timestamp": ts}


def record_checkout(user_id: str, checkin_ts: str, method: str = "face_recognition") -> dict:
    checkin_dt = datetime.fromisoformat(checkin_ts)
    now = datetime.now()
    ts = now.strftime("%Y-%m-%d %H:%M:%S")
    worked = round((now - checkin_dt).total_seconds() / 3600, 2)
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO attendance (user_id, door_id, event_type, timestamp, worked_hours, method)
               VALUES (?, ?, 'check_out', ?, ?, ?)""",
            (user_id, DOOR_ID, ts, worked, method),
        )
    return {"event_type": "check_out", "timestamp": ts, "worked_hours": worked}


def _has_checkout_today(user_id: str) -> bool:
    today = datetime.now().strftime("%Y-%m-%d")
    with get_conn() as conn:
        row = conn.execute(
            """SELECT 1 FROM attendance
               WHERE user_id = ? AND event_type = 'check_out' AND DATE(timestamp) = ?
               LIMIT 1""",
            (user_id, today),
        ).fetchone()
        return row is not None


def determine_next_event(user_id: str) -> Optional[str]:
    """Return 'check_in', 'check_out', or None (cooldown / too soon)."""
    if is_in_cooldown(user_id):
        return None
    last = get_last_event_today(user_id)
    if last is None:
        return "check_in"
    if last["event_type"] == "check_out":
        return "check_in"
    if last["event_type"] == "check_in":
        if not _has_checkout_today(user_id):
            checkin_dt = datetime.fromisoformat(last["timestamp"])
            hours_since = (datetime.now() - checkin_dt).total_seconds() / 3600
            if hours_since < MIN_HOURS_BEFORE_CHECKOUT:
                return None
        return "check_out"
    return None


def get_checkin_record_today(user_id: str) -> Optional[dict]:
    """Return the current session's check-in (most recent unmatched check_in today)."""
    today = datetime.now().strftime("%Y-%m-%d")
    with get_conn() as conn:
        row = conn.execute(
            """SELECT * FROM attendance
               WHERE user_id = ? AND DATE(timestamp) = ? AND event_type = 'check_in'
                 AND NOT EXISTS (
                   SELECT 1 FROM attendance a2
                   WHERE a2.user_id = attendance.user_id
                     AND a2.event_type = 'check_out'
                     AND a2.id > attendance.id
                     AND DATE(a2.timestamp) = ?
                 )
               ORDER BY timestamp DESC LIMIT 1""",
            (user_id, today, today),
        ).fetchone()
        return dict(row) if row else None


def get_total_hours_today(user_id: str) -> float:
    """Sum of worked_hours across all checkout sessions today."""
    today = datetime.now().strftime("%Y-%m-%d")
    with get_conn() as conn:
        row = conn.execute(
            """SELECT ROUND(SUM(COALESCE(worked_hours, 0)), 2) FROM attendance
               WHERE user_id = ? AND event_type = 'check_out' AND DATE(timestamp) = ?""",
            (user_id, today),
        ).fetchone()
        return row[0] or 0.0


def get_user_total_hours_alltime(user_id: str) -> float:
    """Sum of all worked_hours across every checkout ever recorded for the user."""
    with get_conn() as conn:
        row = conn.execute(
            """SELECT ROUND(SUM(COALESCE(worked_hours, 0)), 4) FROM attendance
               WHERE user_id = ? AND event_type = 'check_out'""",
            (user_id,),
        ).fetchone()
        return row[0] or 0.0


def get_user_total_days_alltime(user_id: str) -> int:
    """Count of distinct days the user has checked in."""
    with get_conn() as conn:
        row = conn.execute(
            """SELECT COUNT(DISTINCT DATE(timestamp)) FROM attendance
               WHERE user_id = ? AND event_type = 'check_in'""",
            (user_id,),
        ).fetchone()
        return row[0] or 0


def get_attendance_log(date: str = None, user_id: str = None,
                       department: str = None, event_type: str = None,
                       date_from: str = None, date_to: str = None,
                       limit: int = 500, offset: int = 0) -> list[dict]:
    query = """
        SELECT a.id, a.user_id, u.full_name, u.department, u.role,
               a.door_id, a.event_type, a.timestamp, a.worked_hours, a.method
        FROM attendance a JOIN users u ON a.user_id = u.user_id
        WHERE 1=1
    """
    params = []
    if date:
        query += " AND DATE(a.timestamp) = ?"
        params.append(date)
    if date_from:
        query += " AND DATE(a.timestamp) >= ?"
        params.append(date_from)
    if date_to:
        query += " AND DATE(a.timestamp) <= ?"
        params.append(date_to)
    if user_id:
        query += " AND a.user_id = ?"
        params.append(user_id)
    if department:
        query += " AND u.department = ?"
        params.append(department)
    if event_type:
        query += " AND a.event_type = ?"
        params.append(event_type)
    query += " ORDER BY a.timestamp DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


def get_present_now() -> list[dict]:
    """Users currently inside: last event today is a check_in."""
    today = datetime.now().strftime("%Y-%m-%d")
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT u.user_id, u.full_name, u.department, u.role, u.photo_path,
                   a.timestamp AS checkin_time
            FROM attendance a
            JOIN users u ON a.user_id = u.user_id
            WHERE a.event_type = 'check_in' AND DATE(a.timestamp) = ?
              AND NOT EXISTS (
                SELECT 1 FROM attendance a2
                WHERE a2.user_id = a.user_id
                  AND a2.event_type = 'check_out'
                  AND a2.id > a.id
                  AND DATE(a2.timestamp) = ?
              )
            ORDER BY a.timestamp ASC
        """, (today, today)).fetchall()
        return [dict(r) for r in rows]


def get_stats_today() -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    with get_conn() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM users WHERE is_active = 1"
        ).fetchone()[0]
        present = conn.execute(
            """SELECT COUNT(DISTINCT user_id) FROM attendance
               WHERE event_type = 'check_in' AND DATE(timestamp) = ?""",
            (today,),
        ).fetchone()[0]
        inside = conn.execute(
            """SELECT COUNT(DISTINCT a.user_id) FROM attendance a
               WHERE a.event_type = 'check_in' AND DATE(a.timestamp) = ?
                 AND NOT EXISTS (
                   SELECT 1 FROM attendance a2
                   WHERE a2.user_id = a.user_id
                     AND a2.event_type = 'check_out'
                     AND a2.id > a.id
                     AND DATE(a2.timestamp) = ?
                 )""",
            (today, today),
        ).fetchone()[0]
        unknown_alerts = conn.execute(
            "SELECT COUNT(*) FROM unknown_logs WHERE DATE(timestamp) = ?",
            (today,),
        ).fetchone()[0]
    return {
        "date": today,
        "total_users": total,
        "present": present,
        "checked_out": present - inside,
        "inside": inside,
        "absent": total - present,
        "unknown_alerts": unknown_alerts,
    }


def get_hourly_checkins(date: str = None) -> list[dict]:
    target = date or datetime.now().strftime("%Y-%m-%d")
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT STRFTIME('%H', timestamp) AS hour, COUNT(*) AS count
            FROM attendance
            WHERE event_type = 'check_in' AND DATE(timestamp) = ?
            GROUP BY hour ORDER BY hour
        """, (target,)).fetchall()
        return [dict(r) for r in rows]


def get_monthly_report(month: str) -> list[dict]:
    """month = 'YYYY-MM'. Returns per-user summary."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT u.user_id, u.full_name, u.department,
                   COUNT(DISTINCT DATE(a.timestamp)) AS days_present,
                   ROUND(SUM(COALESCE(a.worked_hours, 0)), 2) AS total_hours
            FROM users u
            LEFT JOIN attendance a
              ON a.user_id = u.user_id
             AND STRFTIME('%Y-%m', a.timestamp) = ?
             AND a.event_type = 'check_out'
            WHERE u.is_active = 1
            GROUP BY u.user_id
            ORDER BY u.full_name
        """, (month,)).fetchall()
        return [dict(r) for r in rows]


def get_monthly_daily_counts(month: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT DATE(timestamp) AS day, COUNT(DISTINCT user_id) AS count
            FROM attendance
            WHERE event_type = 'check_in' AND STRFTIME('%Y-%m', timestamp) = ?
            GROUP BY day ORDER BY day
        """, (month,)).fetchall()
        return [dict(r) for r in rows]


def get_dept_monthly_hours(month: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT u.department,
                   ROUND(SUM(COALESCE(a.worked_hours, 0)), 2) AS total_hours
            FROM users u
            LEFT JOIN attendance a
              ON a.user_id = u.user_id
             AND STRFTIME('%Y-%m', a.timestamp) = ?
             AND a.event_type = 'check_out'
            WHERE u.is_active = 1
            GROUP BY u.department
            ORDER BY u.department
        """, (month,)).fetchall()
        return [dict(r) for r in rows]


def get_user_attendance_history(user_id: str, limit: int = 60) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT event_type, timestamp, worked_hours, door_id
            FROM attendance WHERE user_id = ?
            ORDER BY timestamp DESC LIMIT ?
        """, (user_id, limit)).fetchall()
        return [dict(r) for r in rows]


def get_user_monthly_hours(user_id: str, months: int = 6) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT STRFTIME('%Y-%m', timestamp) AS month,
                   ROUND(SUM(COALESCE(worked_hours, 0)), 2) AS hours
            FROM attendance
            WHERE user_id = ? AND event_type = 'check_out'
            GROUP BY month ORDER BY month DESC LIMIT ?
        """, (user_id, months)).fetchall()
        return [dict(r) for r in rows]


# ── Unknown logs ───────────────────────────────────────────────────────────────

def log_unknown_face(snapshot_path: str = None):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO unknown_logs (snapshot_path, timestamp) VALUES (?, ?)",
            (snapshot_path, ts),
        )


def get_unknown_logs(unregistered_only: bool = False, limit: int = 50, offset: int = 0) -> list[dict]:
    query = "SELECT * FROM unknown_logs"
    if unregistered_only:
        query += " WHERE registered_as IS NULL"
    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    with get_conn() as conn:
        rows = conn.execute(query, (limit, offset)).fetchall()
        return [dict(r) for r in rows]


def get_unknown_log(log_id: int) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM unknown_logs WHERE id = ?", (log_id,)).fetchone()
        return dict(row) if row else None


def mark_unknown_registered(log_id: int, user_id: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE unknown_logs SET registered_as = ? WHERE id = ?",
            (user_id, log_id),
        )


def next_guest_id() -> str:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM users WHERE department = 'Guest'"
        ).fetchone()
        n = (row[0] or 0) + 1
        return f"GUEST{n:03d}"

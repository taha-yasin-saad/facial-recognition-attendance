CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER  PRIMARY KEY AUTOINCREMENT,
    user_id       TEXT     NOT NULL UNIQUE,
    full_name     TEXT     NOT NULL,
    department    TEXT     NOT NULL,
    role          TEXT     NOT NULL DEFAULT '',
    email         TEXT     NOT NULL DEFAULT '',
    photo_path    TEXT     DEFAULT NULL,
    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active     INTEGER  NOT NULL DEFAULT 1
);
"""

CREATE_ATTENDANCE_TABLE = """
CREATE TABLE IF NOT EXISTS attendance (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      TEXT    NOT NULL,
    door_id      TEXT    NOT NULL DEFAULT 'MAIN_ENTRANCE',
    event_type   TEXT    NOT NULL CHECK(event_type IN ('check_in', 'check_out')),
    timestamp    DATETIME DEFAULT CURRENT_TIMESTAMP,
    worked_hours REAL    DEFAULT NULL,
    method       TEXT    NOT NULL DEFAULT 'face_recognition',
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
"""

CREATE_UNKNOWN_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS unknown_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
    snapshot_path TEXT DEFAULT NULL
);
"""

CREATE_ATTENDANCE_IDX = """
CREATE INDEX IF NOT EXISTS idx_att_user_ts ON attendance (user_id, timestamp);
"""

CREATE_ATTENDANCE_DATE_IDX = """
CREATE INDEX IF NOT EXISTS idx_att_date ON attendance (date(timestamp));
"""

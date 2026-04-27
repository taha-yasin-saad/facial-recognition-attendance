"""
User story test: Check-in → Break → Return → Check-out
Simulates a full workday with fabricated timestamps.

Scenario:
  08:00  Employee arrives         → check_in
  12:00  Employee leaves for lunch → check_out  (4h worked)
  13:00  Employee returns         → check_in   (1h break)
  17:30  Employee leaves for day  → check_out  (4h 30m worked)

Expected:
  Session 1 worked: 4h 00m 00s
  Session 2 worked: 4h 30m 00s
  Total today:      8h 30m 00s
  Break (excluded): 1h 00m 00s
"""

import sqlite3
from datetime import datetime, timedelta
from database.db import (
    init_db, get_conn,
    determine_next_event, record_checkin, record_checkout,
    get_checkin_record_today, get_total_hours_today,
    get_present_now, get_stats_today, _has_checkout_today,
)
from config import DB_PATH, DOOR_ID

EMPLOYEE_ID = "EMP001"
TODAY = datetime.now().strftime("%Y-%m-%d")

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def hms(decimal_hours):
    if decimal_hours is None:
        return "—"
    total_s = int(round(float(decimal_hours) * 3600))
    h = total_s // 3600
    m = (total_s % 3600) // 60
    s = total_s % 60
    return f"{h}h {m:02d}m {s:02d}s"

def ok(msg):   print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg): print(f"  {RED}✗{RESET} {msg}")
def info(msg): print(f"  {CYAN}→{RESET} {msg}")
def step(msg): print(f"\n{BOLD}{YELLOW}[ {msg} ]{RESET}")

def assert_eq(label, got, expected):
    if abs(float(got or 0) - float(expected)) < 0.01:
        ok(f"{label}: {hms(got)}")
    else:
        fail(f"{label}: expected {hms(expected)}, got {hms(got)}")

def insert_event(employee_id, event_type, ts, worked_hours=None):
    """Insert an attendance row with a specific timestamp."""
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO attendance (employee_id, door_id, event_type, timestamp, worked_hours, method)
               VALUES (?, ?, ?, ?, ?, 'test')""",
            (employee_id, DOOR_ID, event_type, ts, worked_hours),
        )

def clear_today(employee_id):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM attendance WHERE employee_id = ? AND DATE(timestamp) = ? AND method = 'test'",
            (employee_id, TODAY),
        )

def also_clear_face_recognition(employee_id):
    """Clear any real events from today so tests are isolated."""
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM attendance WHERE employee_id = ? AND DATE(timestamp) = ?",
            (employee_id, TODAY),
        )

# ──────────────────────────────────────────────────────────────────────────────

init_db()
print(f"\n{BOLD}UniAttend — User Story Test{RESET}")
print(f"Employee: {EMPLOYEE_ID}  |  Date: {TODAY}")
print("-" * 60)

also_clear_face_recognition(EMPLOYEE_ID)

# ─────────────────────────────────────────────────────────────
step("STEP 1 — Employee arrives at 08:00 (first check-in)")
ts_in1 = f"{TODAY} 08:00:00"
insert_event(EMPLOYEE_ID, "check_in", ts_in1)
info(f"Inserted check_in at {ts_in1}")

present = get_present_now()
inside_ids = [p["employee_id"] for p in present]
if EMPLOYEE_ID in inside_ids:
    ok("Employee shows as currently inside")
else:
    fail(f"Employee NOT in present list: {inside_ids}")

stats = get_stats_today()
info(f"Stats → inside={stats['inside']}, present={stats['present']}, absent={stats['absent']}")
if stats["inside"] == 1:
    ok("Stats: inside=1")
else:
    fail(f"Stats: expected inside=1, got {stats['inside']}")

# ─────────────────────────────────────────────────────────────
step("STEP 2 — Lunch break at 12:00 (first check-out after 4h)")
ts_out1 = f"{TODAY} 12:00:00"
session1_h = 4.0   # 12:00 - 08:00
insert_event(EMPLOYEE_ID, "check_out", ts_out1, worked_hours=session1_h)
info(f"Inserted check_out at {ts_out1}  →  session worked: {hms(session1_h)}")

present = get_present_now()
inside_ids = [p["employee_id"] for p in present]
if EMPLOYEE_ID not in inside_ids:
    ok("Employee no longer inside during break")
else:
    fail("Employee still shown as inside (should be on break)")

stats = get_stats_today()
info(f"Stats → inside={stats['inside']}, present={stats['present']}, checked_out={stats['checked_out']}")
if stats["inside"] == 0 and stats["present"] == 1 and stats["checked_out"] == 1:
    ok("Stats: inside=0, present=1, checked_out=1")
else:
    fail(f"Stats mismatch: {stats}")

total = get_total_hours_today(EMPLOYEE_ID)
assert_eq("Total hours after session 1", total, 4.0)

# ─────────────────────────────────────────────────────────────
step("STEP 3 — Employee returns from lunch at 13:00 (second check-in)")
ts_in2 = f"{TODAY} 13:00:00"
insert_event(EMPLOYEE_ID, "check_in", ts_in2)
info(f"Inserted check_in at {ts_in2}  (break was 1h)")

present = get_present_now()
inside_ids = [p["employee_id"] for p in present]
if EMPLOYEE_ID in inside_ids:
    ok("Employee back inside after break")
else:
    fail("Employee NOT showing as inside after returning")

# Check the current session's check-in is the 13:00 one, not 08:00
current_checkin = get_checkin_record_today(EMPLOYEE_ID)
if current_checkin and current_checkin["timestamp"].startswith(f"{TODAY} 13:"):
    ok(f"Current session check-in correctly points to 13:00 (not 08:00)")
else:
    fail(f"Current session check-in wrong: {current_checkin}")

stats = get_stats_today()
info(f"Stats → inside={stats['inside']}, present={stats['present']}")
if stats["inside"] == 1 and stats["present"] == 1:
    ok("Stats: inside=1, present=1")
else:
    fail(f"Stats mismatch: {stats}")

# ─────────────────────────────────────────────────────────────
step("STEP 4 — Employee leaves at 17:30 (second check-out after 4h 30m)")
ts_out2 = f"{TODAY} 17:30:00"
session2_h = 4.5   # 17:30 - 13:00
insert_event(EMPLOYEE_ID, "check_out", ts_out2, worked_hours=session2_h)
info(f"Inserted check_out at {ts_out2}  →  session worked: {hms(session2_h)}")

present = get_present_now()
if EMPLOYEE_ID not in [p["employee_id"] for p in present]:
    ok("Employee no longer inside after final check-out")
else:
    fail("Employee still showing as inside")

total = get_total_hours_today(EMPLOYEE_ID)
expected_total = 8.5  # 4.0 + 4.5
assert_eq("Total hours for the day", total, expected_total)

stats = get_stats_today()
info(f"Stats → inside={stats['inside']}, present={stats['present']}, checked_out={stats['checked_out']}, absent={stats['absent']}")
if stats["inside"] == 0 and stats["checked_out"] == 1:
    ok("Stats: inside=0, checked_out=1 (left for the day)")
else:
    fail(f"Stats mismatch: {stats}")

# ─────────────────────────────────────────────────────────────
step("STEP 5 — determine_next_event logic checks")
from unittest.mock import patch
from datetime import timezone

# Simulate: last event is check_out → should offer check_in (break return)
next_ev = determine_next_event(EMPLOYEE_ID)
# Currently last event is check_out at 17:30, cooldown is 5 min
# Since 17:30 is far in the past (simulated), cooldown won't fire unless we're unlucky
# We'll just check the logic path directly
info(f"determine_next_event after final checkout: '{next_ev}'")
if next_ev == "check_in":
    ok("After check-out → next event is check_in (can return / re-enter)")
elif next_ev is None:
    info("Result is None (cooldown active from face recognition session — expected if run recently)")
else:
    fail(f"Unexpected next event: {next_ev}")

# ─────────────────────────────────────────────────────────────
step("SUMMARY")
print()
print(f"  {'Event':<30} {'Time':<12} {'Session Hours'}")
print(f"  {'-'*30} {'-'*12} {'-'*20}")
events = [
    ("Check-in (arrive)",     "08:00",  "-"),
    ("Check-out (lunch)",     "12:00",  hms(4.0)),
    ("--- Break (1h) ---",    "",       ""),
    ("Check-in (return)",     "13:00",  "-"),
    ("Check-out (leave)",     "17:30",  hms(4.5)),
]
for label, time, hrs in events:
    print(f"  {label:<30} {time:<12} {hrs}")
print()
total = get_total_hours_today(EMPLOYEE_ID)
print(f"  {'Total worked (excl. break)':<42} {hms(total)}")
print(f"  {'Break time (excluded)':<42} {hms(1.0)}")
print()

# Cleanup
clear_today(EMPLOYEE_ID)
info("Test records cleaned up from database")
print()

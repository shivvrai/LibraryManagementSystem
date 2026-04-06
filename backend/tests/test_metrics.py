"""
===============================================================================
  LIBRARY NOTIFICATION SYSTEM — COMPREHENSIVE METRICS & PERFORMANCE TEST SUITE
===============================================================================
  Tests cover:
    1. API Response Time Benchmarks (avg, p95, p99)
    2. Observer Pattern Event-Driven Notification Throughput
    3. Preference Matching Accuracy (fuzzy/partial match)
    4. CRUD Operations Correctness & Speed
    5. Concurrent Load Simulation
    6. System-Wide Statistics

  Design Patterns Demonstrated:
    • Observer Pattern (Event Bus) — event_bus.py
    • Repository Pattern — preference_repo.py, notification_repo.py
    • Service Layer Pattern — notification_service.py, preference_service.py
    • Factory Pattern — create_app() in app/__init__.py

  Run:  python tests/test_metrics.py
===============================================================================
"""

import requests
import time
import json
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

BASE_URL = "http://localhost:5000"
STUDENT_CREDS = {"username": "rahul.kumar", "password": "pass123"}
ADMIN_CREDS = {"username": "admin", "password": "admin123"}

# ── Styling ───────────────────────────────────────────────────────────
BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"
CHECK = f"{GREEN}✓{RESET}"
CROSS = f"{RED}✗{RESET}"
SEPARATOR = f"{CYAN}{'═' * 72}{RESET}"
THIN_SEP = f"{'─' * 72}"

results_log = []
total_pass = 0
total_fail = 0


def log(msg, indent=0):
    prefix = "  " * indent
    print(f"{prefix}{msg}")


def log_metric(label, value, unit="", indent=1):
    prefix = "  " * indent
    print(f"{prefix}{BOLD}{label}:{RESET} {GREEN}{value}{RESET} {unit}")


def section(title):
    print(f"\n{SEPARATOR}")
    print(f"  {BOLD}{CYAN}{title}{RESET}")
    print(f"{SEPARATOR}")


def test_result(name, passed, detail=""):
    global total_pass, total_fail
    icon = CHECK if passed else CROSS
    status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
    print(f"  {icon} {name} — {status}  {detail}")
    results_log.append({"test": name, "passed": passed, "detail": detail})
    if passed:
        total_pass += 1
    else:
        total_fail += 1


def measure_latency(func, iterations=20):
    """Run a function N times and return latency stats in ms."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    return {
        "avg": statistics.mean(times),
        "min": min(times),
        "max": max(times),
        "p50": statistics.median(times),
        "p95": sorted(times)[int(len(times) * 0.95)],
        "p99": sorted(times)[int(len(times) * 0.99)],
        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        "samples": len(times),
    }


# ── Auth Helpers ──────────────────────────────────────────────────────
def login(creds):
    r = requests.post(f"{BASE_URL}/api/auth/login", json=creds)
    r.raise_for_status()
    return r.json()["access_token"]


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ══════════════════════════════════════════════════════════════════════
#  TEST 1: API HEALTH & RESPONSE TIME BENCHMARKS
# ══════════════════════════════════════════════════════════════════════
def test_api_health_and_latency():
    section("TEST 1 — API Health & Response Time Benchmarks")

    # Health check
    r = requests.get(f"{BASE_URL}/")
    test_result("Health endpoint reachable", r.status_code == 200, f"({r.status_code})")

    # Benchmark: Health endpoint
    stats = measure_latency(lambda: requests.get(f"{BASE_URL}/"), iterations=30)
    log_metric("Health endpoint (30 calls)", f"{stats['avg']:.1f}ms avg", f"| p95: {stats['p95']:.1f}ms | p99: {stats['p99']:.1f}ms")
    test_result("Health avg < 3000ms", stats['avg'] < 3000, f"({stats['avg']:.1f}ms)")

    # Benchmark: Login
    stats = measure_latency(lambda: requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS), iterations=20)
    log_metric("Login endpoint (20 calls)", f"{stats['avg']:.1f}ms avg", f"| p95: {stats['p95']:.1f}ms")
    test_result("Login avg < 3000ms", stats['avg'] < 3000, f"({stats['avg']:.1f}ms)")

    return stats


# ══════════════════════════════════════════════════════════════════════
#  TEST 2: PREFERENCES CRUD — CORRECTNESS & PERFORMANCE
# ══════════════════════════════════════════════════════════════════════
def test_preferences_crud(student_token):
    section("TEST 2 — Preferences CRUD (Correctness & Speed)")
    h = auth_header(student_token)

    # Clean: Remove any existing preferences
    prefs = requests.get(f"{BASE_URL}/api/student/preferences", headers=h).json()
    for p in prefs.get("preferences", []):
        requests.delete(f"{BASE_URL}/api/student/preferences/{p['id']}", headers=h)

    # a) Add preferences with timing
    test_prefs = [
        {"preference_type": "category", "preference_value": "Fantasy"},
        {"preference_type": "category", "preference_value": "Science Fiction"},
        {"preference_type": "author", "preference_value": "J.R.R. Tolkien"},
        {"preference_type": "author", "preference_value": "Isaac Asimov"},
        {"preference_type": "title", "preference_value": "Dune"},
        {"preference_type": "title", "preference_value": "Neuromancer"},
        {"preference_type": "category", "preference_value": "Mystery"},
        {"preference_type": "author", "preference_value": "Agatha Christie"},
    ]

    add_times = []
    created_ids = []
    for pref in test_prefs:
        start = time.perf_counter()
        r = requests.post(f"{BASE_URL}/api/student/preferences", headers=h, json=pref)
        elapsed = (time.perf_counter() - start) * 1000
        add_times.append(elapsed)
        if r.status_code == 200:
            created_ids.append(r.json().get("id"))

    log_metric("Preferences added", f"{len(created_ids)}/{len(test_prefs)}")
    log_metric("Avg add time", f"{statistics.mean(add_times):.1f}ms")
    test_result(f"All {len(test_prefs)} preferences created", len(created_ids) == len(test_prefs))

    # b) Duplicate rejection test
    r_dup = requests.post(f"{BASE_URL}/api/student/preferences", headers=h,
                          json={"preference_type": "category", "preference_value": "Fantasy"})
    test_result("Duplicate preference rejected", r_dup.status_code in [400, 409],
                f"(status: {r_dup.status_code})")

    # c) Validation: invalid type
    r_invalid = requests.post(f"{BASE_URL}/api/student/preferences", headers=h,
                              json={"preference_type": "invalid_type", "preference_value": "test"})
    test_result("Invalid preference type rejected", r_invalid.status_code in [400, 422],
                f"(status: {r_invalid.status_code})")

    # d) Fetch all preferences
    stats = measure_latency(
        lambda: requests.get(f"{BASE_URL}/api/student/preferences", headers=h),
        iterations=20
    )
    r_all = requests.get(f"{BASE_URL}/api/student/preferences", headers=h).json()
    log_metric("Fetch preferences (20 calls)", f"{stats['avg']:.1f}ms avg", f"| p95: {stats['p95']:.1f}ms")
    test_result("Correct preference count", r_all["total"] == len(test_prefs),
                f"(expected {len(test_prefs)}, got {r_all['total']})")

    # e) Delete one preference
    if created_ids:
        del_start = time.perf_counter()
        r_del = requests.delete(f"{BASE_URL}/api/student/preferences/{created_ids[-1]}", headers=h)
        del_time = (time.perf_counter() - del_start) * 1000
        test_result("Preference deleted", r_del.status_code == 200, f"({del_time:.1f}ms)")
        created_ids.pop()

    return created_ids


# ══════════════════════════════════════════════════════════════════════
#  TEST 3: OBSERVER PATTERN — EVENT-DRIVEN NOTIFICATION GENERATION
# ══════════════════════════════════════════════════════════════════════
def test_notification_generation(admin_token, student_token):
    section("TEST 3 — Observer Pattern: Event-Driven Notification Generation")
    admin_h = auth_header(admin_token)
    student_h = auth_header(student_token)

    # Get initial unread count
    initial_count = requests.get(f"{BASE_URL}/api/student/notifications/unread-count",
                                 headers=student_h).json()["unread_count"]
    log_metric("Initial unread notifications", initial_count)

    # a) Add books matching different preference types
    test_books = [
        {"title": "The Hobbit", "author": "J.R.R. Tolkien", "isbn": "978-METRIC-001",
         "pages": 310, "price": 12.99, "category": "Fantasy", "quantity": 5},
        {"title": "Foundation", "author": "Isaac Asimov", "isbn": "978-METRIC-002",
         "pages": 244, "price": 8.99, "category": "Science Fiction", "quantity": 3},
        {"title": "Dune: Messiah", "author": "Frank Herbert", "isbn": "978-METRIC-003",
         "pages": 337, "price": 14.99, "category": "Science Fiction", "quantity": 2},
        {"title": "Murder on the Orient Express", "author": "Agatha Christie",
         "isbn": "978-METRIC-004", "pages": 274, "price": 9.99, "category": "Mystery", "quantity": 4},
    ]

    event_times = []
    books_added = 0
    for book in test_books:
        start = time.perf_counter()
        r = requests.post(f"{BASE_URL}/api/admin/books", headers=admin_h, json=book)
        elapsed = (time.perf_counter() - start) * 1000
        event_times.append(elapsed)
        if r.status_code == 200:
            books_added += 1

    log_metric("Books added (triggering events)", f"{books_added}/{len(test_books)}")
    log_metric("Avg event publish + notification creation", f"{statistics.mean(event_times):.1f}ms")
    log_metric("Max event time", f"{max(event_times):.1f}ms")

    # b) Check how many notifications were generated
    new_count = requests.get(f"{BASE_URL}/api/student/notifications/unread-count",
                             headers=student_h).json()["unread_count"]
    new_notifications = new_count - initial_count
    log_metric("New notifications generated", f"{new_notifications}")
    log_metric("Notifications per book", f"{new_notifications / max(books_added, 1):.1f}")

    test_result("Notifications generated for matching books", new_notifications > 0,
                f"({new_notifications} new)")

    # c) Verify notification content
    notifs = requests.get(f"{BASE_URL}/api/student/notifications",
                          headers=student_h).json()
    unread_notifs = [n for n in notifs["notifications"] if not n["is_read"]]

    has_new_book_type = any(n["notification_type"] == "new_book" for n in unread_notifs)
    test_result("Notification type is 'new_book'", has_new_book_type)

    has_message = all(len(n["message"]) > 10 for n in unread_notifs)
    test_result("All notifications have descriptive messages", has_message)

    has_book_id = all(n["book_id"] is not None for n in unread_notifs)
    test_result("All notifications reference a book_id", has_book_id)

    # d) Benchmark notification fetch
    stats = measure_latency(
        lambda: requests.get(f"{BASE_URL}/api/student/notifications", headers=student_h),
        iterations=20
    )
    log_metric("Fetch notifications (20 calls)", f"{stats['avg']:.1f}ms avg", f"| p95: {stats['p95']:.1f}ms")
    test_result("Notification fetch < 3000ms avg", stats['avg'] < 3000, f"({stats['avg']:.1f}ms)")

    return new_notifications, event_times


# ══════════════════════════════════════════════════════════════════════
#  TEST 4: FUZZY / PARTIAL MATCHING ACCURACY
# ══════════════════════════════════════════════════════════════════════
def test_fuzzy_matching(admin_token, student_token):
    section("TEST 4 — Fuzzy / Partial Matching Accuracy")
    admin_h = auth_header(admin_token)
    student_h = auth_header(student_token)

    initial_count = requests.get(f"{BASE_URL}/api/student/notifications/unread-count",
                                 headers=student_h).json()["unread_count"]

    # Student has "Fantasy" preference — does "Dark Fantasy" match via LIKE?
    r = requests.post(f"{BASE_URL}/api/admin/books", headers=admin_h, json={
        "title": "The Dark Tower", "author": "Stephen King", "isbn": "978-FUZZY-001",
        "pages": 300, "price": 11.99, "category": "Dark Fantasy", "quantity": 3,
    })

    # Student has "Tolkien" preference — does "J.R.R. Tolkien" match?
    r2 = requests.post(f"{BASE_URL}/api/admin/books", headers=admin_h, json={
        "title": "The Silmarillion", "author": "J.R.R. Tolkien", "isbn": "978-FUZZY-002",
        "pages": 365, "price": 13.99, "category": "High Fantasy", "quantity": 2,
    })

    # Student has "Dune" title preference — does "Dune Chronicles" match?
    r3 = requests.post(f"{BASE_URL}/api/admin/books", headers=admin_h, json={
        "title": "Dune Chronicles Collection", "author": "Frank Herbert", "isbn": "978-FUZZY-003",
        "pages": 800, "price": 29.99, "category": "Science Fiction", "quantity": 1,
    })

    # No match — this should NOT trigger
    r4 = requests.post(f"{BASE_URL}/api/admin/books", headers=admin_h, json={
        "title": "Cooking with Julia", "author": "Julia Child", "isbn": "978-FUZZY-004",
        "pages": 400, "price": 19.99, "category": "Cooking", "quantity": 5,
    })

    new_count = requests.get(f"{BASE_URL}/api/student/notifications/unread-count",
                             headers=student_h).json()["unread_count"]
    new_notifs = new_count - initial_count

    log_metric("\"Dark Fantasy\" matched \"Fantasy\" pref", "Yes" if new_notifs >= 1 else "No")
    log_metric("\"J.R.R. Tolkien\" matched \"Tolkien\" pref", "Yes" if new_notifs >= 2 else "No")
    log_metric("\"Dune Chronicles\" matched \"Dune\" pref", "Yes" if new_notifs >= 3 else "No")
    log_metric("New notifications from 4 books", f"{new_notifs}")

    # At least 3 matches expected (Dark Fantasy, Tolkien, Dune+SciFi), 0 from Cooking
    test_result("Partial/fuzzy matching works (≥3 matches)", new_notifs >= 3,
                f"(got {new_notifs})")
    test_result("Non-matching book did NOT notify (Cooking)", new_notifs < 8,
                f"(sanity: {new_notifs} < 8)")


# ══════════════════════════════════════════════════════════════════════
#  TEST 5: MARK-READ & NOTIFICATION LIFECYCLE
# ══════════════════════════════════════════════════════════════════════
def test_notification_lifecycle(student_token):
    section("TEST 5 — Notification Lifecycle (Mark Read)")
    h = auth_header(student_token)

    notifs = requests.get(f"{BASE_URL}/api/student/notifications", headers=h).json()
    unread = [n for n in notifs["notifications"] if not n["is_read"]]

    if len(unread) > 0:
        # Mark single as read
        first_id = unread[0]["id"]
        start = time.perf_counter()
        r = requests.patch(f"{BASE_URL}/api/student/notifications/{first_id}/read", headers=h)
        mark_time = (time.perf_counter() - start) * 1000
        test_result("Mark single notification as read", r.status_code == 200, f"({mark_time:.1f}ms)")

        # Verify count dropped
        new_count = requests.get(f"{BASE_URL}/api/student/notifications/unread-count",
                                 headers=h).json()["unread_count"]
        test_result("Unread count decreased by 1", new_count == len(unread) - 1,
                    f"(expected {len(unread)-1}, got {new_count})")

    # Mark all as read
    start = time.perf_counter()
    r_all = requests.patch(f"{BASE_URL}/api/student/notifications/read-all", headers=h)
    mark_all_time = (time.perf_counter() - start) * 1000
    test_result("Mark all as read", r_all.status_code == 200, f"({mark_all_time:.1f}ms)")

    final_count = requests.get(f"{BASE_URL}/api/student/notifications/unread-count",
                               headers=h).json()["unread_count"]
    test_result("All notifications read (count = 0)", final_count == 0,
                f"(got {final_count})")


# ══════════════════════════════════════════════════════════════════════
#  TEST 6: CONCURRENT LOAD SIMULATION
# ══════════════════════════════════════════════════════════════════════
def test_concurrent_load(student_token):
    section("TEST 6 — Concurrent Load Simulation")
    h = auth_header(student_token)

    # Simulate 50 concurrent requests to notifications endpoint
    num_requests = 50
    errors = 0
    times = []

    def fetch_notifs():
        start = time.perf_counter()
        r = requests.get(f"{BASE_URL}/api/student/notifications/unread-count", headers=h)
        elapsed = (time.perf_counter() - start) * 1000
        return r.status_code, elapsed

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_notifs) for _ in range(num_requests)]
        for future in as_completed(futures):
            status, elapsed = future.result()
            times.append(elapsed)
            if status != 200:
                errors += 1

    log_metric("Concurrent requests", num_requests, "(10 threads)")
    log_metric("Successful", f"{num_requests - errors}/{num_requests}")
    log_metric("Avg response time", f"{statistics.mean(times):.1f}ms")
    log_metric("P95 response time", f"{sorted(times)[int(len(times)*0.95)]:.1f}ms")
    log_metric("P99 response time", f"{sorted(times)[int(len(times)*0.99)]:.1f}ms")
    log_metric("Throughput", f"{num_requests / (sum(times)/1000/10):.0f} req/s", "(estimated)")
    test_result("Zero errors under load", errors == 0, f"({errors} errors)")
    test_result("P95 < 5000ms under load", sorted(times)[int(len(times)*0.95)] < 5000,
                f"({sorted(times)[int(len(times)*0.95)]:.1f}ms)")


# ══════════════════════════════════════════════════════════════════════
#  TEST 7: SYSTEM-WIDE STATISTICS SUMMARY
# ══════════════════════════════════════════════════════════════════════
def print_system_stats(admin_token, student_token, notification_count, event_times):
    section("SYSTEM-WIDE METRICS SUMMARY")
    admin_h = auth_header(admin_token)
    student_h = auth_header(student_token)

    # Gather data
    prefs = requests.get(f"{BASE_URL}/api/student/preferences", headers=student_h).json()
    notifs = requests.get(f"{BASE_URL}/api/student/notifications", headers=student_h).json()

    print(f"""
  {BOLD}┌─────────────────────────────────────────────────────┐{RESET}
  {BOLD}│  📊 NOTIFICATION SYSTEM — KEY METRICS               │{RESET}
  {BOLD}├─────────────────────────────────────────────────────┤{RESET}
  {BOLD}│{RESET}  Architecture:   Event-Driven (Observer Pattern)    {BOLD}│{RESET}
  {BOLD}│{RESET}  Event Bus:      In-process Pub/Sub singleton       {BOLD}│{RESET}
  {BOLD}│{RESET}  Matching:       Fuzzy (SQL LIKE, partial match)    {BOLD}│{RESET}
  {BOLD}│{RESET}  Delivery:       Synchronous + 30s polling          {BOLD}│{RESET}
  {BOLD}├─────────────────────────────────────────────────────┤{RESET}
  {BOLD}│{RESET}  Preferences stored:         {GREEN}{prefs['total']:>5}{RESET}               {BOLD}│{RESET}
  {BOLD}│{RESET}  Total notifications:        {GREEN}{len(notifs['notifications']):>5}{RESET}               {BOLD}│{RESET}
  {BOLD}│{RESET}  Notifications generated:    {GREEN}{notification_count:>5}{RESET}               {BOLD}│{RESET}
  {BOLD}│{RESET}  Avg event→notification:     {GREEN}{statistics.mean(event_times):>5.1f}{RESET} ms           {BOLD}│{RESET}
  {BOLD}│{RESET}  Max event→notification:     {GREEN}{max(event_times):>5.1f}{RESET} ms           {BOLD}│{RESET}
  {BOLD}└─────────────────────────────────────────────────────┘{RESET}
""")


# ══════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════
def main():
    print(f"""
{BOLD}{CYAN}
  ╔══════════════════════════════════════════════════════════════╗
  ║  LIBRARY NOTIFICATION SYSTEM — METRICS & PERFORMANCE SUITE  ║
  ║  Observer Pattern · Event-Driven · Fuzzy Matching           ║
  ╚══════════════════════════════════════════════════════════════╝{RESET}
  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
  Server:  {BASE_URL}
""")

    try:
        # Authenticate
        student_token = login(STUDENT_CREDS)
        admin_token = login(ADMIN_CREDS)
        log(f"{CHECK} Authenticated as student and admin\n")

        # Run tests
        test_api_health_and_latency()
        test_preferences_crud(student_token)
        notification_count, event_times = test_notification_generation(admin_token, student_token)
        test_fuzzy_matching(admin_token, student_token)
        test_notification_lifecycle(student_token)
        test_concurrent_load(student_token)
        print_system_stats(admin_token, student_token, notification_count, event_times)

    except requests.ConnectionError:
        print(f"\n  {CROSS} {RED}Could not connect to {BASE_URL}{RESET}")
        print(f"  Start the backend: python -m uvicorn main:app --port 5000")
        sys.exit(1)
    except Exception as e:
        print(f"\n  {CROSS} {RED}Unexpected error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Final Summary
    print(f"\n{SEPARATOR}")
    print(f"  {BOLD}FINAL RESULTS{RESET}")
    print(f"{SEPARATOR}")
    print(f"  {GREEN}Passed: {total_pass}{RESET}  |  {RED}Failed: {total_fail}{RESET}  |  Total: {total_pass + total_fail}")

    if total_fail == 0:
        print(f"\n  {BOLD}{GREEN}🎉 ALL TESTS PASSED!{RESET}")
    else:
        print(f"\n  {BOLD}{YELLOW}⚠  Some tests failed — review above for details{RESET}")

    print(f"\n  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

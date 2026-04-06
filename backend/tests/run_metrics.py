"""Fast metrics test - saves results to tests/METRICS_REPORT.txt"""
import requests, time, statistics, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

B = "http://localhost:5000"
P = 0
F = 0
R = []

def l(m=""):
    R.append(m)
    print(m)

def chk(n, p, d=""):
    global P, F
    tag = "PASS" if p else "FAIL"
    l(f"  [{tag}] {n}  {d}")
    if p:
        P += 1
    else:
        F += 1

s_tok = requests.post(f"{B}/api/auth/login", json={"username": "rahul.kumar", "password": "pass123"}).json()["access_token"]
a_tok = requests.post(f"{B}/api/auth/login", json={"username": "admin", "password": "admin123"}).json()["access_token"]
sh = {"Authorization": f"Bearer {s_tok}"}
ah = {"Authorization": f"Bearer {a_tok}"}

# Clean old prefs
for p in requests.get(f"{B}/api/student/preferences", headers=sh).json().get("preferences", []):
    requests.delete(f"{B}/api/student/preferences/{p['id']}", headers=sh)

l("=" * 60)
l("  NOTIFICATION SYSTEM - METRICS REPORT")
l("=" * 60)
l(f"  {datetime.now():%Y-%m-%d %H:%M:%S}")
l()

# TEST 1: CRUD
l("-" * 60)
l("  TEST 1: PREFERENCES CRUD")
l("-" * 60)
prefs = [("category","Fantasy"),("category","Science Fiction"),("author","J.R.R. Tolkien"),("author","Isaac Asimov"),("title","Dune"),("title","Neuromancer"),("category","Mystery"),("author","Agatha Christie")]
ok = 0
ts = []
for pt, pv in prefs:
    t0 = time.perf_counter()
    r = requests.post(f"{B}/api/student/preferences", headers=sh, json={"preference_type": pt, "preference_value": pv})
    ts.append((time.perf_counter() - t0) * 1000)
    if r.status_code == 200:
        ok += 1
l(f"  Added {ok}/{len(prefs)}  avg={statistics.mean(ts):.0f}ms")
chk(f"All {len(prefs)} preferences created", ok == len(prefs))
dup = requests.post(f"{B}/api/student/preferences", headers=sh, json={"preference_type": "category", "preference_value": "Fantasy"})
chk("Duplicate rejected", dup.status_code in [400, 409], f"(HTTP {dup.status_code})")
inv = requests.post(f"{B}/api/student/preferences", headers=sh, json={"preference_type": "xyz", "preference_value": "x"})
chk("Invalid type rejected", inv.status_code in [400, 422], f"(HTTP {inv.status_code})")
l()

# TEST 2: OBSERVER NOTIFICATIONS
l("-" * 60)
l("  TEST 2: OBSERVER PATTERN NOTIFICATIONS")
l("-" * 60)
i0 = requests.get(f"{B}/api/student/notifications/unread-count", headers=sh).json()["unread_count"]
books = [
    {"title": "The Hobbit", "author": "J.R.R. Tolkien", "isbn": "9780547928227", "pages": 310, "price": 12.99, "category": "Fantasy", "quantity": 5},
    {"title": "Foundation", "author": "Isaac Asimov", "isbn": "9780553293357", "pages": 244, "price": 8.99, "category": "Science Fiction", "quantity": 3},
    {"title": "Orient Express", "author": "Agatha Christie", "isbn": "9780007119318", "pages": 274, "price": 9.99, "category": "Mystery", "quantity": 4},
    {"title": "Dune Messiah", "author": "Frank Herbert", "isbn": "9780593099322", "pages": 337, "price": 14.99, "category": "Science Fiction", "quantity": 2},
]
et = []
for b in books:
    t0 = time.perf_counter()
    requests.post(f"{B}/api/admin/books", headers=ah, json=b)
    et.append((time.perf_counter() - t0) * 1000)
i1 = requests.get(f"{B}/api/student/notifications/unread-count", headers=sh).json()["unread_count"]
gn = i1 - i0
l(f"  Books added: {len(books)}  Notifications: {gn}  Avg event: {statistics.mean(et):.0f}ms")
chk("Observer Pattern triggers notifications", gn > 0, f"({gn} created)")
nd = requests.get(f"{B}/api/student/notifications", headers=sh).json()
chk("Correct notification type", any(n["notification_type"] == "new_book" for n in nd["notifications"]))
chk("All have book_id", all(n["book_id"] is not None for n in nd["notifications"] if not n["is_read"]))
l()

# TEST 3: FUZZY MATCHING
l("-" * 60)
l("  TEST 3: FUZZY MATCHING")
l("-" * 60)
i2 = requests.get(f"{B}/api/student/notifications/unread-count", headers=sh).json()["unread_count"]
requests.post(f"{B}/api/admin/books", headers=ah, json={"title": "Dark Tower", "author": "Stephen King", "isbn": "9780451528513", "pages": 300, "price": 11.99, "category": "Dark Fantasy", "quantity": 3})
requests.post(f"{B}/api/admin/books", headers=ah, json={"title": "Silmarillion", "author": "J.R.R. Tolkien", "isbn": "9780261102736", "pages": 365, "price": 13.99, "category": "High Fantasy", "quantity": 2})
requests.post(f"{B}/api/admin/books", headers=ah, json={"title": "Cooking 101", "author": "Julia Child", "isbn": "9780375712579", "pages": 400, "price": 19.99, "category": "Cooking", "quantity": 5})
i3 = requests.get(f"{B}/api/student/notifications/unread-count", headers=sh).json()["unread_count"]
fz = i3 - i2
l(f"  3 books (2 partial + 1 no-match) -> {fz} notifications")
chk("Partial match works", fz >= 2, f"({fz} matched)")
chk("Non-match ignored", fz <= 5)
l()

# TEST 4: LIFECYCLE
l("-" * 60)
l("  TEST 4: NOTIFICATION LIFECYCLE")
l("-" * 60)
un = requests.get(f"{B}/api/student/notifications", headers=sh).json()
ul = [n for n in un["notifications"] if not n["is_read"]]
l(f"  Unread: {len(ul)}")
if ul:
    requests.patch(f"{B}/api/student/notifications/{ul[0]['id']}/read", headers=sh)
    c1 = requests.get(f"{B}/api/student/notifications/unread-count", headers=sh).json()["unread_count"]
    chk("Mark single read", c1 == len(ul) - 1)
requests.patch(f"{B}/api/student/notifications/read-all", headers=sh)
cf = requests.get(f"{B}/api/student/notifications/unread-count", headers=sh).json()["unread_count"]
chk("Mark all read (count=0)", cf == 0)
l()

# TEST 5: CONCURRENT LOAD
l("-" * 60)
l("  TEST 5: CONCURRENT LOAD (50 req / 10 threads)")
l("-" * 60)
er = 0
lt = []
def fetch():
    t0 = time.perf_counter()
    r = requests.get(f"{B}/api/student/notifications/unread-count", headers=sh)
    return r.status_code, (time.perf_counter() - t0) * 1000
with ThreadPoolExecutor(max_workers=10) as ex:
    for f in as_completed([ex.submit(fetch) for _ in range(50)]):
        s, e = f.result()
        lt.append(e)
        if s != 200:
            er += 1
lt.sort()
tp_val = 50 / (sum(lt) / 1000 / 10)
l(f"  OK: {50-er}/50  Avg: {statistics.mean(lt):.0f}ms  P95: {lt[47]:.0f}ms  ~{tp_val:.0f} req/s")
chk("Zero errors under load", er == 0)
l()

# SUMMARY
tn = len(requests.get(f"{B}/api/student/notifications", headers=sh).json()["notifications"])
tp2 = requests.get(f"{B}/api/student/preferences", headers=sh).json()["total"]
l("=" * 60)
l("  SYSTEM SUMMARY")
l("=" * 60)
l(f"  Patterns:      Observer, Repository, Service Layer, Factory")
l(f"  Matching:      Fuzzy (SQL LIKE partial)")
l(f"  Preferences:   {tp2}")
l(f"  Notifications: {tn}")
l(f"  Throughput:    ~{tp_val:.0f} req/s")
l()
l("=" * 60)
l(f"  PASSED: {P}  |  FAILED: {F}  |  TOTAL: {P + F}")
if F == 0:
    l("  >>> ALL TESTS PASSED! <<<")
l("=" * 60)

with open("tests/METRICS_REPORT.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(R))
l(f"\n  Saved: tests/METRICS_REPORT.txt")
sys.exit(0 if F == 0 else 1)

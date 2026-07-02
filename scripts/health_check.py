#!/usr/bin/env python3
# scripts/health_check.py
"""
Automated smoke test for Road Safety Dar es Salaam.

Run this against the live Render URL to verify all endpoints
are working after deployment.

Usage:
    # Against local dev server
    python scripts/health_check.py http://127.0.0.1:8000

    # Against live Render URL
    python scripts/health_check.py https://roadsafety-dar.onrender.com

    # Against custom domain
    python scripts/health_check.py https://roadsafety.co.tz
"""

import sys
import time
import urllib.request
import urllib.error
import json

# ── Colour output ─────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):    print(f"  {GREEN}✅ PASS{RESET}  {msg}")
def fail(msg):  print(f"  {RED}❌ FAIL{RESET}  {msg}")
def warn(msg):  print(f"  {YELLOW}⚠️  WARN{RESET}  {msg}")
def info(msg):  print(f"  {BLUE}ℹ️  INFO{RESET}  {msg}")


# ── Test definitions ──────────────────────────────────────────────────────────

TESTS = [
    # (name, path, expected_status, check_fn)
    # check_fn receives the response body (str) and returns (passed, message)

    (
        "Health check",
        "/health/",
        200,
        lambda body: (
            '"status": "ok"' in body or '"status":"ok"' in body,
            f'status=ok, engine={_extract(body, "engine")}'
        ),
    ),
    (
        "Root redirect",
        "/",
        200,  # 302 followed to dashboard
        lambda body: (
            "dashboard" in body.lower() or "Road Safety" in body,
            "Root redirects to dashboard"
        ),
    ),
    (
        "Public dashboard",
        "/dashboard/",
        200,
        lambda body: (
            "leaflet" in body.lower() or "map" in body.lower(),
            "Dashboard renders with map"
        ),
    ),
    (
        "Report form",
        "/report/",
        200,
        lambda body: (
            "form" in body.lower() or "accident" in body.lower(),
            "Report form renders"
        ),
    ),
    (
        "Login page",
        "/auth/login/",
        200,
        lambda body: (
            "google" in body.lower() or "sign" in body.lower(),
            "Login page renders"
        ),
    ),
    (
        "API: heatmap",
        "/api/heatmap/",
        200,
        lambda body: (
            body.strip().startswith("["),
            f"{len(json.loads(body))} heatmap points"
        ),
    ),
    (
        "API: accidents",
        "/api/accidents/",
        200,
        lambda body: (
            body.strip().startswith("["),
            f"{len(json.loads(body))} accident records"
        ),
    ),
    (
        "API: severity",
        "/api/severity/",
        200,
        lambda body: (
            "minor" in body or "fatal" in body,
            f"severity data: {body[:80].strip()}"
        ),
    ),
    (
        "API: vehicles",
        "/api/vehicles/",
        200,
        lambda body: (
            isinstance(json.loads(body), dict),
            "vehicle type counts returned"
        ),
    ),
    (
        "API: monthly",
        "/api/monthly/",
        200,
        lambda body: (
            body.strip().startswith("["),
            f"{len(json.loads(body))} monthly data points"
        ),
    ),
    (
        "API: hourly",
        "/api/hourly/",
        200,
        lambda body: (
            len(json.loads(body)) == 24,
            "24 hourly buckets returned"
        ),
    ),
    (
        "API: junctions",
        "/api/junctions/",
        200,
        lambda body: (
            len(json.loads(body)) > 0,
            f"{len(json.loads(body))} junctions returned"
        ),
    ),
    (
        "API: summary",
        "/api/summary/",
        200,
        lambda body: (
            "total" in body,
            f"summary: {body[:100].strip()}"
        ),
    ),
    (
        "API: accidents near (with params)",
        "/api/accidents/near/?lat=-6.792&lng=39.208&radius=2000",
        200,
        lambda body: (
            "accidents" in body,
            f"radius search returned {_extract(body, 'count')} results"
        ),
    ),
    (
        "API: accidents near (no params — expect 400)",
        "/api/accidents/near/",
        400,
        lambda body: (
            "error" in body.lower(),
            "Correct 400 error on missing params"
        ),
    ),
    (
        "API: heatmap with bbox filter",
        "/api/heatmap/?bbox=-7.0,39.1,-6.5,39.5",
        200,
        lambda body: (
            body.strip().startswith("["),
            f"{len(json.loads(body))} points in bbox"
        ),
    ),
    (
        "Authority redirect (not logged in)",
        "/authority/",
        200,  # 302 → login → 200
        lambda body: (
            "login" in body.lower() or "sign" in body.lower(),
            "Authority redirects to login when not authenticated"
        ),
    ),
    (
        "Editor queue redirect (not logged in)",
        "/editor/queue/",
        200,  # 302 → login → 200
        lambda body: (
            "login" in body.lower() or "sign" in body.lower(),
            "Editor queue redirects to login when not authenticated"
        ),
    ),
]


def _extract(body: str, key: str) -> str:
    """Extract a value from a JSON string by key — best effort."""
    try:
        data = json.loads(body)
        return str(data.get(key, "?"))
    except Exception:
        return "?"


# ── Runner ────────────────────────────────────────────────────────────────────

def run_smoke_tests(base_url: str) -> bool:
    """
    Runs all smoke tests against base_url.
    Returns True if all critical tests pass.
    """
    base_url = base_url.rstrip("/")

    print(f"\n{BOLD}{'='*56}{RESET}")
    print(f"{BOLD}  Road Safety Dar — Smoke Test{RESET}")
    print(f"{BOLD}  Target: {base_url}{RESET}")
    print(f"{BOLD}{'='*56}{RESET}\n")

    # Warm up the server (Render free tier cold start)
    print(f"  Warming up server (may take 30s on Render free tier)...")
    for attempt in range(3):
        try:
            urllib.request.urlopen(f"{base_url}/health/", timeout=40)
            print(f"  Server is awake ✅\n")
            break
        except Exception:
            if attempt < 2:
                print(f"  Waiting... (attempt {attempt + 1}/3)")
                time.sleep(10)
            else:
                print(f"  {RED}Server did not respond. Is it deployed?{RESET}\n")

    passed = 0
    failed = 0
    warned = 0
    start = time.time()

    for name, path, expected_status, check_fn in TESTS:
        url = f"{base_url}{path}"
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "RoadSafetyDar-SmokeTest/1.0")

            response = urllib.request.urlopen(req, timeout=30)
            status = response.status
            body = response.read().decode("utf-8", errors="replace")

        except urllib.error.HTTPError as e:
            status = e.code
            body = e.read().decode("utf-8", errors="replace")
        except urllib.error.URLError as e:
            fail(f"{name} — Connection error: {e.reason}")
            failed += 1
            continue
        except Exception as e:
            fail(f"{name} — Unexpected error: {e}")
            failed += 1
            continue

        # Status check
        if status != expected_status:
            fail(f"{name} — Expected {expected_status}, got {status}")
            failed += 1
            continue

        # Content check
        try:
            result, message = check_fn(body)
            if result:
                ok(f"{name} — {message}")
                passed += 1
            else:
                warn(f"{name} — {message}")
                warned += 1
        except Exception as e:
            warn(f"{name} — Check error: {e}")
            warned += 1

        # Small delay to avoid overwhelming the server
        time.sleep(0.3)

    elapsed = time.time() - start

    # Summary
    print(f"\n{BOLD}{'='*56}{RESET}")
    print(f"{BOLD}  Results{RESET}")
    print(f"  {GREEN}✅ Passed:  {passed}{RESET}")
    if warned:
        print(f"  {YELLOW}⚠️  Warned:  {warned}{RESET}")
    if failed:
        print(f"  {RED}❌ Failed:  {failed}{RESET}")
    print(f"  ⏱️  Time:    {elapsed:.1f}s")
    print(f"{BOLD}{'='*56}{RESET}\n")

    all_passed = (failed == 0)
    if all_passed:
        print(f"{GREEN}{BOLD}  All critical tests passed. "
              f"System is live and healthy! 🚀{RESET}\n")
    else:
        print(f"{RED}{BOLD}  {failed} test(s) failed. "
              f"Check Render logs for details.{RESET}\n")

    return all_passed


if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    success = run_smoke_tests(base)
    sys.exit(0 if success else 1)

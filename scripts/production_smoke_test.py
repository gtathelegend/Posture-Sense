#!/usr/bin/env python3
"""
PostureSense v2 — Production Deployment Smoke Test Script

Validates publicly testable endpoints, health checks, version metadata,
and static MediaPipe/WASM asset delivery against local or production deployments.

Usage:
    BASE_URL=https://posture-sense-4b1i.onrender.com python scripts/production_smoke_test.py
"""

import sys
import os
import time
import urllib.request
import urllib.error
import json


BASE_URL = os.getenv("BASE_URL", "http://localhost:8080").rstrip("/")

ENDPOINTS_TO_TEST = [
    {
        "name": "Health Check",
        "path": "/health",
        "expected_status": 200,
        "expected_content_type_contains": "application/json",
        "critical": True,
    },
    {
        "name": "API Health Check",
        "path": "/api/health",
        "expected_status": 200,
        "expected_content_type_contains": "application/json",
        "critical": True,
    },
    {
        "name": "Version Endpoint",
        "path": "/version",
        "expected_status": 200,
        "expected_content_type_contains": "application/json",
        "critical": True,
    },
    {
        "name": "Landing / Index Page",
        "path": "/",
        "expected_status": 200,
        "expected_content_type_contains": "text/html",
        "critical": True,
    },
    {
        "name": "MediaPipe Vision Bundle JS",
        "path": "/static/vendor/mediapipe/v0.10.0/vision_bundle.js",
        "expected_status": 200,
        "expected_content_type_contains": "javascript",
        "min_bytes": 100000,
        "critical": True,
    },
    {
        "name": "MediaPipe Pose Landmarker Model Task",
        "path": "/static/vendor/mediapipe/v0.10.0/pose_landmarker_lite.task",
        "expected_status": 200,
        "expected_content_type_contains": "octet-stream",
        "min_bytes": 1000000,
        "critical": True,
    },
    {
        "name": "MediaPipe WASM Binary",
        "path": "/static/vendor/mediapipe/v0.10.0/wasm/vision_wasm_internal.wasm",
        "expected_status": 200,
        "expected_content_type_contains": "wasm",
        "min_bytes": 1000000,
        "critical": True,
    },
    {
        "name": "MediaPipe Worker Script",
        "path": "/static/assets/js/workers/mediapipe_worker.js",
        "expected_status": 200,
        "expected_content_type_contains": "javascript",
        "min_bytes": 1000,
        "critical": True,
    },
    {
        "name": "MediaPipe Engine Script",
        "path": "/static/assets/js/engines/mediapipe_engine.js",
        "expected_status": 200,
        "expected_content_type_contains": "javascript",
        "min_bytes": 1000,
        "critical": True,
    },
]


def run_smoke_test():
    print("======================================================================")
    print(" PostureSense v2 — Production Smoke Test")
    print(f" Target Base URL: {BASE_URL}")
    print("======================================================================\n")

    passed_count = 0
    failed_count = 0
    results = []

    for ep in ENDPOINTS_TO_TEST:
        url = f"{BASE_URL}{ep['path']}"
        start_time = time.time()
        
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "PostureSense-Production-SmokeTest/2.0.0",
                "Accept": "*/*",
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                elapsed_ms = (time.time() - start_time) * 1000
                status_code = resp.getcode()
                content_type = resp.headers.get("Content-Type", "")
                
                content_bytes = resp.read()
                actual_bytes = len(content_bytes)

                # Validation checks
                status_ok = status_code == ep["expected_status"]
                ct_ok = ep["expected_content_type_contains"].lower() in content_type.lower() if ep.get("expected_content_type_contains") else True
                bytes_ok = actual_bytes >= ep.get("min_bytes", 0)

                # HTML error check for static assets
                html_error = False
                if ep["path"].startswith("/static/") and ("text/html" in content_type.lower() or content_bytes.startswith(b"<!DOCTYPE") or content_bytes.startswith(b"<html")):
                    html_error = True

                is_pass = status_ok and ct_ok and bytes_ok and not html_error

                if is_pass:
                    passed_count += 1
                    status_str = "PASS"
                else:
                    failed_count += 1
                    status_str = "FAIL"

                details = f"HTTP {status_code} | {elapsed_ms:.1f}ms | {actual_bytes:,} bytes | {content_type}"
                results.append((ep['name'], ep['path'], status_str, details))

                print(f"[{status_str}] {ep['name']:<35} ({ep['path']})")
                print(f"       -> {details}")

                if not is_pass:
                    if html_error:
                        print("       [!] ERROR: Asset returned HTML content instead of binary/script data!")
                    if not status_ok:
                        print(f"       [!] ERROR: Expected HTTP {ep['expected_status']}, got {status_code}")
                    if not ct_ok:
                        print(f"       [!] ERROR: Expected Content-Type containing '{ep['expected_content_type_contains']}', got '{content_type}'")
                    if not bytes_ok:
                        print(f"       [!] ERROR: Expected min {ep['min_bytes']} bytes, got {actual_bytes}")

        except urllib.error.HTTPError as e:
            elapsed_ms = (time.time() - start_time) * 1000
            failed_count += 1
            details = f"HTTP {e.code} ({e.reason}) | {elapsed_ms:.1f}ms"
            results.append((ep['name'], ep['path'], "FAIL", details))
            print(f"[FAIL] {ep['name']:<35} ({ep['path']})")
            print(f"       -> {details}")
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            failed_count += 1
            details = f"Error: {str(e)} | {elapsed_ms:.1f}ms"
            results.append((ep['name'], ep['path'], "FAIL", details))
            print(f"[FAIL] {ep['name']:<35} ({ep['path']})")
            print(f"       -> {details}")
        
        print()

    print("======================================================================")
    print(f" Summary: {passed_count} Passed, {failed_count} Failed out of {len(ENDPOINTS_TO_TEST)} checks.")
    print("======================================================================")

    if failed_count > 0:
        print("\n[!] Smoke Test Verdict: FAILED")
        return 1
    else:
        print("\n[PASS] Smoke Test Verdict: PASSED -- All endpoints operational")
        return 0


if __name__ == "__main__":
    sys.exit(run_smoke_test())

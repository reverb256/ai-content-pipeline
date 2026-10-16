#!/usr/bin/env python3
"""Check if playwright is available and what version."""
import sys
try:
    import playwright
    print(f"playwright version: {playwright.__version__}")
    print(f"playwright path: {playwright.__file__}")
except ImportError as e:
    print(f"playwright NOT installed: {e}")
    sys.exit(1)

# Check for sync API
try:
    from playwright.sync_api import sync_playwright
    print("sync_api: available")
except ImportError as e:
    print(f"sync_api NOT available: {e}")

# Check for async API
try:
    from playwright.async_api import async_playwright
    print("async_api: available")
except ImportError as e:
    print(f"async_api NOT available: {e}")

# Check for chromium browser
import os
cache_dir = os.path.expanduser("~/.cache/ms-playwright")
if os.path.isdir(cache_dir):
    browsers = os.listdir(cache_dir)
    print(f"cached browsers: {browsers}")
else:
    print("no playwright browser cache found")

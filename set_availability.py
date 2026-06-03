import os
import time
from playwright.sync_api import sync_playwright

BASE_URL = os.environ["BASE_URL"]
USERNAME = os.environ["USERNAME"]
PASSWORD = os.environ["PASSWORD"]
STATUS_CHOICE = os.environ.get("STATUS_CHOICE", "available")

PAGE_TIMEOUT = int(os.environ.get("PAGE_TIMEOUT", "30000"))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.environ.get("RETRY_DELAY", "10"))


def validate_env():
    missing = [v for v in ("BASE_URL", "USERNAME", "PASSWORD") if v not in os.environ]
    if missing:
        raise SystemExit(f"Missing required env vars: {', '.join(missing)}")
    if STATUS_CHOICE not in ("available", "unavailable"):
        raise SystemExit(
            f"STATUS_CHOICE must be 'available' or 'unavailable', got '{STATUS_CHOICE}'"
        )


def attempt_set_status():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(locale="en-US", timezone_id="America/New_York")
        page = context.new_page()

        try:
            print(f"Logging into {BASE_URL}/user/login ...")
            page.goto(
                f"{BASE_URL}/user/login",
                wait_until="load",
                timeout=PAGE_TIMEOUT,
            )

            page.wait_for_selector("input#edit-name", timeout=PAGE_TIMEOUT)
            page.fill("input#edit-name", USERNAME)
            page.wait_for_selector("input#edit-pass", timeout=PAGE_TIMEOUT)
            page.fill("input#edit-pass", PASSWORD)
            page.click("input#edit-submit")

            page.wait_for_function(
                '!window.location.href.includes("/user/login")',
                timeout=PAGE_TIMEOUT,
            )
            print("Login successful.")

            toggle_url = f"{BASE_URL}/change-availability-for-tomorrow/{STATUS_CHOICE}"
            print(f"Navigating to {toggle_url} ...")
            page.goto(toggle_url, wait_until="load", timeout=PAGE_TIMEOUT)

            page.wait_for_timeout(4000)

            page_content = page.content()
            expected_message = (
                "You're made available for tomorrow"
                if STATUS_CHOICE == "available"
                else "You're made unavailable for tomorrow"
            )

            if expected_message in page_content:
                print(f"SUCCESS: {expected_message}")
                result = "success"
            elif f"availunavail-header-top {STATUS_CHOICE}" in page_content:
                print(
                    f"SUCCESS: Status changed to {STATUS_CHOICE} "
                    "(verified via header class)"
                )
                result = "success"
            else:
                print("WARNING: Could not verify status change via message or header.")
                result = "unknown"

            page.screenshot(path="final-status.png", full_page=True)
            return result

        except Exception as e:
            print(f"ERROR: {e}")
            try:
                page.screenshot(path="error-screenshot.png", full_page=True)
            except Exception:
                pass
            raise

        finally:
            browser.close()


def main():
    validate_env()

    last_exception = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = attempt_set_status()
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write(f"result={result}\n")
            return
        except Exception as e:
            last_exception = e
            if attempt < MAX_RETRIES:
                print(
                    f"Attempt {attempt}/{MAX_RETRIES} failed: {e}. "
                    f"Retrying in {RETRY_DELAY}s..."
                )
                time.sleep(RETRY_DELAY)

    print(f"All {MAX_RETRIES} attempts failed.")
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write("result=failure\n")
    raise last_exception


if __name__ == "__main__":
    main()

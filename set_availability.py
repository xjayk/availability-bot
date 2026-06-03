import os
from playwright.sync_api import sync_playwright

LOGIN_URL = os.environ["LOGIN_URL"]
USERNAME = os.environ["USERNAME"]
PASSWORD = os.environ["PASSWORD"]
STATUS_URL = os.environ["STATUS_URL"]
STATUS_CHOICE = os.environ.get("STATUS_CHOICE", "Available")
STATUS_BUTTON_SELECTOR = os.environ.get("STATUS_BUTTON_SELECTOR", 'text="Available"')
SAVE_BUTTON_SELECTOR = os.environ.get("SAVE_BUTTON_SELECTOR", 'button:has-text("Save")')

USERNAME_SELECTOR = os.environ.get("USERNAME_SELECTOR", 'input[name="username"]')
PASSWORD_SELECTOR = os.environ.get("PASSWORD_SELECTOR", 'input[name="password"]')
SUBMIT_SELECTOR = os.environ.get("SUBMIT_SELECTOR", 'button[type="submit"]')


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            print(f"Navigating to {LOGIN_URL}...")
            page.goto(LOGIN_URL, wait_until="networkidle")
            page.fill(USERNAME_SELECTOR, USERNAME)
            page.fill(PASSWORD_SELECTOR, PASSWORD)
            page.click(SUBMIT_SELECTOR)

            page.wait_for_url("**/dashboard**", timeout=15000)
            print("Login successful.")

            print(f"Navigating to {STATUS_URL}...")
            page.goto(STATUS_URL, wait_until="networkidle")

            print(f"Selecting status: {STATUS_CHOICE}")
            page.click(STATUS_BUTTON_SELECTOR)

            page.click(SAVE_BUTTON_SELECTOR)
            page.wait_for_timeout(2000)

            page.screenshot(path="status-confirmation.png", full_page=True)
            print("Status set successfully. Screenshot saved.")

            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write(f"result=success\n")

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="error-screenshot.png", full_page=True)
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write(f"result=failure\n")
            raise

        finally:
            browser.close()


if __name__ == "__main__":
    main()

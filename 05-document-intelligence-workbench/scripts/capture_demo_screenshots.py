from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright


DASHBOARD_URL = "http://127.0.0.1:8512"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "demo"


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1200})
        page.goto(DASHBOARD_URL, wait_until="networkidle", timeout=120000)

        page.wait_for_selector("text=Document Intelligence Workbench", timeout=60000)

        # Capture only the main pane for public assets, excluding sidebar access fields.
        main_pane = page.locator('[data-testid="stMain"]')
        main_pane.screenshot(path=str(OUTPUT_DIR / "workbench-dashboard.png"))
        main_box = main_pane.bounding_box()
        if not main_box:
            raise RuntimeError("Could not determine main pane bounds for screenshot clipping")

        review_heading = page.get_by_role("heading", name="Review Queue")
        review_heading.scroll_into_view_if_needed()
        page.wait_for_timeout(1000)
        review_box = review_heading.bounding_box()
        if not review_box:
            raise RuntimeError("Could not determine review section bounds")
        page.screenshot(
            path=str(OUTPUT_DIR / "workbench-review-table.png"),
            clip={
                "x": main_box["x"],
                "y": max(main_box["y"], review_box["y"] - 40),
                "width": main_box["width"],
                "height": min(480, max(220, main_box["height"] - (review_box["y"] - main_box["y"]))),
            },
        )

        extracted_heading = page.get_by_role("heading", name="Extracted Fields")
        extracted_heading.scroll_into_view_if_needed()
        page.wait_for_timeout(1000)
        extracted_box = extracted_heading.bounding_box()
        if not extracted_box:
            raise RuntimeError("Could not determine extracted fields section bounds")
        page.screenshot(
            path=str(OUTPUT_DIR / "workbench-export.png"),
            clip={
                "x": main_box["x"],
                "y": max(main_box["y"], extracted_box["y"] - 40),
                "width": main_box["width"],
                "height": min(480, max(220, main_box["height"] - (extracted_box["y"] - main_box["y"]))),
            },
        )

        browser.close()
    print("Captured demo screenshots in demo/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

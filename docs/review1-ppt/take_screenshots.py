"""
SecureNeuroGrade — Automated Screenshot Capture
Captures all key UI pages for the Review 1 presentation.
"""
import asyncio
import os
from pathlib import Path

SCREENSHOT_DIR = Path(r"D:\My Stuff\Anitgravity\MAIN PROJECT\docs\review1-ppt\screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://127.0.0.1:5000"

# Small test image to upload (1x1 black PNG — will trigger quality rejection for being too small)
import base64
# 1x1 pixel black PNG
TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9Q"
    "DwADhgGAWjR9awAAAABJRU5ErkJggg=="
)

# Create a small valid test PNG (40x40 so it passes size/dimension but triggers other checks)
import struct, zlib

def make_png(width=40, height=40):
    """Generate a minimal valid PNG of given size."""
    def pack_chunk(name, data):
        c = struct.pack('>I', len(data)) + name + data
        return c + struct.pack('>I', zlib.crc32(name + data) & 0xffffffff)
    
    header = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr = pack_chunk(b'IHDR', ihdr_data)
    
    # Build raw image data (width * 3 bytes per row, + 1 filter byte)
    raw = b''
    for _ in range(height):
        raw += b'\x00' + b'\x00\x80\x80' * width  # teal pixels
    
    compressed = zlib.compress(raw)
    idat = pack_chunk(b'IDAT', compressed)
    iend = pack_chunk(b'IEND', b'')
    return header + ihdr + idat + iend

test_png_path = SCREENSHOT_DIR / "test_upload.png"
test_png_path.write_bytes(make_png(200, 200))
print(f"[OK] Test PNG created: {test_png_path}")


async def take_screenshots():
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        def ss(name):
            path = str(SCREENSHOT_DIR / f"{name}.png")
            print(f"  [Screenshot] {name}.png")
            return page.screenshot(path=path, full_page=True)

        # ── 1. Login page ────────────────────────────────────────────────────
        print("\n[1] Login page")
        await page.goto(f"{BASE_URL}/auth/login", wait_until="networkidle")
        await ss("01_login_page")

        # ── 2. Technician login ──────────────────────────────────────────────
        print("[2] Technician login")
        await page.fill('input[name="username"]', "technician")
        await page.fill('input[name="password"]', "tech123")
        await page.click('button[type="submit"]')
        await page.wait_for_load_state("networkidle")
        await ss("02_technician_dashboard")

        # ── 3. Upload form ───────────────────────────────────────────────────
        print("[3] Upload form")
        # Try common upload link patterns
        upload_url = None
        for link_text in ["Upload", "New Scan", "Upload Scan", "Upload MRI", "Add Scan"]:
            lnk = page.get_by_role("link", name=link_text, exact=False)
            if await lnk.count() > 0:
                upload_url = await lnk.first.get_attribute("href")
                break
        
        if upload_url:
            await page.goto(f"{BASE_URL}{upload_url}", wait_until="networkidle")
        else:
            await page.goto(f"{BASE_URL}/technician/upload", wait_until="networkidle")
        
        await ss("03_upload_form")

        # ── 4. Submit upload (will fail quality check — tiny/wrong type) ─────
        print("[4] Uploading test file...")
        try:
            # Fill patient ID
            patient_field = page.locator('input[name="patient_identifier"], input[name="patient_id"], input[id*="patient"]').first
            if await patient_field.count() > 0:
                await patient_field.fill("TEST-PATIENT-001")

            # Optional age
            age_field = page.locator('input[name="patient_age"], input[name="age"]').first
            if await age_field.count() > 0:
                await age_field.fill("45")

            # File input
            file_input = page.locator('input[type="file"]').first
            if await file_input.count() > 0:
                await file_input.set_input_files(str(test_png_path))
            
            # Submit
            submit_btn = page.locator('button[type="submit"], input[type="submit"]').first
            if await submit_btn.count() > 0:
                await submit_btn.click()
                await page.wait_for_load_state("networkidle")
                await ss("04_upload_status_after_submit")
        except Exception as e:
            print(f"  [WARN] Upload step issue: {e}")
            await ss("04_upload_page_error")

        # ── 5. Technician scan history ────────────────────────────────────────
        print("[5] Technician scan history")
        await page.goto(f"{BASE_URL}/technician/", wait_until="networkidle")
        await ss("05_technician_scan_list")

        # ── 6. Logout ────────────────────────────────────────────────────────
        print("[6] Logout")
        await page.goto(f"{BASE_URL}/auth/logout", wait_until="networkidle")
        await ss("06_after_logout")

        # ── 7. Doctor login ───────────────────────────────────────────────────
        print("[7] Doctor login")
        await page.goto(f"{BASE_URL}/auth/login", wait_until="networkidle")
        await page.fill('input[name="username"]', "doctor")
        await page.fill('input[name="password"]', "doctor123")
        await page.click('button[type="submit"]')
        await page.wait_for_load_state("networkidle")
        await ss("07_doctor_dashboard")

        # ── 8. Doctor result detail (if any scan exists) ──────────────────────
        print("[8] Doctor result detail (if any)")
        result_links = await page.locator('a[href*="/doctor/result/"], a[href*="/scans/"], a[href*="/results/"]').all()
        if result_links:
            href = await result_links[0].get_attribute("href")
            await page.goto(f"{BASE_URL}{href}", wait_until="networkidle")
            await ss("08_doctor_result_detail")
        else:
            # Try to navigate to a scan from the scan list
            await page.goto(f"{BASE_URL}/doctor/", wait_until="networkidle")
            rows = await page.locator('table tbody tr a, .scan-row a, .result-link').all()
            if rows:
                href = await rows[0].get_attribute("href")
                if href:
                    await page.goto(f"{BASE_URL}{href}", wait_until="networkidle")
                    await ss("08_doctor_result_detail")
            else:
                print("  [INFO] No result detail links found on doctor dashboard")

        # ── 9. Light mode toggle check ────────────────────────────────────────
        print("[9] Light mode")
        await page.goto(f"{BASE_URL}/doctor/", wait_until="networkidle")
        theme_toggle = page.locator('#theme-toggle, .theme-toggle, [aria-label*="theme"], [title*="theme"]').first
        if await theme_toggle.count() > 0:
            await theme_toggle.click()
            await page.wait_for_timeout(800)
            await ss("09_light_mode_doctor_dashboard")

        # ── 10. Login page light mode ─────────────────────────────────────────
        print("[10] Login page light mode")
        await page.goto(f"{BASE_URL}/auth/logout", wait_until="networkidle")
        await page.goto(f"{BASE_URL}/auth/login", wait_until="networkidle")
        await ss("10_login_page_light")

        await browser.close()
        print("\n[DONE] All screenshots saved to:", SCREENSHOT_DIR)
        screenshots = list(SCREENSHOT_DIR.glob("*.png"))
        print(f"[DONE] {len(screenshots)} files:")
        for f in sorted(screenshots):
            print(f"       {f.name} ({f.stat().st_size // 1024} KB)")


asyncio.run(take_screenshots())

import asyncio
import logging
import hashlib
import re
import time
import random
import urllib.request
import speech_recognition as sr
import base64
from pydub import AudioSegment
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Response, Request
try:
    from playwright_stealth import stealth_async  # playwright-stealth 1.x
except ImportError:
    try:
        from playwright_stealth import Stealth  # playwright-stealth 2.x
        async def stealth_async(page):
            await Stealth().apply_stealth_async(page)
    except ImportError:
        async def stealth_async(page):
            pass  # stealth unavailable, continue without it
from core.llm import LLMAnalyzer


logger = logging.getLogger(__name__)

_FAKE_DATA_BY_REGION = {
    "FR": {
        "email": "victime@exemple.fr",
        "password": "MotDePasse123!",
        "tel": "0612345678",
        "text": "Jean Dupont",
        "name": "Jean Dupont",
        "cc": "4532000000000000",
        "cvv": "123",
        "exp": "12/28",
        "otp": "123456",
    },
    "DE": {
        "email": "opfer@beispiel.de",
        "password": "Passwort123!",
        "tel": "01512345678",
        "text": "Max Mustermann",
        "name": "Max Mustermann",
        "cc": "4532000000000000",
        "cvv": "123",
        "exp": "12/28",
        "otp": "123456",
    },
    "JP": {
        "email": "higaisha@example.jp",
        "password": "Password123!",
        "tel": "09012345678",
        "text": "田中太郎",
        "name": "田中太郎",
        "cc": "4532000000000000",
        "cvv": "123",
        "exp": "12/28",
        "otp": "123456",
    },
    "US": {
        "email": "victim@example.com",
        "password": "Password123!",
        "tel": "5551234567",
        "text": "John Doe",
        "name": "John Doe",
        "cc": "4532000000000000",
        "cvv": "123",
        "exp": "12/28",
        "otp": "123456",
    },
}


class BrowserManager:
    def __init__(self, headless: bool = True, region: str = "US"):
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.redirect_chain: List[Dict[str, Any]] = []
        self.network_log: List[Dict[str, Any]] = []
        self.downloaded_files: List[Dict[str, Any]] = []
        self.llm = LLMAnalyzer() # Initialize AI for smart detection

        # Region-localized fake data for realistic probing
        self.fake_data = _FAKE_DATA_BY_REGION.get(region.upper(), _FAKE_DATA_BY_REGION["US"])


    async def start(self, locale: str = "en-US", timezone_id: str = "America/New_York"):
        """Initializes Playwright and launches the browser with stealth."""
        self.playwright = await async_playwright().start()
        
        # We MUST run in headed mode (headless=False) because Cloudflare blocks
        # traditional headless mode by checking WebGL vendor and Canvas fingerprints.
        # Since we use XVFB in docker, headed mode works perfectly in the background.
        self.browser = await self.playwright.chromium.launch(
            headless=False, 
            slow_mo=100, 
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars",
                "--disable-setuid-sandbox",
                "--window-size=1280,900"
            ]
        )
        
        # Randomize User-Agent to avoid fingeprint tracking and blacklisting
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.1; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]
        chosen_ua = random.choice(user_agents)
        
        # Randomize viewport slightly
        width = random.randint(1280, 1920)
        height = random.randint(720, 1080)
        
        self.context = await self.browser.new_context(
            user_agent=chosen_ua,
            viewport={"width": width, "height": height},
            locale=locale,
            timezone_id=timezone_id,
            bypass_csp=True, 
            ignore_https_errors=True
        )

        # Apply stealth at the context level if possible, or individually to pages
        # The simplest approach is wrapping the context creation but `use_async` targets pages generally.
        self.page = await self.context.new_page()
        
        # Apply strict stealth mode to evade Cloudflare and other advanced anti-bots
        await stealth_async(self.page)
        await self._apply_stealth(self.context)
        
        self.page.on("request", self._on_request)
        self.page.on("response", self._on_response)

    async def _apply_stealth(self, context: BrowserContext):
        """Deprecated. Native JS patches are removed in favor of playwright-stealth."""
        pass

    async def _on_request(self, request: Request):
        pass

    async def _on_response(self, response: Response):
        """Callback for network responses. Captures chain and files."""
        if 300 <= response.status < 400:
            self.redirect_chain.append({
                "url": response.url,
                "status": response.status,
                "headers": response.headers,
                "type": "http_redirect"
            })

        url_lower = response.url.lower()
        content_type = response.headers.get("content-type", "").lower()

        is_java = (url_lower.endswith(".jar") or "java-archive" in content_type)
        is_js = (url_lower.endswith(".js") or "javascript" in content_type)

        if is_java or is_js:
            try:
                body = await response.body()
                self.network_log.append({
                    "url": response.url,
                    "type": "java" if is_java else "js",
                    "content": body, 
                    "headers": response.headers
                })
            except Exception as e:
                logger.error(f"Failed to capture body for {response.url}: {e}")

    async def _fill_page_inputs(self, page) -> List[str]:
        """Scans and fills visible inputs with fake data."""
        filled_log = []
        try:
            # 1. Get all visible inputs
            inputs = await page.locator("input, textarea, select").all()
            
            for inp in inputs:
                if not await inp.is_visible(): continue
                
                # Get usage hints
                id_attr = (await inp.get_attribute("id") or "").lower()
                name_attr = (await inp.get_attribute("name") or "").lower()
                type_attr = (await inp.get_attribute("type") or "").lower()
                placeholder = (await inp.get_attribute("placeholder") or "").lower()
                
                # Determine value to fill
                val_to_fill = ""
                field_type = "unknown"
                
                # Check Password
                if "pass" in id_attr or "pass" in name_attr or "password" in type_attr:
                    val_to_fill = self.fake_data["password"]
                    field_type = "password"
                # Check Email
                elif "mail" in id_attr or "mail" in name_attr or "email" in type_attr or "@" in placeholder:
                    val_to_fill = self.fake_data["email"]
                    field_type = "email"
                # Check Phone
                elif "tel" in id_attr or "mob" in name_attr or "phone" in type_attr or "tel" in type_attr:
                    val_to_fill = self.fake_data["tel"]
                    field_type = "phone"
                # Check Credit Card
                elif "card" in id_attr or "cc" in name_attr or "numero" in id_attr or "number" in placeholder:
                    val_to_fill = self.fake_data["cc"]
                    field_type = "credit_card"
                # Check OTP/Code
                elif "otp" in id_attr or "code" in name_attr or "code" in placeholder:
                    val_to_fill = self.fake_data["otp"]
                    field_type = "otp"
                # Generic Text / Name
                elif type_attr in ["text", ""] and ("user" in id_attr or "nom" in name_attr or "name" in name_attr):
                    val_to_fill = self.fake_data["name"]
                    field_type = "name"
                
                # Fill if we found a match and it's empty
                if val_to_fill:
                    current_val = await inp.input_value()
                    if not current_val: # Only fill if empty
                        await inp.fill(val_to_fill)
                        filled_log.append(f"Filled {field_type} ({name_attr or id_attr})")
                        
        except Exception as e:
            logger.warning(f"Input filling error: {e}")
            
        return filled_log

    async def _simulate_human(self, page) -> None:
        """Simulates human interaction (mouse movements, scrolling) to build trust score."""
        try:
            # 1. Random Mouse Movements
            logger.info("👻 Simulating human mouse movements...")
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, 1500)
                y = random.randint(100, 800)
                # steps makes the movement less linear and a bit jerky like a real hand
                await page.mouse.move(x, y, steps=random.randint(5, 15))
                await asyncio.sleep(random.uniform(0.1, 0.4))
            
            # 2. Random Scrolling
            if random.random() > 0.3: # 70% chance to scroll
                logger.info("👻 Simulating human scroll...")
                scroll_amount = random.randint(200, 600)
                await page.mouse.wheel(0, scroll_amount)
                await asyncio.sleep(random.uniform(0.5, 1.2))
                # maybe scroll back up a bit
                if random.random() > 0.5:
                    await page.mouse.wheel(0, -random.randint(50, 200))
                    await asyncio.sleep(random.uniform(0.3, 0.8))
        except Exception as e:
            logger.warning(f"Error during human simulation: {e}")

    def _page_changed(self, url_before: str, hash_before: str, url_after: str, hash_after: str) -> bool:
        """Returns True if the page meaningfully changed after a CAPTCHA interaction."""
        return url_after != url_before or hash_after != hash_before

    async def _captcha_still_present(self, page) -> bool:
        """Quick check: is there still an active CAPTCHA on the page?"""
        try:
            content_lower = (await page.content()).lower()
            title_lower = (await page.title()).lower()
            cf_strings = ["just a moment", "cf-chl-widget", "turnstile", "checking your browser"]
            captcha_strings = ["captcha", "recaptcha", "hcaptcha", "anti-bot", "bot-check"]
            return (
                any(s in content_lower for s in cf_strings + captcha_strings)
                or any(s in title_lower for s in cf_strings)
                or "captcha" in page.url.lower()
            )
        except Exception:
            return False

    async def _solve_captcha(self, page) -> bool:
        """
        Multi-tier CAPTCHA bypass system with retry logic:
          Tier 0a : Cloudflare IUAM / Turnstile — stealth wait + multi-position clicks (3 retries)
          Tier 0b : reCAPTCHA / hCaptcha checkbox — click the "I'm not a robot" box
          Tier 1  : AI LLM analysis (Mistral text + llava vision, 2 retries)
          Tier 1.5: Audio challenge solver (speech-recognition, 2 retries)
          Tier 1.7: Visual image-grid solver (llava VLM, 2 retries)
          Tier 2  : Heuristic math CAPTCHA (DOM extraction + regex, 3 retries)
          Tier 3  : 2captcha / Anti-Captcha service (optional — set TWO_CAPTCHA_KEY env var)

        Returns True if a CAPTCHA was bypassed, False if none detected or all tiers exhausted.
        """
        import os as _os
        try:
            content = await page.content()
            content_lower = content.lower()

            # ─── Detection ────────────────────────────────────────────────────────
            page_title = ""
            try:
                page_title = (await page.title()).lower()
            except Exception:
                pass

            cf_iuam_strings = [
                "just a moment", "checking your browser", "ddos protection by cloudflare",
                "cf-chl-widget", "cf_clearance", "turnstile", "please stand by"
            ]
            is_cloudflare = (
                any(s in content_lower for s in cf_iuam_strings)
                or any(s in page_title for s in cf_iuam_strings)
                or await page.locator('iframe[src*="cloudflare"], iframe[src*="turnstile"], [class*="cf-turnstile"]').count() > 0
            )

            strong_indicators = [
                "captcha", "recaptcha", "hcaptcha", "g-recaptcha", "h-captcha",
                "math-problem", "anti-bot", "bot-check", "security-check",
                "captcha-input", "captcha-container", "are you human", "robot",
                "prove you", "vérifiez que vous", "je ne suis pas un robot"
            ]
            has_strong = (
                is_cloudflare
                or any(ind in content_lower for ind in strong_indicators)
                or "captcha" in page.url.lower()
            )

            if not has_strong:
                weak_indicators = [
                    "vérification", "verification", "calcul", "calculation",
                    "résolvez", "sécurité", "security challenge"
                ]
                has_weak = any(ind in content_lower for ind in weak_indicators)
                if has_weak:
                    has_captcha_input = await page.evaluate('''() => {
                        if (document.querySelector('iframe[src*="cloudflare"], iframe[src*="turnstile"]')) return true;
                        return document.querySelectorAll(
                            'input[name*="captcha"], input[id*="captcha"], input[name="result"], ' +
                            'input[id="result"], .captcha-input, .result-input, ' +
                            'input[name="answer"], input[id="answer"]'
                        ).length > 0;
                    }''')
                    if not has_captcha_input:
                        return False
                else:
                    return False

            logger.info("🛡️ CAPTCHA/Anti-Bot confirmed! Starting multi-tier bypass...")
            url_before = page.url
            html_before_hash = hashlib.md5((await page.content())[:3000].encode()).hexdigest()

            # Human warm-up before touching anything
            await self._simulate_human(page)

            # ═══════════════════════════════════════════════════════
            # TIER 0a: Cloudflare IUAM / Turnstile
            # ═══════════════════════════════════════════════════════
            if is_cloudflare:
                logger.info("☁️ TIER 0a: Cloudflare detected — attempting stealth bypass...")

                # Phase 1: Wait passively — Cloudflare JS challenge often self-solves with real browser
                for wait_attempt in range(3):
                    logger.info(f"☁️ Passive wait {wait_attempt+1}/3 (5s)...")
                    await asyncio.sleep(5)
                    try:
                        await page.wait_for_load_state("networkidle", timeout=4000)
                    except Exception:
                        pass
                    url_now = page.url
                    hash_now = hashlib.md5((await page.content())[:3000].encode()).hexdigest()
                    if self._page_changed(url_before, html_before_hash, url_now, hash_now):
                        if not await self._captcha_still_present(page):
                            logger.info("✅ TIER 0a SUCCESS: Cloudflare resolved passively!")
                            return True
                        logger.info("☁️ Page changed but CAPTCHA still present, continuing...")
                        url_before = url_now
                        html_before_hash = hash_now

                # Phase 2: Try clicking the Turnstile checkbox at multiple positions
                cf_selectors = [
                    'iframe[src*="turnstile"]',
                    'iframe[src*="cloudflare"]',
                    '[class*="cf-turnstile"] iframe',
                    'iframe[title*="cloudflare"]',
                ]
                click_positions = [
                    {"x": 25, "y": 25},   # typical checkbox center
                    {"x": 30, "y": 30},
                    {"x": 20, "y": 20},
                    {"x": 35, "y": 35},
                    {"x": 28, "y": 18},
                ]
                for cf_sel in cf_selectors:
                    cf_loc = page.locator(cf_sel).first
                    if await cf_loc.count() == 0:
                        continue
                    for pos in click_positions:
                        try:
                            logger.info(f"☁️ Clicking Turnstile iframe at {pos}...")
                            await cf_loc.scroll_into_view_if_needed()
                            await asyncio.sleep(0.3)
                            await cf_loc.hover(position=pos)
                            await asyncio.sleep(random.uniform(0.3, 0.8))
                            await cf_loc.click(position=pos, force=True)
                            logger.info("☁️ Clicked — waiting 10s for challenge resolution...")
                            await asyncio.sleep(10)
                            url_now = page.url
                            hash_now = hashlib.md5((await page.content())[:3000].encode()).hexdigest()
                            if self._page_changed(url_before, html_before_hash, url_now, hash_now):
                                if not await self._captcha_still_present(page):
                                    logger.info(f"✅ TIER 0a SUCCESS: Turnstile bypassed at position {pos}!")
                                    return True
                        except Exception as e:
                            logger.debug(f"☁️ Click attempt failed at {pos}: {e}")
                            continue
                    break  # Only try first matching selector

                # Phase 3: Try the Turnstile inside nested frames
                try:
                    for frame in page.frames:
                        frame_url = frame.url or ""
                        if "turnstile" in frame_url or "cloudflare" in frame_url:
                            cb = frame.locator('input[type="checkbox"], .ctp-checkbox-label, [id*="checkbox"]').first
                            if await cb.count() > 0:
                                logger.info("☁️ Found checkbox inside Cloudflare frame!")
                                await cb.click(force=True)
                                await asyncio.sleep(8)
                                if not await self._captcha_still_present(page):
                                    logger.info("✅ TIER 0a SUCCESS: Cloudflare checkbox clicked in frame!")
                                    return True
                except Exception as e:
                    logger.debug(f"☁️ Frame checkbox attempt failed: {e}")

                logger.warning("☁️ Tier 0a exhausted — Cloudflare not bypassed automatically.")

            # ═══════════════════════════════════════════════════════
            # TIER 0b: reCAPTCHA / hCaptcha checkbox ("I'm not a robot")
            # ═══════════════════════════════════════════════════════
            logger.info("🤖 TIER 0b: Checking for reCAPTCHA/hCaptcha checkbox...")
            try:
                checkbox_selectors = [
                    '.recaptcha-checkbox', '#recaptcha-anchor', '[class*="recaptcha-checkbox"]',
                    '.hcaptcha-box', '.checkbox', 'div[role="checkbox"]',
                ]
                for frame in page.frames:
                    for sel in checkbox_selectors:
                        cb = frame.locator(sel).first
                        if await cb.count() > 0 and await cb.is_visible():
                            logger.info(f"🤖 Found CAPTCHA checkbox ({sel}) — clicking...")
                            # Realistic human interaction: small offset + delay
                            await cb.hover()
                            await asyncio.sleep(random.uniform(0.5, 1.2))
                            await cb.click(force=True)
                            await asyncio.sleep(4)
                            if not await self._captcha_still_present(page):
                                logger.info("✅ TIER 0b SUCCESS: reCAPTCHA/hCaptcha checkbox passed!")
                                return True
                            # May have triggered an image challenge — fall through to Tier 1.7
                            logger.info("🤖 Checkbox clicked but image challenge appeared — continuing tiers...")
                            break
            except Exception as e:
                logger.debug(f"🤖 Tier 0b error: {e}")

            # ═══════════════════════════════════════════════════════
            # TIER 1: AI LLM Analysis (text + vision, 2 retries)
            # ═══════════════════════════════════════════════════════
            captcha_type = "unknown"
            ai_input_sel = ""
            ai_submit_sel = ""
            for ai_attempt in range(2):
                logger.info(f"🧠 TIER 1: AI CAPTCHA Analysis — attempt {ai_attempt+1}/2...")
                try:
                    screenshot_bytes = await page.screenshot(type="jpeg", quality=80)
                    b64_img = base64.b64encode(screenshot_bytes).decode('utf-8')
                except Exception:
                    b64_img = None

                # Refresh content in case page changed
                current_content = await page.content()
                ai_result = self.llm.solve_captcha(current_content, page.url, base64_image=b64_img)

                captcha_type = ai_result.get("type", "unknown")
                ai_answer = ai_result.get("answer")
                ai_confidence = ai_result.get("confidence", 0)
                ai_input_sel = ai_result.get("input_selector", "")
                ai_submit_sel = ai_result.get("submit_selector", "")

                logger.info(f"🧠 AI: type={captcha_type}, answer={ai_answer}, confidence={ai_confidence}%")

                if ai_answer and ai_confidence >= 65:
                    logger.info(f"🧠 Applying AI answer: '{ai_answer}'")
                    solved = await self._apply_captcha_answer(page, str(ai_answer), ai_input_sel, ai_submit_sel)
                    if solved:
                        logger.info("✅ TIER 1 SUCCESS: AI solved the CAPTCHA!")
                        return True
                    logger.warning("🧠 AI answer submitted but page unchanged — retrying...")
                    await asyncio.sleep(2)
                elif ai_confidence < 65:
                    logger.info(f"🧠 AI confidence too low ({ai_confidence}%), skipping answer application.")
                    break

            # ═══════════════════════════════════════════════════════
            # TIER 1.5: Audio Challenge (reCAPTCHA/hCaptcha, 2 retries)
            # ═══════════════════════════════════════════════════════
            for audio_attempt in range(2):
                logger.info(f"🔊 TIER 1.5: Audio Challenge solver — attempt {audio_attempt+1}/2...")
                audio_solved = await self._solve_audio_captcha(page)
                if audio_solved:
                    logger.info("✅ TIER 1.5 SUCCESS: Audio CAPTCHA solved!")
                    return True
                if audio_attempt == 0:
                    await asyncio.sleep(2)

            # ═══════════════════════════════════════════════════════
            # TIER 1.7: Visual Image Grid (llava VLM, 2 retries)
            # ═══════════════════════════════════════════════════════
            for vis_attempt in range(2):
                logger.info(f"👁️ TIER 1.7: Visual grid solver — attempt {vis_attempt+1}/2...")
                visual_solved = await self._solve_visual_captcha(page)
                if visual_solved:
                    logger.info("✅ TIER 1.7 SUCCESS: Visual CAPTCHA solved!")
                    return True
                if vis_attempt == 0:
                    await asyncio.sleep(2)

            # ═══════════════════════════════════════════════════════
            # TIER 2: Heuristic Math Solver (DOM + regex, 3 retries)
            # ═══════════════════════════════════════════════════════
            logger.info("🔧 TIER 2: Heuristic math solver...")
            for math_attempt in range(3):
                fresh_content = await page.content()
                heuristic_solved = await self._solve_math_captcha_heuristic(page, fresh_content)
                if heuristic_solved:
                    logger.info(f"✅ TIER 2 SUCCESS: Math CAPTCHA solved (attempt {math_attempt+1})!")
                    return True
                if math_attempt < 2:
                    await asyncio.sleep(2)

            # ═══════════════════════════════════════════════════════
            # TIER 3: 2captcha / Anti-Captcha Service (optional)
            # ═══════════════════════════════════════════════════════
            two_captcha_key = _os.getenv("TWO_CAPTCHA_KEY", "") or _os.getenv("ANTI_CAPTCHA_KEY", "")
            if two_captcha_key:
                logger.info("🔑 TIER 3: External CAPTCHA service (2captcha/Anti-Captcha)...")
                solved = await self._solve_via_service(page, two_captcha_key, captcha_type)
                if solved:
                    logger.info("✅ TIER 3 SUCCESS: External service solved the CAPTCHA!")
                    return True
            else:
                logger.info("🔑 TIER 3 skipped (set TWO_CAPTCHA_KEY or ANTI_CAPTCHA_KEY env var to enable).")

            logger.warning("❌ All CAPTCHA bypass tiers exhausted — could not solve automatically.")
            return False

        except Exception as e:
            logger.warning(f"🛡️ CAPTCHA solver top-level error: {e}")
            return False

    async def _solve_via_service(self, page, api_key: str, captcha_type: str) -> bool:
        """
        Submits the CAPTCHA to 2captcha API for solving.
        Supports: recaptcha v2, hcaptcha, image/text CAPTCHAs.
        API docs: https://2captcha.com/api-docs
        """
        import requests as _req
        try:
            page_url = page.url

            # Detect sitekey for reCAPTCHA/hCaptcha
            sitekey = await page.evaluate('''() => {
                const rc = document.querySelector('[data-sitekey]');
                if (rc) return rc.getAttribute('data-sitekey');
                const irc = document.querySelector('.g-recaptcha, .h-captcha');
                if (irc) return irc.getAttribute('data-sitekey');
                return null;
            }''')

            is_recaptcha = captcha_type == "recaptcha" or await page.locator('.g-recaptcha, [data-sitekey]').count() > 0
            is_hcaptcha = captcha_type == "hcaptcha" or await page.locator('.h-captcha').count() > 0

            if sitekey and (is_recaptcha or is_hcaptcha):
                method = "hcaptcha" if is_hcaptcha else "userrecaptcha"
                params = {
                    "key": api_key,
                    "method": method,
                    "sitekey": sitekey,
                    "pageurl": page_url,
                    "json": 1,
                }
                logger.info(f"🔑 2captcha: Submitting {method} with sitekey={sitekey[:20]}...")
                resp = _req.post("http://2captcha.com/in.php", data=params, timeout=20)
                if resp.json().get("status") != 1:
                    logger.warning(f"🔑 2captcha submission failed: {resp.text}")
                    return False

                task_id = resp.json()["request"]
                logger.info(f"🔑 2captcha task ID: {task_id} — polling for result...")

                # Poll for result (max 60s)
                for _ in range(12):
                    await asyncio.sleep(5)
                    res = _req.get(
                        f"http://2captcha.com/res.php?key={api_key}&action=get&id={task_id}&json=1",
                        timeout=10
                    )
                    data = res.json()
                    if data.get("status") == 1:
                        token = data["request"]
                        logger.info(f"🔑 2captcha solved! Token: {token[:30]}...")
                        # Inject token into page
                        await page.evaluate(f'''(token) => {{
                            const ta = document.querySelector('#g-recaptcha-response, textarea[name="g-recaptcha-response"]');
                            if (ta) {{ ta.value = token; ta.style.display = 'block'; }}
                            const ha = document.querySelector('[name="h-captcha-response"]');
                            if (ha) {{ ha.value = token; }}
                            if (window.___grecaptcha_cfg) {{
                                Object.keys(window.___grecaptcha_cfg.clients || {{}}).forEach(k => {{
                                    const c = window.___grecaptcha_cfg.clients[k];
                                    const cb = c?.aa?.callback || c?.l?.callback;
                                    if (typeof cb === 'function') cb(token);
                                }});
                            }}
                        }}''', token)
                        await asyncio.sleep(2)
                        # Try to submit the form
                        for submit_sel in ['[type="submit"]', 'button[class*="submit"]', '#recaptcha-demo-submit']:
                            try:
                                loc = page.locator(submit_sel).first
                                if await loc.count() > 0 and await loc.is_visible():
                                    await loc.click()
                                    await asyncio.sleep(3)
                                    return not await self._captcha_still_present(page)
                            except Exception:
                                continue
                        return not await self._captcha_still_present(page)
                    elif data.get("request") == "CAPCHA_NOT_READY":
                        continue
                    else:
                        logger.warning(f"🔑 2captcha error: {data}")
                        return False

            # Fallback: image-based CAPTCHA
            try:
                screenshot_bytes = await page.screenshot(type="jpeg", quality=70)
                b64_img = base64.b64encode(screenshot_bytes).decode('utf-8')
                params = {"key": api_key, "method": "base64", "body": b64_img, "json": 1}
                resp = _req.post("http://2captcha.com/in.php", data=params, timeout=20)
                if resp.json().get("status") != 1:
                    return False
                task_id = resp.json()["request"]
                for _ in range(10):
                    await asyncio.sleep(5)
                    res = _req.get(
                        f"http://2captcha.com/res.php?key={api_key}&action=get&id={task_id}&json=1",
                        timeout=10
                    )
                    data = res.json()
                    if data.get("status") == 1:
                        answer = data["request"]
                        return await self._apply_captcha_answer(page, answer, "", "")
                    elif data.get("request") != "CAPCHA_NOT_READY":
                        return False
            except Exception as e:
                logger.warning(f"🔑 2captcha image fallback error: {e}")

            return False
        except Exception as e:
            logger.warning(f"🔑 External CAPTCHA service error: {e}")
            return False

    async def _apply_captcha_answer(self, page, answer: str, input_selector: str, submit_selector: str) -> bool:
        """Fills the answer into the input field and clicks submit. Returns True if page changed."""
        url_before = page.url
        html_before_hash = hashlib.md5((await page.content())[:3000].encode()).hexdigest()
        
        try:
            # Try AI-suggested selector first, then common fallbacks
            input_selectors = [s for s in [input_selector] if s] + [
                '#result', 'input[name="result"]', 'input[name="captcha"]',
                'input[name="answer"]', '.captcha-input', 'input[type="number"]',
                'input[type="text"]:not([name="email"]):not([name="password"])'
            ]
            
            filled = False
            for sel in input_selectors:
                try:
                    loc = page.locator(sel).first
                    if await loc.count() > 0 and await loc.is_visible():
                        await loc.click() # Click the input first to focus
                        await asyncio.sleep(random.uniform(0.2, 0.6))
                        # Type with realistic human latency
                        await loc.type(answer, delay=random.randint(100, 250))
                        logger.info(f"📝 Typed CAPTCHA answer '{answer}' in '{sel}' with human delay")
                        filled = True
                        break
                except:
                    continue
            
            if not filled:
                logger.warning("❌ Could not find any input field for CAPTCHA answer")
                return False
            
            # Click submit
            await asyncio.sleep(0.5)
            submit_selectors = [s for s in [submit_selector] if s] + [
                'button[type="submit"]', 'input[type="submit"]', '.submit-btn',
                'button:has-text("Vérifier")', 'button:has-text("Verify")',
                'button:has-text("Submit")', 'button:has-text("Valider")',
                'button:has-text("OK")', 'button:has-text("Envoyer")'
            ]
            
            clicked = False
            for sel in submit_selectors:
                try:
                    loc = page.locator(sel).first
                    if await loc.count() > 0 and await loc.is_visible():
                        await loc.hover() # Hover button before clicking
                        await asyncio.sleep(random.uniform(0.5, 1.5))
                        await loc.click()
                        logger.info(f"🖱️ Clicked submit: '{sel}'")
                        clicked = True
                        break
                except:
                    continue
            
            if not clicked:
                logger.warning("❌ Could not find submit button")
                return False
            
            # Verify page changed
            await asyncio.sleep(2)
            try:
                await page.wait_for_load_state("networkidle", timeout=5000)
            except:
                pass
            
            html_after_hash = hashlib.md5((await page.content())[:3000].encode()).hexdigest()
            page_changed = (page.url != url_before) or (html_after_hash != html_before_hash)
            
            if page_changed:
                logger.info("✅ Page changed after CAPTCHA submission!")
            else:
                logger.warning("⚠️ Page did not change after CAPTCHA submission")
            
            return page_changed
            
        except Exception as e:
            logger.warning(f"❌ CAPTCHA answer application failed: {e}")
            return False

    async def _solve_math_captcha_heuristic(self, page, content: str) -> bool:
        """Heuristic math CAPTCHA solver (regex + DOM extraction)."""
        try:
            # Strategy 1: Extract from specific ID elements
            first_num = await page.evaluate('''() => {
                const el = document.getElementById("firstNumber") || 
                           document.querySelector("[id*='first']") ||
                           document.querySelector(".math-problem span:first-child");
                return el ? parseInt(el.innerText) : null;
            }''')
            
            operator = await page.evaluate('''() => {
                const el = document.getElementById("operator") ||
                           document.querySelector("[id*='operator']") ||
                           document.querySelector(".math-problem span:nth-child(2)");
                return el ? el.innerText.trim() : null;
            }''')
            
            second_num = await page.evaluate('''() => {
                const el = document.getElementById("secondNumber") ||
                           document.querySelector("[id*='second']") ||
                           document.querySelector(".math-problem span:nth-child(3)");
                return el ? parseInt(el.innerText) : null;
            }''')
            
            # Strategy 2: Regex fallback (with textual number normalisation)
            if first_num is None or operator is None or second_num is None:
                logger.info("🔢 Trying regex fallback for math extraction...")
                # Normalise textual numbers (FR/EN) → digits before applying regex
                _text_to_num = {
                    'zéro': '0', 'zero': '0',
                    'une': '1', 'un': '1', 'one': '1',
                    'deux': '2', 'two': '2',
                    'trois': '3', 'three': '3',
                    'quatre': '4', 'four': '4',
                    'cinq': '5', 'five': '5',
                    'six': '6',
                    'sept': '7', 'seven': '7',
                    'huit': '8', 'eight': '8',
                    'neuf': '9', 'nine': '9',
                    'dix': '10', 'ten': '10',
                }
                normalised = content
                for word, digit in _text_to_num.items():
                    normalised = re.sub(r'\b' + word + r'\b', digit, normalised, flags=re.IGNORECASE)
                math_match = re.search(r'(\d+)\s*([+\-×*x/÷])\s*(\d+)\s*=', normalised)
                if math_match:
                    first_num = int(math_match.group(1))
                    operator = math_match.group(2)
                    second_num = int(math_match.group(3))
            
            if first_num is None or operator is None or second_num is None:
                return False
            
            # Normalize operator
            if operator in ['×', 'x', 'X', '*']:
                operator = '*'
            elif operator in ['÷', '/']:
                operator = '/'
                
            # Calculate
            result = None
            if operator == '+': result = first_num + second_num
            elif operator == '-': result = first_num - second_num
            elif operator == '*': result = first_num * second_num
            elif operator == '/': result = first_num // second_num if second_num != 0 else 0
            
            if result is None:
                return False
            
            logger.info(f"🔢 Heuristic Math: {first_num} {operator} {second_num} = {result}")
            return await self._apply_captcha_answer(page, str(result), "", "")
            
        except Exception as e:
            logger.warning(f"🔢 Heuristic math solver error: {e}")
            return False

    async def _solve_audio_captcha(self, page) -> bool:
        """Finds the audio challenge button, downloads the MP3/WAV, transcribes it, and submits."""
        try:
            # 1. Look for the audio button (e.g. reCAPTCHA headphones icon)
            audio_btn_selectors = [
                'button.rc-button-audio', '#recaptcha-audio-button', 
                '.hcaptcha-audio-button', 'button[title*="audio"]'
            ]
            
            audio_btn = None
            for iframe in page.frames:
                for sel in audio_btn_selectors:
                    loc = iframe.locator(sel).first
                    if await loc.count() > 0 and await loc.is_visible():
                        audio_btn = loc
                        break
                if audio_btn: break
                
            if not audio_btn:
                return False
                
            logger.info("🔊 Found Audio Challenge button! Clicking...")
            await audio_btn.click()
            await asyncio.sleep(2)
            
            # 2. Find the audio source URL
            audio_url = None
            for iframe in page.frames:
                loc = iframe.locator('audio').first
                if await loc.count() > 0:
                    src = await loc.get_attribute('src')
                    if src:
                        # Handle relative URLs
                        if src.startswith('/'):
                            parsed = urlparse(page.url)
                            src = f"{parsed.scheme}://{parsed.netloc}{src}"
                        audio_url = src
                        break
                        
            if not audio_url:
                # Some reCAPTCHA versions put a download link instead of <audio> tag sometimes
                for iframe in page.frames:
                    loc = iframe.locator('a.rc-audiochallenge-edownload-link').first
                    if await loc.count() > 0:
                        audio_url = await loc.get_attribute('href')
                        break
                        
            if not audio_url:
                logger.warning("🔊 Audio challenge found but couldn't locate MP3 source.")
                return False
                
            logger.info(f"🔊 Downloading audio challenge: {audio_url[:50]}...")
            
            # 3. Download and convert to WAV
            import tempfile
            import os
            
            temp_mp3 = tempfile.mktemp(suffix=".mp3")
            temp_wav = tempfile.mktemp(suffix=".wav")
            
            # Download using requests to handle headers if needed
            import requests
            r = requests.get(audio_url, timeout=10)
            if r.status_code != 200:
                logger.warning(f"🔊 Failed to download audio (Status {r.status_code})")
                return False
                
            with open(temp_mp3, 'wb') as f:
                f.write(r.content)
                
            # Convert MP3 to WAV via pydub (requires ffmpeg)
            try:
                audio = AudioSegment.from_file(temp_mp3)
                audio.export(temp_wav, format="wav")
            except Exception as e:
                logger.error(
                    f"🔊 Audio conversion failed: {e}. "
                    "ffmpeg is required for audio CAPTCHA solving. "
                    "Install it with: apt-get install ffmpeg  (or brew install ffmpeg on macOS). "
                    "Skipping audio tier."
                )
                return False
                
            # 4. Transcribe using SpeechRecognition
            logger.info("🔊 Transcribing audio via local SpeechRecognition (Sphinx/Google)...")
            recognizer = sr.Recognizer()
            with sr.AudioFile(temp_wav) as source:
                audio_data = recognizer.record(source)
                
            try:
                # Using Google's free STT endpoint for simplicity, Sphinx could be offline alternative
                text = recognizer.recognize_google(audio_data)
                logger.info(f"🔊 Transcribed text: '{text}'")
            except sr.UnknownValueError:
                logger.warning("🔊 Speech Recognition could not understand the audio")
                return False
            except sr.RequestError as e:
                logger.warning(f"🔊 Speech Recognition API error: {e}")
                return False
            finally:
                # Cleanup
                if os.path.exists(temp_mp3): os.remove(temp_mp3)
                if os.path.exists(temp_wav): os.remove(temp_wav)
                
            # 5. Input and Submit
            input_sel = '#audio-response, input[title*="audio"], .rc-response-input'
            submit_sel = '#recaptcha-verify-button, button[title*="verify"]'
            
            # Find the frame with the input
            for iframe in page.frames:
                loc = iframe.locator(input_sel).first
                if await loc.count() > 0 and await loc.is_visible():
                    await loc.fill(text)
                    await asyncio.sleep(0.5)
                    sub_loc = iframe.locator(submit_sel).first
                    if await sub_loc.count() > 0:
                        await sub_loc.click()
                        logger.info("🔊 Audio answer submitted! Waiting for resolution...")
                        await asyncio.sleep(3)
                        return True
                        
            return False
            
        except Exception as e:
            logger.warning(f"🔊 Audio solver error: {e}")
            return False

    async def _solve_visual_captcha(self, page) -> bool:
        """Finds an image grid CAPTCHA, screenshots it, queries VLM, and clicks the coordinates."""
        try:
            # 1. Locate the CAPTCHA frame and image grid
            # This covers reCAPTCHA and hCaptcha standard 3x3 grids or 4x4
            grid_selectors = [
                '#rc-imageselect', '.rc-imageselect-payload',
                '.hcaptcha-challenge-wrap', '.challenge-container'
            ]
            
            grid_loc = None
            grid_frame = None
            for iframe in page.frames:
                for sel in grid_selectors:
                    loc = iframe.locator(sel).first
                    if await loc.count() > 0 and await loc.is_visible():
                        grid_loc = loc
                        grid_frame = iframe
                        break
                if grid_loc: break
                
            if not grid_loc:
                return False
                
            logger.info("👁️ Found Image Grid CAPTCHA! Attempting visual solve...")
            
            # 2. Extract instructions
            instruction = "Select the requested images."
            inst_selectors = ['.rc-imageselect-instructions', '.prompt-text', '.challenge-instructions']
            for sel in inst_selectors:
                loc = grid_frame.locator(sel).first
                if await loc.count() > 0:
                    instruction = await loc.inner_text()
                    break
                    
            logger.info(f"👁️ Challenge: '{instruction}'")
            
            # 3. Screenshot the grid wrapper
            screenshot_bytes = await grid_loc.screenshot(type="jpeg", quality=80)
            b64_img = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # 4. Ask VLM which tiles to click (3x3 default, some are 4x4)
            # We assume 3x3 for simplicity
            tiles_to_click = self.llm.solve_captcha_visual(b64_img, instruction, "3x3")
            if not tiles_to_click:
                logger.warning("👁️ Vision AI returned no tiles to click.")
                return False
                
            # 5. Click the tiles
            # Tiles are usually <td> or <li> inside the grid wrapper
            # For 3x3 (9 tiles), index 1 is [0,0], index 2 is [0,1], etc.
            tile_selectors = ['.rc-image-tile-wrapper', '.task-image', '.challenge-image']
            tiles_loc = None
            for sel in tile_selectors:
                locs = grid_frame.locator(sel)
                if await locs.count() > 0:
                    tiles_loc = locs
                    break
                    
            if not tiles_loc:
                logger.warning("👁️ Could not find individual tiles to click.")
                return False
                
            num_tiles = await tiles_loc.count()
            logger.info(f"👁️ Found {num_tiles} interactable tiles in the grid.")
            
            clicked = False
            for t_num in tiles_to_click:
                if 1 <= t_num <= num_tiles:
                    idx = t_num - 1
                    logger.info(f"👁️ Clicking tile {t_num} (index {idx})...")
                    await tiles_loc.nth(idx).click()
                    await asyncio.sleep(0.5)
                    clicked = True
                    
            if not clicked:
                return False
                
            # 6. Click Verify/Next
            await asyncio.sleep(1)
            submit_selectors = ['#recaptcha-verify-button', '.verify-button', 'button[title*="verify"]']
            for sel in submit_selectors:
                loc = grid_frame.locator(sel).first
                if await loc.count() > 0 and await loc.is_visible():
                    logger.info("👁️ Clicking Verify button...")
                    await loc.click()
                    await asyncio.sleep(4)
                    return True
                    
            return False
            
        except Exception as e:
            logger.warning(f"👁️ Visual solver error: {e}")
            return False

    async def smart_interact(self, page) -> List[Dict[str, Any]]:
        """
        AI-Powered Adaptive Crawler: Interacts with the page using intelligent phishing detection.
        - Uses AI to analyze and rank elements proactively
        - Detects phishing patterns at each step
        - Combines heuristic + AI scoring (30% heuristic, 70% AI)
        - Detects loops/stagnation and switches to exhaustive clicking.
        """
        journey_log = []
        max_steps = 25 
        
        # Tracking State
        seen_states = set() # Hash of (URL + HTML snippet)
        clicked_hashes = set() # Hash of button text/selector
        stagnation_count = 0
        loading_wait_count = 0
        form_was_filled = False  # track whether a form was submitted
        
        # Initial State
        await page.wait_for_load_state("networkidle")
        try: init_html = await page.content()
        except: init_html = ""
        
        # Initial AI Pattern Detection
        logger.info("🤖 AI: Analyzing initial page for phishing patterns...")
        initial_patterns = self.llm.detect_phishing_patterns(init_html, page.url)
        logger.info(f"🤖 AI Initial Analysis: Suspicion={initial_patterns.get('suspicion_score', '?')}%, Patterns={initial_patterns.get('detected_patterns', [])}")
        
        journey_log.append({
            "step": "step_00_initial",
            "description": f"Initial Page Load (AI Suspicion: {initial_patterns.get('suspicion_score', '?')}%)",
            "screenshot": await page.screenshot(full_page=True),
            "url": page.url,
            "html": init_html,
            "ai_patterns": initial_patterns
        })
        
        # Keywords for heuristic scoring - Extended French phishing detection
        priority_keywords = [
            # French
            "réclamer", "recevoir", "confirmer", "valider", "vérifier", "gagner", "obtenir", "participer",
            "commencer le sondage", "répondre au sondage", "récupérer", "profiter",
            # English
            "claim", "receive", "confirm", "verify", "win", "prize", "get", "participate"
        ]
        nav_keywords = [
            # French
            "commencer", "sondage", "continuer", "suivant", "oui", "non", "démarrer", "participer",
            "répondre", "questionnaire", "enquête", "accepter",
            # English
            "start", "survey", "continue", "next", "yes", "no", "begin", "accept"
        ]
        
        for i in range(1, max_steps + 1):
            logger.info(f"--- Interaction Step {i}/{max_steps} ---")
            await asyncio.sleep(2)
            
            # 1. State Check & fake loading detection
            try: content = await page.content()
            except: content = ""
            current_url = page.url
            
            # Simple state hash: URL + first 5000 chars of body text
            try: body_text = await page.inner_text("body", timeout=1000)
            except: body_text = ""
            state_hash = hashlib.md5((current_url + body_text[:5000]).encode('utf-8')).hexdigest()
            
            if state_hash in seen_states:
                logger.info(f"State Stagnation detected (Count: {stagnation_count})")
                stagnation_count += 1
            else:
                stagnation_count = 0
                seen_states.add(state_hash)
            
            # Check for fake loading screens
            if "vérification" in content.lower() or "checking" in content.lower() or "patientez" in content.lower():
                if loading_wait_count < 3:
                    logger.info(f"Loading screen detected (Attempt {loading_wait_count+1}/3). Waiting...")
                    await asyncio.sleep(4)
                    loading_wait_count += 1
                    continue
                else:
                    logger.info("Loading screen persistent. Ignoring and forcing interaction.")
            else:
                loading_wait_count = 0

            # 🍪 Cookie Banner Dismissal (before any interaction)
            try:
                _cookie_selectors = [
                    # Accept/agree buttons
                    "button#accept-cookie", "button#acceptAll", "button#accept_all",
                    "button[id*='accept']", "button[class*='accept']",
                    "button[id*='agree']", "button[class*='agree']",
                    "a[id*='accept']", "a[class*='accept-cookie']",
                    # French
                    "button:has-text('Accepter tout')", "button:has-text('Tout accepter')",
                    "button:has-text('Accepter')", "button:has-text('J\\'accepte')",
                    "button:has-text('Continuer sans accepter')",
                    # English
                    "button:has-text('Accept all')", "button:has-text('Accept All')",
                    "button:has-text('Accept cookies')", "button:has-text('I agree')",
                    "button:has-text('OK')", "button:has-text('Got it')",
                    # Generic consent wrappers
                    "#cookie-accept", "#cookie-consent-accept", ".cookie-accept",
                    "[data-testid*='cookie-accept']", "[aria-label*='cookie']",
                ]
                for _sel in _cookie_selectors:
                    _loc = page.locator(_sel).first
                    if await _loc.count() > 0 and await _loc.is_visible():
                        logger.info(f"🍪 Dismissing cookie banner: {_sel}")
                        await _loc.click(timeout=2000)
                        await asyncio.sleep(0.8)
                        break
            except Exception:
                pass

            # 🛡️ MULTI-TIER CAPTCHA SOLVER: AI → Heuristic → Manual Popup
            captcha_solved = await self._solve_captcha(page)
            if captcha_solved:
                logger.info("🛡️ CAPTCHA bypassed - reloading state...")
                journey_log.append({
                    "step": f"step_{i:02d}_captcha",
                    "description": "CAPTCHA bypassed (AI/Heuristic/Manual)",
                    "screenshot": await page.screenshot(full_page=True),
                    "url": page.url,
                    "html": await page.content()
                })
                continue # IMPORTANT: Re-evaluate the new page structure safely
                
            # If CAPTCHA is active but unsolved, do NOT interact with anything else
            try:
                page_text = (await page.content()).lower()
                is_captcha_active = "captcha" in page.url.lower() or "just a moment" in page_text or "cf-chl-widget" in page_text or "security-check" in page_text
                if is_captcha_active:
                    logger.warning("🚨 CAPTCHA is still active and unsolved. Halting exploration to prevent ban.")
                    journey_log.append({
                        "step": f"step_{i:02d}_blocked",
                        "description": "Exploration halted: CAPTCHA unsolved.",
                        "screenshot": await page.screenshot(full_page=True),
                        "url": page.url,
                        "html": await page.content()
                    })
                    break
            except: pass

            # ⚡ FAST PATH: Force click on "Commencer" / "Start" buttons proactively
            try:
                # Common priority keywords for phishing CTAs
                fast_track_regex = re.compile(r"commencer|start|sondage|survey|continuer|continue|réclamer|claim", re.IGNORECASE)
                # Find valid clickables using Playwright Locator (reliable)
                fast_buttons = await page.locator('button, a, input[type="submit"], div[class*="btn"], div[role="button"]').filter(has_text=fast_track_regex).all()
                clicked_fast = False
                for btn in fast_buttons:
                    if await btn.is_visible():
                        # Verify text length to avoid clicking huge containers
                        txt = (await btn.inner_text()).strip()
                        if len(txt) < 50: 
                            logger.info(f"⚡ FAST TRACK: Clicking detected priority button: '{txt}'")
                            # Highlight for screenshot
                            await btn.evaluate("el => el.style.border = '5px solid red'")
                            await asyncio.sleep(0.5)
                            await btn.click(force=True, timeout=2000)
                            clicked_fast = True
                            await asyncio.sleep(3) # Wait for reaction
                            break # Only click one per cycle
                
                if clicked_fast:
                    logger.info("⚡ Fast Track Action Taken - Reloading state...")
                    continue # Skip AI analysis, re-evaluate page
            except Exception as e:
                logger.warning(f"Fast Track check failed: {e}")

            # 2. AI Pattern Detection at each step
            logger.info("🤖 AI: Analyzing current page for phishing patterns...")
            patterns = self.llm.detect_phishing_patterns(content, current_url)
            
            if patterns.get("is_final_payload_page") or patterns.get("recommendation") == "stop_reached_payload":
                journey_log.append({
                    "step": f"step_{i:02d}_suspicious",
                    "description": f"[SUSPICIOUS PAGE] {patterns.get('detected_patterns', [])}",
                    "screenshot": await page.screenshot(full_page=True),
                    "url": current_url,
                    "html": content,
                    "ai_patterns": patterns
                })
                if form_was_filled:
                    logger.info("🎯 Final payload page detected after form submission — stopping exploration.")
                    break
                else:
                    logger.info("🎯 AI detected Suspicious Page — continuing to go deeper...")

            # 3. Gather interactive elements
            candidates = []
            try:
                candidates = await page.evaluate(r"""
                () => {
                    // Helper to get text content clean
                    const getText = (el) => (el.innerText || el.textContent || "").trim();
                    
                    // Specific strategy for "Commencer" / "Start" buttons that might be divs or spans
                    const allUrlElements = Array.from(document.querySelectorAll('*'));
                    const keywords = ["commencer", "start", "sondage", "survey", "continuer", "continue", "répondre", "answer", "participer", "participate"];
                    
                    const textMatches = allUrlElements.filter(el => {
                        const txt = getText(el).toLowerCase();
                        // Element must have one of the keywords as its MAIN text (short length)
                        if (txt.length > 0 && txt.length < 30 && keywords.some(k => txt.includes(k))) {
                             // Must be visible and leaf or close to leaf (no big containers)
                             if (el.children.length < 3) return true;
                        }
                        return false;
                    });

                    const standardItems = Array.from(document.querySelectorAll('button, a, input[type="submit"], div[role="button"], span[class*="btn"], [onclick]'));
                    
                    // Combine and dedupe
                    const combined = [...new Set([...standardItems, ...textMatches])];

                    return combined.map(el => {
                        const rect = el.getBoundingClientRect();
                        return {
                            tagName: el.tagName.toLowerCase(),
                            text: getText(el),
                            href: el.href || '',
                            visible: (rect.width > 0 && rect.height > 0 && window.getComputedStyle(el).visibility !== 'hidden'),
                            role: el.getAttribute('role'),
                            className: el.className || '',
                            id: el.id || '',
                            outerHTML: el.outerHTML.slice(0, 300)
                        };
                    }).filter(item => item.visible && item.text.length > 0);
                }
                """)

            except Exception as e: logger.warning(f"JS Eval failed: {e}")

            # 3b. PROACTIVE: Fill Forms before clicking
            filled_actions = await self._fill_page_inputs(page)
            if filled_actions:
                form_was_filled = True
                desc = f"Form Auto-Fill: {', '.join(filled_actions)}"
                logger.info(f"📝 {desc}")
                # If we filled forms, we likely want to submit.
                # We don't break yet, we let the click logic find the submit button.

            # 4. AI-Powered Element Analysis (Proactive)
            ai_ranked_elements = []
            if candidates and stagnation_count < 5:
                logger.info(f"🤖 AI: Analyzing {len(candidates)} interactive elements...")
                ai_ranked_elements = self.llm.analyze_interactive_elements(candidates, current_url)
                
                # Build a lookup for AI scores
                ai_scores_map = {}
                for el in ai_ranked_elements:
                    if isinstance(el, dict):
                        key = el.get('text', '')
                        ai_scores_map[key] = {
                            'score': el.get('phishing_score', 50),
                            'reason': el.get('ai_reason', '')
                        }
            
            # 5. Hybrid Scoring: 30% Heuristic + 70% AI
            elements_to_try = []
            for c in candidates:
                heuristic_score = 10  # Base fallback score
                txt = c['text'].lower()
                
                # Heuristic scoring (exclusive tiers)
                if any(k in txt for k in priority_keywords):
                    heuristic_score = 150  # Boosted priority
                elif any(k in txt for k in nav_keywords):
                    heuristic_score = 100
                
                # Super Boost for "Commencer" / "Start" specifically
                if "commencer" in txt or "start" in txt:
                    heuristic_score += 200

                # Boost "Login" / "Submit" if we just filled a form
                if filled_actions and ("login" in txt or "connect" in txt or "submit" in txt or "valider" in txt):
                    heuristic_score += 150
                
                # AI scoring
                ai_data = ai_scores_map.get(c['text'], {'score': 50, 'reason': ''}) if ai_ranked_elements else {'score': 50, 'reason': ''}
                ai_score = ai_data['score']
                
                # Hybrid: 30% heuristic + 70% AI
                final_score = (heuristic_score * 0.3) + (ai_score * 0.7)
                
                # Penalize already clicked
                c_hash = hashlib.md5((c['text'] + c['outerHTML']).encode('utf-8')).hexdigest()
                if c_hash in clicked_hashes: final_score -= 200
                
                # Penalize repeated URL links
                if c['href'] and c['href'] == current_url: final_score -= 50
                if c['href'] and any(step['url'] == c['href'] for step in journey_log): final_score -= 20

                if final_score > 0:
                    elements_to_try.append({
                        'score': final_score,
                        'candidate': c,
                        'hash': c_hash,
                        'ai_reason': ai_data['reason']
                    })
            
            elements_to_try.sort(key=lambda x: x['score'], reverse=True)
            
            # Log top candidates
            if elements_to_try:
                top_3 = elements_to_try[:3]
                logger.info(f"🤖 AI Top Candidates: {[(e['candidate']['text'][:30], round(e['score'])) for e in top_3]}")

            # 6. Action Logic
            clicked = False
            desc = ""
            ai_reason = ""
            
            # Try top ranked from hybrid scoring
            for elem_data in elements_to_try:
                cand = elem_data['candidate']
                c_hash = elem_data['hash']
                ai_reason = elem_data.get('ai_reason', '')
                score = elem_data['score']
                
                try:
                    # Construct robust selector
                    if cand['text']:
                        selector = f"text={cand['text']}"
                    else:
                        continue
                    
                    if await page.is_visible(selector):
                        logger.info(f"🤖 Interaction: Clicking '{cand['text']}' (Score: {score:.0f}, AI: {ai_reason[:50]})")
                        await page.click(selector, timeout=2000)
                        clicked = True
                        clicked_hashes.add(c_hash)
                        desc = f"Clicked '{cand['text']}' (AI: {ai_reason[:40]})"
                        break
                except: continue
                
            # Fallback: Stagnation → Scroll + Tab to reveal hidden elements
            if not clicked and stagnation_count >= 2:
                logger.info(f"⏬ Stagnation detected ({stagnation_count}x) — trying scroll + Tab to reveal elements...")
                try:
                    await page.mouse.wheel(0, random.randint(300, 600))
                    await asyncio.sleep(1.0)
                    await page.keyboard.press("Tab")
                    await asyncio.sleep(0.5)
                    # Try pressing Enter on the focused element (may be a button)
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(1.5)
                    logger.info("⏬ Scroll+Tab done — re-evaluating page on next iteration.")
                    continue
                except Exception as e:
                    logger.debug(f"Scroll+Tab strategy failed: {e}")

            # Fallback: AI Direct Suggestion (if hybrid fails)
            if not clicked and stagnation_count >= 3:
                logger.info("🤖 Heuristics exhausted. Asking AI for direct guidance...")
                try:
                    ai_decision = self.llm.get_next_action(content, current_url)
                    ai_selector = ai_decision.get("selector")
                    ai_reason = ai_decision.get("reason", "Unknown")
                    ai_confidence = ai_decision.get("confidence", 0)
                    
                    if ai_selector and ai_confidence > 50:
                        logger.info(f"🤖 AI Direct: '{ai_selector}' (Confidence: {ai_confidence}%) - {ai_reason}")
                        if await page.is_visible(ai_selector):
                            await page.click(ai_selector, timeout=3000)
                            clicked = True
                            desc = f"AI Clicked '{ai_selector}' ({ai_reason})"
                except Exception as e:
                    logger.error(f"AI Direct Interaction failed: {e}")

            # Fallback: Generic visible button
            if not clicked:
                try:
                    generic_selectors = ["button", "a", "div[role='button']", ".btn", "input[type='submit']"]
                    for sel in generic_selectors:
                        count = await page.locator(sel).count()
                        for idx in range(min(count, 10)):    
                            el = page.locator(sel).nth(idx)
                            if await el.is_visible():
                                txt = await el.text_content()
                                txt = txt.strip() if txt else "unknown"
                                c_hash = hashlib.md5((txt + sel + str(idx)).encode('utf-8')).hexdigest()
                                
                                if c_hash not in clicked_hashes:
                                    logger.info(f"Fallback Interaction: Clicking generic {sel} [{txt}]")
                                    await el.click(timeout=1000)
                                    clicked = True
                                    clicked_hashes.add(c_hash)
                                    desc = f"Clicked generic {sel}: '{txt}'"
                                    break
                        if clicked: break
                except: 
                    pass

            # 7. Wait and Log
            if clicked:
                try: await page.wait_for_load_state("networkidle", timeout=5000)
                except: await asyncio.sleep(2)
                
                screenshot = await page.screenshot(full_page=True)
                
                # Check for Payment Form (High Value)
                pay_found = False
                try:
                    if await page.locator("input[name*='card']").count() > 0 or await page.locator("#cc_number").count() > 0:
                        pay_found = True
                        desc += " [PAYMENT DETECTED]"
                except: pass

                try: html_snap = await page.content()
                except: html_snap = ""

                journey_log.append({
                    "step": f"step_{i:02d}",
                    "description": desc,
                    "screenshot": screenshot,
                    "url": page.url,
                    "html": html_snap,
                    "ai_patterns": patterns
                })
                
                if pay_found:
                    logger.info("💰 Payment Form Identified - Stopping Exploration")
                    break
            else:
                logger.info("No actionable elements found. Journey ends.")
                break
                
        print(f"DEBUG_CRITICAL: smart_interact returning {len(journey_log)} steps.")
        return journey_log

    async def analyze_url(self, url: str):
        """Navigates to the URL, interacts, and returns detailed forensics."""
        if not self.page: raise Exception("Browser not started")
 
        logger.info(f"Navigating to {url}")
        
        journey = []
        links = []
        inputs = []
        html_content = ""
        final_screenshot = b""
        
        try:
            # 1. Navigation
            response = await self.page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Reconstruct redirect chain
            if response:
                current_request = response.request
                redirects = []
                while current_request.redirected_from:
                    redirects.insert(0,  {
                        "url": current_request.redirected_from.url,
                        "status": "3xx", 
                        "type": "navigation_redirect"
                    })
                    current_request = current_request.redirected_from
                for r in redirects:
                     if not any(entry['url'] == r['url'] for entry in self.redirect_chain):
                         self.redirect_chain.append(r)
                self.redirect_chain.append({"url": response.url, "status": response.status, "type": "landing"})

            # 2. Smart Interaction
            logger.info("Starting interactive browsing session (Deep Scan)...")
            await self.page.screenshot(path="output/screenshot_initial.png")
            
            journey = await self.smart_interact(self.page)
            
            final_screenshot = journey[-1]["screenshot"] if journey else await self.page.screenshot(full_page=True)

            # 3. Content Extraction
            try:
                links = await self.page.evaluate("""() => {
                    return Array.from(document.querySelectorAll('a')).map(a => ({
                        text: a.innerText.trim(),
                        href: a.href
                    })).filter(l => l.href.length > 0);
                }""")
                inputs = await self.page.evaluate("""() => {
                    return Array.from(document.querySelectorAll('input, select, textarea')).map(i => ({
                        type: i.type || i.tagName.toLowerCase(),
                        name: i.name || i.id,
                        placeholder: i.placeholder || ''
                    }));
                }""")
                html_content = await self.page.content()
            except Exception as e:
                logger.warning(f"Content extraction failed: {e}")

            return {
                "redirect_chain": self.redirect_chain,
                "network_log": self.network_log,
                "screenshot": final_screenshot, 
                "interaction_journey": journey, 
                "final_url": self.page.url,
                "html": html_content,
                "links": links,
                "inputs": inputs
            }

        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return {
                "redirect_chain": self.redirect_chain,
                "network_log": self.network_log,
                "screenshot": final_screenshot or b"",
                "interaction_journey": journey,
                "final_url": self.page.url if self.page else url,
                "html": html_content,
                "links": links,
                "inputs": inputs,
                "error": str(e)
            }

    async def close(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

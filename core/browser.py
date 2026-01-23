import asyncio
import logging
import hashlib
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Response, Request
from core.llm import LLMAnalyzer


logger = logging.getLogger(__name__)

class BrowserManager:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.redirect_chain: List[Dict[str, Any]] = []
        self.network_log: List[Dict[str, Any]] = []
        self.network_log: List[Dict[str, Any]] = []
        self.downloaded_files: List[Dict[str, Any]] = []
        self.llm = LLMAnalyzer() # Initialize AI for smart detection
        
        # Fake Data for probing
        self.fake_data = {
            "email": "victim@example.com",
            "password": "Password123!",
            "tel": "0612345678",
            "text": "John Doe",
            "name": "John Doe",
            "cc": "4532000000000000",
            "cvv": "123",
            "exp": "12/28",
            "otp": "123456"
        }


    async def start(self, locale: str = "en-US", timezone_id: str = "America/New_York"):
        """Initializes Playwright and launches the browser."""
        self.playwright = await async_playwright().start()
        # Launch Chromium.
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=100, 
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale=locale,
            timezone_id=timezone_id,
            bypass_csp=True, 
            ignore_https_errors=True
        )

        await self._apply_stealth(self.context)
        self.page = await self.context.new_page()
        self.page.on("request", self._on_request)
        self.page.on("response", self._on_response)

    async def _apply_stealth(self, context: BrowserContext):
        """Injects scripts to mask automation."""
        stealth_js = """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ? Promise.resolve({ state: Notification.permission }) : originalQuery(parameters)
            );
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        """
        await context.add_init_script(stealth_js)

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
            
            if "vérification" in content.lower() or "checking" in content.lower() or "patientez" in content.lower():
                logger.info("Loading screen detected. Waiting...")
                await asyncio.sleep(4)
                continue

            # 2. AI Pattern Detection at each step
            logger.info("🤖 AI: Analyzing current page for phishing patterns...")
            patterns = self.llm.detect_phishing_patterns(content, current_url)
            
            if patterns.get("is_final_payload_page") or patterns.get("recommendation") == "stop_reached_payload":
                logger.info("🎯 AI detected FINAL PAYLOAD PAGE - Stopping exploration!")
                journey_log.append({
                    "step": f"step_{i:02d}_payload",
                    "description": f"[PAYLOAD DETECTED] {patterns.get('detected_patterns', [])}",
                    "screenshot": await page.screenshot(full_page=True),
                    "url": current_url,
                    "html": content,
                    "ai_patterns": patterns
                })
                break

            # 3. Gather interactive elements
            candidates = []
            try:
                candidates = await page.evaluate(r"""
                () => {
                    const items = Array.from(document.querySelectorAll('button, a, input[type="submit"], div[role="button"], span[class*="btn"], [onclick]'));
                    return items.map(el => {
                        const rect = el.getBoundingClientRect();
                        return {
                            tagName: el.tagName.toLowerCase(),
                            text: el.innerText.trim(),
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
                desc = f"Form Auto-Fill: {', '.join(filled_actions)}"
                logger.info(f"📝 {desc}")
                # If we filled forms, we likely want to submit. 
                # We don't break yet, we let the click logic find the submit button.
                # But we might want to capture this state change.

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
                heuristic_score = 0
                txt = c['text'].lower()
                
                # Heuristic scoring
                if any(k in txt for k in priority_keywords): heuristic_score = 100
                elif any(k in txt for k in nav_keywords): heuristic_score = 50
                
                # Boost "Login" / "Submit" if we just filled a form
                if filled_actions and ("login" in txt or "connect" in txt or "submit" in txt or "valider" in txt):
                    heuristic_score += 150

                else: heuristic_score = 10
                
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

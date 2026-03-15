import os
import time
import requests
import logging
import json
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class LLMAnalyzer:
    def __init__(self, model: str = "mistral"):
        self.model = model
        # Use env var for Docker compatibility, default to localhost
        base_host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
        # We only append /api/generate if it's not already there
        if not base_host.endswith("/api/generate"):
            self.api_url = f"{base_host}/api/generate"
        else:
            self.api_url = base_host

    def _call_ollama(self, payload: dict, timeout: int = 90, retries: int = 3) -> str:
        """Shared Ollama call with exponential backoff and safe JSON extraction."""
        last_err = None
        for attempt in range(retries):
            try:
                resp = requests.post(self.api_url, json=payload, timeout=timeout)
                resp.raise_for_status()
                result = resp.json().get("response", "")
                if isinstance(result, str):
                    return result.strip()
                return json.dumps(result)
            except requests.exceptions.ConnectionError as e:
                last_err = e
                logger.warning(f"[LLM] Ollama unreachable (attempt {attempt+1}/{retries}): {e}")
                time.sleep(2 ** attempt)
            except Exception as e:
                last_err = e
                logger.warning(f"[LLM] Call failed (attempt {attempt+1}/{retries}): {e}")
                time.sleep(2 ** attempt)
        logger.error(f"[LLM] All {retries} attempts failed: {last_err}")
        return ""

    def _call_ollama_json(self, payload: dict, timeout: int = 45, retries: int = 2) -> dict | list:
        """Like _call_ollama but parses and returns JSON, defaulting to {} on failure."""
        payload = {**payload, "format": "json"}
        raw = self._call_ollama(payload, timeout=timeout, retries=retries)
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract first JSON object/array from the string
            import re
            m = re.search(r'(\{.*\}|\[.*\])', raw, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(1))
                except Exception:
                    pass
            logger.warning(f"[LLM] Could not parse JSON response: {raw[:200]}")
            return {}

    def analyze_javascript(self, js_code: str, filename: str) -> str:
        """Analyzes a JavaScript snippet for malicious intent."""
        prompt = f"""Tu es un analyste malware. Analyse ce fichier JavaScript extrait d'un site de phishing.

FICHIER: {filename}
CODE (premiers 4000 caractères):
{js_code[:4000]}

TÂCHE:
1. Identifie l'objectif (obfuscation, redirection, fingerprinting, exfiltration de données, livraison de payload).
2. Mets en évidence les fonctions ou logiques dangereuses spécifiques.
3. Explique exactement ce que ce script tente de faire à la victime.
4. Indique le niveau de dangerosité: FAIBLE / MOYEN / ÉLEVÉ / CRITIQUE

Sois concis (4-5 phrases max). Réponds en français.
"""
        result = self._call_ollama({"model": self.model, "prompt": prompt, "stream": False}, timeout=90)
        return result or "Analyse indisponible."

    def analyze_journey_step(self, step_data: dict) -> str:
        """Analyzes a specific step in the user journey."""
        import re as _re
        # Extract visible text from HTML (strip tags) rather than sending raw markup
        html = step_data.get('html', '') or ''
        visible_text = _re.sub(r'<[^>]+>', ' ', html)
        visible_text = _re.sub(r'\s+', ' ', visible_text).strip()[:800]

        prompt = f"""
        Analyse this Phishing Interaction Step.

        Step: {step_data.get('step')}
        Action Taken: {step_data.get('description')}
        Current URL: {step_data.get('url')}
        Visible Page Text:
        {visible_text}

        Question:
        What is the attacker trying to do here? (e.g. build trust, simulate loading, extract data, redirect).
        Be very brief (1-2 sentences). Réponds en français.
        """
        result = self._call_ollama({"model": self.model, "prompt": prompt, "stream": False}, timeout=30, retries=2)
        return result or "Analyse ignorée."

    def analyze_report(self, report_data: dict) -> str:
        """Sends the report JSON to Ollama for a security summary."""

        journey_desc = "\n".join([f"- {s['step']}: {s['description']} (URL: {s.get('url','?')})" for s in report_data.get('interaction_journey', [])])

        chain = report_data.get('redirect_chain', [])
        final_url = chain[-1].get('url') if chain else report_data.get('target_url', 'Unknown')

        # Include visual analysis findings
        visual = report_data.get('visual_analysis', {}) or {}
        visual_info = ""
        if visual:
            visual_info = (
                f"\nVISUAL ANALYSIS:\n"
                f"  Brand detected: {visual.get('brand_detected', 'None')}\n"
                f"  Logos found: {visual.get('logos_found', [])}\n"
                f"  OCR text snippet: {str(visual.get('ocr_text', ''))[:200]}\n"
            )

        # Summarise POST submissions for the report
        post_submissions = [e for e in report_data.get("network_log", []) if e.get("type") == "post_submission"]
        post_info = ""
        if post_submissions:
            post_info = f"\nSOUMISSIONS POST ({len(post_submissions)}):\n"
            for ps in post_submissions[:5]:
                raw = ps.get("content", b"")
                data_str = (raw.decode("utf-8", errors="replace") if isinstance(raw, (bytes, bytearray)) else str(raw))[:300]
                post_info += f"  → {ps.get('url', '?')} | data: {data_str}\n"

        prompt = f"""Tu es un Expert en Cybersécurité analysant un scan de phishing complet.

DONNÉES:
Cible: {report_data.get('target_url')}
Chaîne de redirections: {len(chain)} saut(s). URL finale: {final_url}
Champs de saisie: {len(report_data.get('inputs', []))} (types: {[i.get('type') for i in report_data.get('inputs', [])[:5]]})
{visual_info}{post_info}
PARCOURS INTERACTIF (simulation victime):
{journey_desc}

ARTEFACTS TÉLÉCHARGÉS:
{json.dumps(report_data.get('files_extracted', []), indent=2)[:1500]}

TÂCHE — Rédige un Rapport Forensique Détaillé en Markdown comprenant:
1. **Résumé exécutif** : Nature de l'attaque, marque usurpée, objectif (collecte identifiants/CB/OTP).
2. **Analyse des preuves** : Cite les étapes spécifiques du parcours pour prouver l'intention malveillante.
3. **Techniques d'attaque** : Explique pourquoi les mécanismes (obfuscation, fake survey, urgence) sont efficaces.
4. **Mapping MITRE ATT&CK** : Liste les techniques applicables (ex: T1566.002, T1056.001, T1204.001).
5. **IOCs extraits** : Domaines, IPs, URLs de collecte identifiés.
6. **Évaluation de la sévérité** : FAIBLE / MOYEN / ÉLEVÉ / CRITIQUE avec justification.
7. **Recommandations** : Actions immédiates pour les victimes et équipes de sécurité.

Utilise le gras pour les points clés. Réponds entièrement en français.
"""

        logger.info(f"[LLM] Sending forensic report analysis to Ollama (model: {self.model})...")
        result = self._call_ollama({"model": self.model, "prompt": prompt, "stream": False}, timeout=120)
        if result:
            return result
        return "**Analyse indisponible** : Ollama ne répond pas. Vérifiez que `ollama serve` est lancé."

    def get_next_action(self, html_snippet: str, url: str) -> dict:
        """
        Asks the LLM to identify the next best action to progress through the phishing flow.
        Returns a dict: {"selector": "...", "action": "click", "reason": "...", "confidence": 0-100}
        """
        prompt = f"""
        You are an AI Phishing Crawler Agent specialized in detecting and navigating phishing websites.
        Your goal is to simulate a victim and click through the phishing campaign to reach the final credential/payment harvesting page.

        CURRENT PAGE: {url}
        HTML SNIPPET:
        {html_snippet[:3000]}
        
        PHISHING INDICATORS TO LOOK FOR:
        - Urgency words: "urgent", "limited time", "expires", "act now"
        - Reward words: "won", "winner", "congratulations", "prize", "gift", "reward"  
        - Action words: "claim", "receive", "confirm", "verify", "continue", "start", "next"
        - Fake branding: logos of known companies, misleading domain names
        - Suspicious buttons with bright colors or exclamation marks
        
        TASK:
        Identify the SINGLE best HTML element to CLICK to proceed deeper into the phishing flow.
        Prioritize elements that:
        1. Promise rewards or require "verification"
        2. Have urgency indicators
        3. Are prominent call-to-action buttons
        
        IGNORE: "Cancel", "Terms", "Privacy", "Close", navigation menus.

        RESPONSE FORMAT:
        Return ONLY a JSON object (no markdown, no extra text):
        {{
            "selector": "CSS selector to identify the element (e.g. 'button.submit' or 'a#btn-next' or 'text=Click Here')",
            "reason": "Brief explanation of why this element is likely part of the phishing flow",
            "confidence": 85,
            "is_phishing_cta": true
        }}
        """
        result = self._call_ollama_json(
            {"model": self.model, "prompt": prompt, "stream": False}, timeout=30
        )
        return result if isinstance(result, dict) else {}

    def analyze_interactive_elements(self, elements: list, url: str) -> list:
        """
        Analyzes a list of interactive elements and ranks them by phishing likelihood.
        Returns elements with AI-assigned scores.
        """
        if not elements:
            return []
        
        # Limit elements to avoid token overflow
        elements_summary = json.dumps(elements[:15], indent=2)
        
        prompt = f"""
        You are a Phishing Detection AI. Analyze these interactive elements from a suspected phishing page.
        
        URL: {url}
        ELEMENTS:
        {elements_summary}
        
        For each element, assign a "phishing_score" from 0-100 based on:
        - 90-100: Definitely a phishing call-to-action (claim prize, verify account, etc.)
        - 70-89: Likely phishing related (continue survey, next step, etc.)
        - 50-69: Possibly suspicious (generic buttons)
        - 0-49: Not suspicious (navigation, terms, close buttons)
        
        RESPONSE FORMAT:
        Return a JSON array with each element having its original properties PLUS:
        - "phishing_score": 0-100
        - "ai_reason": brief explanation
        
        Example:
        [
            {{"text": "Claim Your Prize", "phishing_score": 95, "ai_reason": "Classic phishing CTA"}},
            {{"text": "Cancel", "phishing_score": 10, "ai_reason": "Exit action, not phishing"}}
        ]
        """
        result = self._call_ollama_json(
            {"model": self.model, "prompt": prompt, "stream": False}, timeout=35
        )
        return result if isinstance(result, list) else elements

    def detect_phishing_patterns(self, html_content: str, url: str) -> dict:
        """
        Detects phishing patterns in the page content.
        Returns a dict with detected patterns and overall suspicion score.
        """
        prompt = f"""
        Analyze this webpage for phishing indicators.
        
        URL: {url}
        HTML CONTENT (truncated):
        {html_content[:2500]}
        
        DETECT THESE PATTERNS:
        1. Urgency tactics (countdown timers, "limited time", "expires soon")
        2. Reward promises ("you won", "congratulations", "free gift")
        3. Fake branding (mentions of Apple, Google, Amazon, Microsoft, banks)
        4. Data harvesting forms (credit card, SSN, password fields)
        5. Social engineering (fake surveys, "verify your account")
        6. Suspicious redirects or URL patterns
        
        RESPONSE FORMAT (JSON only):
        {{
            "suspicion_score": 0-100,
            "detected_patterns": ["pattern1", "pattern2"],
            "brand_impersonation": "CompanyName or null",
            "has_data_harvesting_form": true/false,
            "is_final_payload_page": true/false,
            "recommendation": "continue_exploration" or "stop_reached_payload"
        }}
        """
        result = self._call_ollama_json(
            {"model": self.model, "prompt": prompt, "stream": False}, timeout=30
        )
        if isinstance(result, dict) and "suspicion_score" in result:
            return result
        return {"suspicion_score": 50, "detected_patterns": [], "recommendation": "continue_exploration"}

    def extract_target_brand(self, report_data: dict) -> str:
        """
        Analyzes the full report to identify the targeted brand/company.
        Returns a sanitized string (e.g. 'Netflix', 'VinciAutoroutes', 'Unknown').
        """
        journey_summary = " ".join([s['description'] for s in report_data.get('interaction_journey', [])])
        html_snippets = " ".join([s.get('html', '')[:500] for s in report_data.get('interaction_journey', [])[:3]]) # Check first few pages
        
        chain = report_data.get('redirect_chain')
        final_url = chain[-1].get('url') if chain else report_data.get('target_url', 'Unknown')
        
        prompt = f"""
        Analyze this phishing scan data to identify the BRAND or COMPANY being impersonated.
        
        Target URL: {report_data.get('target_url')}
        Final URL: {final_url}
        User Journey Log: {journey_summary[:1000]}
        HTML Snippets: {html_snippets[:2000]}
        
        TASK:
        Identify the single brand name targeted (e.g. "Netflix", "Microsoft", "Vinci Autoroutes", "La Poste").
        If generic or unknown, return "Unknown".
        
        RESPONSE FORMAT:
        Return ONLY the brand name as a string. No markdown. No punctuation.
        Example: VinciAutoroutes
        """
        raw = self._call_ollama({"model": self.model, "prompt": prompt, "stream": False}, timeout=20, retries=2)
        if not raw:
            return "Unknown"
        import re
        brand = re.sub(r'[^a-zA-Z0-9\s\-]', '', raw).strip().split('\n')[0].strip()
        brand = re.sub(r'\s+', '', brand)  # remove internal spaces for folder naming
        return brand if 2 <= len(brand) < 40 else "Unknown"

    def solve_captcha(self, html_snippet: str, page_url: str, base64_image: str = None) -> dict:
        """
        AI-powered CAPTCHA analysis and solving.
        Analyzes page HTML and an optional screenshot to:
        1. Classify the CAPTCHA type (math, text, image, slider, recaptcha, hcaptcha, unknown)
        2. Extract the challenge details (especially if the math/text is inside an image)
        3. Attempt to provide the answer
        
        Returns: {"type": str, "answer": str|None, "confidence": int, 
                  "instructions": str, "input_selector": str, "submit_selector": str}
        """
        prompt = f"""You are a CAPTCHA solving expert analyzing a webpage that contains a CAPTCHA challenge.

PAGE URL: {page_url}
HTML CONTENT:
{html_snippet[:4000]}

TASK:
1. Identify the CAPTCHA type from these categories:
   - "math": Simple arithmetic (e.g., "3 + 5 = ?")
   - "text": Text-based question (e.g., "What color is the sky?")
   - "slider": Drag slider to complete puzzle
   - "recaptcha": Google reCAPTCHA (checkbox or image grid)
   - "hcaptcha": hCaptcha challenge
   - "image": Select images matching a description
   - "unknown": Cannot identify

2. If the CAPTCHA is solvable (math, text, or letters in an image), provide the answer. IF A SCREENSHOT IS PROVIDED, LOOK AT IT TO EXTRACT THE MATH PROBLEM OR TEXT.

3. Identify the CSS selector for:
   - The input field where the answer should be typed
   - The submit button to click after answering

4. Rate your confidence (0-100) in your answer.

5. Provide brief human-readable instructions for manual solving if needed.

RESPONSE FORMAT (JSON only, no markdown):
{{
    "type": "math",
    "challenge_description": "What is 8 + 3?",
    "answer": "11",
    "confidence": 95,
    "input_selector": "#result",
    "submit_selector": "button[type=submit]",
    "instructions": "Enter the result of 8 + 3 in the input field and click submit"
}}

If you cannot solve it, set answer to null and confidence to 0."""

        model_to_use = "llava" if base64_image else self.model
        payload: dict = {"model": model_to_use, "prompt": prompt, "stream": False}
        if base64_image:
            payload["images"] = [base64_image]
        logger.info(f"🧠 AI CAPTCHA Solver: analyzing with {model_to_use} (vision={'yes' if base64_image else 'no'})...")
        parsed = self._call_ollama_json(payload, timeout=60)
        if not isinstance(parsed, dict):
            parsed = {}
        return {
            "type": parsed.get("type", "unknown"),
            "challenge_description": parsed.get("challenge_description", ""),
            "answer": parsed.get("answer"),
            "confidence": int(parsed.get("confidence", 0)),
            "input_selector": parsed.get("input_selector", ""),
            "submit_selector": parsed.get("submit_selector", ""),
            "instructions": parsed.get("instructions", "Résoudre le CAPTCHA manuellement.")
        }

    def solve_captcha_visual(self, base64_image: str, challenge_instruction: str, grid_size: str = "3x3") -> List[int]:
        """
        Uses a local Vision-Language Model (like llava) to solve an Image Grid CAPTCHA.
        Returns a list of 1-indexed tile numbers to click.
        E.g. [1, 4, 5] means click top-left, middle-left, and center tiles in a 3x3 grid.
        """
        prompt = f"""
        You are a sophisticated AI CAPTCHA solver. 
        You are looking at an image grid CAPTCHA of size {grid_size}.
        The tiles are numbered from 1 to 9 (for a 3x3 grid) reading left-to-right, top-to-bottom.
        1 2 3
        4 5 6
        7 8 9
        
        CHALLENGE INSTRUCTION: {challenge_instruction}
        
        TASK:
        Examine the image carefully. Identify which tiles contain the requested object.
        
        RESPONSE FORMAT:
        Return ONLY a JSON array of the tile numbers to click. Do not include any other text or explanation.
        Example: [2, 5, 8]
        If no tiles match, return: []
        """
        
        vision_model = "llava"
        logger.info(f"👁️ Vision AI: solving CAPTCHA grid with {vision_model}...")
        payload = {"model": vision_model, "prompt": prompt, "images": [base64_image], "stream": False}
        result = self._call_ollama_json(payload, timeout=60)
        if isinstance(result, list) and all(isinstance(t, int) for t in result):
            # Validate tile indices are within grid bounds
            max_tile = int(grid_size.split("x")[0]) ** 2 if "x" in grid_size else 9
            valid = [t for t in result if 1 <= t <= max_tile]
            logger.info(f"👁️ Vision AI suggests tiles: {valid}")
            return valid
        logger.warning(f"👁️ Vision AI returned unexpected response: {result}")
        return []

    # ──────────────────────────────────────────────────────────────
    # Network Artifacts / IOC Analysis
    # ──────────────────────────────────────────────────────────────
    def analyze_network_artifacts(self, network_log: list, redirect_chain: list) -> str:
        """
        Analyse les artefacts réseau (POST submissions, JS chargés, redirections)
        pour extraire les IOCs et identifier le schéma d'exfiltration.
        """
        if not network_log and not redirect_chain:
            return ""

        post_entries = [e for e in network_log if e.get("type") == "post_submission"]
        js_entries = [e for e in network_log if e.get("type") == "js"]

        post_summary = []
        for e in post_entries[:10]:
            content = ""
            raw = e.get("content", b"")
            if isinstance(raw, (bytes, bytearray)):
                content = raw.decode("utf-8", errors="replace")[:500]
            elif isinstance(raw, str):
                content = raw[:500]
            post_summary.append({"url": e.get("url", ""), "data": content})

        redirect_urls = [h.get("url", "") for h in redirect_chain]
        js_urls = [e.get("url", "") for e in js_entries[:20]]

        prompt = f"""Tu es un analyste en threat intelligence. Analyse ces artefacts réseau d'un site de phishing.

REDIRECTIONS ({len(redirect_chain)}):
{json.dumps(redirect_urls[:20], indent=2)}

SOUMISSIONS POST ({len(post_summary)} détectée(s)):
{json.dumps(post_summary, indent=2)}

SCRIPTS JS CHARGÉS ({len(js_urls)}):
{json.dumps(js_urls[:20], indent=2)}

TÂCHE:
1. Identifie les domaines/IPs de collecte (endpoints de réception des données volées).
2. Identifie les patterns d'URL suspects (trackers, redirecteurs, C2 potentiels).
3. Extrait les IOCs (Indicators of Compromise): domaines, IPs, URLs suspectes.
4. Map les techniques MITRE ATT&CK pertinentes (ex: T1566.002 Spearphishing Link, T1056 Input Capture).
5. Évalue si l'infrastructure est partagée (hosting bulletproof, CDN d'abus connus).

Réponds en français. Format: bullet points structurés.
"""
        result = self._call_ollama({"model": self.model, "prompt": prompt, "stream": False}, timeout=90)
        return result or ""

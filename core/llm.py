import os
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

    def analyze_javascript(self, js_code: str, filename: str) -> str:
        """Analyzes a JavaScript snippet for malicious intent."""
        prompt = f"""
        You are a Malware Analyst. Analyze this suspicious JavaScript file extracted from a phishing site.
        
        FILENAME: {filename}
        CODE SNIPPET (First 2000 chars):
        {js_code[:2000]}
        
        TASK:
        1. Identify the purpose (e.g., obfuscation, redirection, fingerprinting, payload delivery).
        2. Highlight any specific dangerous functions or logic.
        3. Explain exactly what this script tries to do to the victim.
        
        Keep it concise (3-4 sentences).
        """
        try:
            payload = {"model": self.model, "prompt": prompt, "stream": False}
            response = requests.post(self.api_url, json=payload, timeout=40)
            return response.json().get("response", "Analysis failed.").strip()
        except Exception as e:
            logger.error(f"JS Analysis failed: {e}")
            return "Analysis unavailable."

    def analyze_journey_step(self, step_data: dict) -> str:
        """Analyzes a specific step in the user journey."""
        prompt = f"""
        Analyze this Phishing Interaction Step.
        
        Step: {step_data.get('step')}
        Action Taken: {step_data.get('description')}
        Current URL: {step_data.get('url')}
        Page HTML Snippet:
        {step_data.get('html', '')[:1000]}...
        
        Question:
        What is the attacker trying to do here? (e.g. build trust, simulate loading, extract data, redirect).
        Be very brief (1-2 sentences).
        """
        try:
            payload = {"model": self.model, "prompt": prompt, "stream": False}
            response = requests.post(self.api_url, json=payload, timeout=30)
            return response.json().get("response", "").strip()
        except: return "Analysis skipped."

    def analyze_report(self, report_data: dict) -> str:
        """Sends the report JSON to Ollama for a security summary."""
        
        journey_desc = "\n".join([f"- {s['step']}: {s['description']} (URL: {s.get('url','?')})" for s in report_data.get('interaction_journey', [])])
        
        chain = report_data.get('redirect_chain', [])
        final_url = chain[-1].get('url') if chain else report_data.get('target_url', 'Unknown')
        
        prompt = f"""
        You are a Cybersecurity Expert analyzing a Phishing Scan.
        
        DATA:
        Target: {report_data.get('target_url')}
        Redirect Chain: {len(chain)} hops.
        Final URL: {final_url}
        Inputs Found: {len(report_data.get('inputs', []))} (Types: {[i.get('type') for i in report_data.get('inputs', [])[:5]]})
        
        INTERACTIVE JOURNEY (Bot clicked buttons):
        {journey_desc}
        
        ARTIFACTS:
        {json.dumps(report_data.get('files_extracted', []), indent=2)[:1500]}
        
        TASK:
        Write a detailed Forensic Report.
        1. **Evidence-Based Analysis**: Cite specific steps from the 'Interactive Journey' to prove malicious intent (e.g., "After clicking 'Start', the user is redirected to...").
        2. **Technique Explanation**: Explain *why* the obfuscation or the survey flow is effective/malicious.
        3. **Severity**: Assessment.
        
        Format as Markdown. Use bolding for key findings.
        """

        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            logger.info(f"Sending analysis request to Ollama (Model: {self.model})...")
            response = requests.post(self.api_url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json().get("response", "No response from LLM.")
        except Exception as e:
            logger.error(f"Ollama analysis failed: {e}")
            return f"**Analysis Unavailable**: Could not connect to local Ollama instance ({e}). Please ensure 'ollama serve' is running."

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
        try:
            payload = {"model": self.model, "prompt": prompt, "stream": False, "format": "json"}
            response = requests.post(self.api_url, json=payload, timeout=15)
            result = response.json().get("response", "{}")
            if isinstance(result, str):
                return json.loads(result)
            return result
        except Exception as e:
            logger.error(f"LLM Action Decision failed: {e}")
            return {}

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
        try:
            payload = {"model": self.model, "prompt": prompt, "stream": False, "format": "json"}
            response = requests.post(self.api_url, json=payload, timeout=20)
            result = response.json().get("response", "[]")
            if isinstance(result, str):
                return json.loads(result)
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"LLM Element Analysis failed: {e}")
            return elements  # Return original if AI fails

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
        try:
            payload = {"model": self.model, "prompt": prompt, "stream": False, "format": "json"}
            response = requests.post(self.api_url, json=payload, timeout=15)
            result = response.json().get("response", "{}")
            if isinstance(result, str):
                return json.loads(result)
            return result
        except Exception as e:
            logger.error(f"LLM Pattern Detection failed: {e}")
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
        try:
            payload = {"model": self.model, "prompt": prompt, "stream": False}
            response = requests.post(self.api_url, json=payload, timeout=20)
            brand = response.json().get("response", "Unknown").strip()
            # Sanitize
            import re
            brand = re.sub(r'[^a-zA-Z0-9]', '', brand)
            return brand if len(brand) < 30 else "Unknown"
        except Exception as e:
            logger.warning(f"Brand extraction failed: {e}")
            return "Unknown"

    def solve_captcha(self, html_snippet: str, page_url: str) -> dict:
        """
        AI-powered CAPTCHA analysis and solving.
        Analyzes page HTML to:
        1. Classify the CAPTCHA type (math, text, image, slider, recaptcha, hcaptcha, unknown)
        2. Extract the challenge details
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

2. If the CAPTCHA is solvable (math or text), provide the answer.

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

        try:
            payload = {"model": self.model, "prompt": prompt, "stream": False, "format": "json"}
            logger.info("🧠 AI CAPTCHA Solver: Analyzing page...")
            response = requests.post(self.api_url, json=payload, timeout=30)
            result = response.json().get("response", "{}")
            if isinstance(result, str):
                parsed = json.loads(result)
            else:
                parsed = result
            
            # Ensure required fields exist with defaults
            return {
                "type": parsed.get("type", "unknown"),
                "challenge_description": parsed.get("challenge_description", ""),
                "answer": parsed.get("answer"),
                "confidence": parsed.get("confidence", 0),
                "input_selector": parsed.get("input_selector", ""),
                "submit_selector": parsed.get("submit_selector", ""),
                "instructions": parsed.get("instructions", "Solve the CAPTCHA manually")
            }
        except Exception as e:
            logger.error(f"🧠 AI CAPTCHA analysis failed: {e}")
            return {
                "type": "unknown",
                "challenge_description": "",
                "answer": None,
                "confidence": 0,
                "input_selector": "",
                "submit_selector": "",
                "instructions": "AI analysis failed. Please solve the CAPTCHA manually."
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
        
        try:
            # Note: We assume the user has a vision model installed, e.g. 'llava' or 'llama3.2-vision'
            # We hardcode to 'llava' for testing, or use self.model if we assume the main model is multimodal.
            # Local users usually pull 'llava' specifically for vision.
            vision_model = "llava" 
            
            payload = {
                "model": vision_model,
                "prompt": prompt,
                "images": [base64_image],
                "stream": False,
                "format": "json"
            }
            logger.info(f"👁️ Vision AI: Analyzing CAPTCHA image with {vision_model}...")
            response = requests.post(self.api_url, json=payload, timeout=60)
            
            if response.status_code == 404 or "model" in response.text.lower():
                logger.warning(f"👁️ Vision model '{vision_model}' not found in Ollama. Please run 'ollama pull {vision_model}'.")
                return []
                
            result = response.json().get("response", "[]")
            
            if isinstance(result, str):
                tiles = json.loads(result)
            else:
                tiles = result
                
            if isinstance(tiles, list) and all(isinstance(t, int) for t in tiles):
                logger.info(f"👁️ Vision AI suggests clicking tiles: {tiles}")
                return tiles
            else:
                logger.warning(f"👁️ Vision AI returned malformed response: {result}")
                return []
                
        except Exception as e:
            logger.error(f"👁️ Vision AI analysis failed: {e}")
            return []

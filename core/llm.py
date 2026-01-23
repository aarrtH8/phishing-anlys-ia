import requests
import logging
import json

logger = logging.getLogger(__name__)

class LLMAnalyzer:
    def __init__(self, model: str = "mistral"):
        self.model = model
        self.api_url = "http://localhost:11434/api/generate"

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
        final_url = chain[-1].get('url') if chain else "Unknown"
        
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
        
        prompt = f"""
        Analyze this phishing scan data to identify the BRAND or COMPANY being impersonated.
        
        Target URL: {report_data.get('target_url')}
        Redirect Chain (Last): {report_data.get('redirect_chain', [{'url': 'none'}])[-1].get('url')}
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

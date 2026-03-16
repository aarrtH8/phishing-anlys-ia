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
        """Deep forensic analysis of a single interaction step."""
        import re as _re

        html = step_data.get('html', '') or ''

        # ── Extract form fields ──────────────────────────────────────────
        form_fields = []
        for m in _re.finditer(r'<input[^>]+>', html, _re.IGNORECASE):
            tag = m.group(0)
            name  = (_re.search(r'name=["\']([^"\']+)["\']', tag) or _re.search(r'name=(\S+)', tag))
            ftype = (_re.search(r'type=["\']([^"\']+)["\']', tag) or _re.search(r'type=(\S+)', tag))
            fid   = _re.search(r'id=["\']([^"\']+)["\']', tag)
            form_fields.append({
                "name":  name.group(1)  if name  else "?",
                "type":  ftype.group(1) if ftype else "text",
                "id":    fid.group(1)   if fid   else "",
            })

        # ── Extract script snippets (first 300 chars each, max 4) ────────
        scripts_inline = []
        for m in _re.finditer(r'<script[^>]*>(.*?)</script>', html, _re.DOTALL | _re.IGNORECASE):
            s = m.group(1).strip()
            if len(s) > 30:
                scripts_inline.append(s[:300])
            if len(scripts_inline) >= 4:
                break

        # ── External script sources ──────────────────────────────────────
        script_srcs = _re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html, _re.IGNORECASE)

        # ── Hidden fields (common exfil technique) ───────────────────────
        hidden_fields = [f for f in form_fields if f.get("type") == "hidden"]

        # ── Visible text (clean) ─────────────────────────────────────────
        visible_text = _re.sub(r'<[^>]+>', ' ', html)
        visible_text = _re.sub(r'\s+', ' ', visible_text).strip()[:600]

        # ── Scripts captured by browser instrumentation ──────────────────
        browser_scripts = step_data.get('scripts', [])[:10]

        prompt = f"""Tu es un analyste CTI (Cyber Threat Intelligence) de niveau expert.
Effectue une analyse forensique technique et précise de cette étape d'un parcours de phishing.

━━━ CONTEXTE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Étape   : {step_data.get('step')}
Action  : {step_data.get('description')}
URL     : {step_data.get('url')}
━━━ FORMULAIRE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Champs trouvés ({len(form_fields)}) : {json.dumps(form_fields[:10])}
Champs cachés  : {json.dumps(hidden_fields)}
━━━ JAVASCRIPT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Scripts externes : {json.dumps(script_srcs[:8])}
Scripts inline   : {json.dumps(scripts_inline)}
Scripts navigateur: {json.dumps(browser_scripts)}
━━━ TEXTE VISIBLE ━━━━━━━━━━━━━━━━━━━━━━━━
{visible_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Produis une analyse technique structurée en Markdown. Sois précis et concis. Format OBLIGATOIRE :

**🎯 Objectif de l'attaquant** : [phrase courte — ex: collecte d'adresse postale, simulation confiance, exfil CB]

**🔍 Technique d'ingénierie sociale** : [nom précis — ex: Fake Package Tracking, Urgency Pressure, Brand Impersonation La Poste]

**📋 Champs de collecte** : [liste des champs et ce qu'ils récoltent — ex: `nom`, `adresse`, `code_postal` → profilage géographique]

**💻 Comportement JS** : [ce que font les scripts — fonctions détectées, tracking pixels, obfuscation base64/eval, appels externes]

**🔗 Endpoint de réception** : [URL POST cible si détectable, sinon "non visible à cette étape"]

**⚠️ Indicateurs de compromission (IOC)** : [domaines tiers, pixels tracking, URLs suspectes dans le HTML]

**📊 Sévérité de cette étape** : [RECONNAISSANCE / INGÉNIERIE SOCIALE / COLLECTE DONNÉES / EXFILTRATION / PAIEMENT]

Réponds uniquement en français. Pas d'introduction générique.
"""
        result = self._call_ollama(
            {"model": self.model, "prompt": prompt, "stream": False},
            timeout=60, retries=2
        )
        return result or "_Analyse de l'étape indisponible (timeout LLM)._"

    def analyze_report(self, report_data: dict) -> str:
        """Deep forensic LLM report — CTI-grade, structured, technical."""

        chain = report_data.get('redirect_chain', [])
        final_url = chain[-1].get('url', '?') if chain else report_data.get('target_url', '?')

        # Build redirect chain text
        chain_text = "\n".join(
            f"  {i+1}. [{h.get('status','?')}] {h.get('url','?')}"
            for i, h in enumerate(chain)
        ) or "  (aucune redirection)"

        # POST submissions
        post_submissions = [e for e in report_data.get("network_log", []) if e.get("type") == "post_submission"]
        post_text = ""
        for ps in post_submissions[:6]:
            raw = ps.get("content", b"")
            data_str = (raw.decode("utf-8", errors="replace") if isinstance(raw, (bytes, bytearray)) else str(raw))[:400]
            post_text += f"  POST → {ps.get('url', '?')}\n  Payload: {data_str}\n"
        if not post_text:
            post_text = "  Aucune soumission POST capturée"

        # Input fields
        inputs = report_data.get('inputs', [])
        inputs_text = ", ".join(
            f"`{i.get('name') or i.get('id') or '?'}` ({i.get('type','text')})"
            for i in inputs[:12]
        ) or "Aucun"

        # Journey summary
        journey = report_data.get('interaction_journey', [])
        journey_text = "\n".join(
            f"  [{s.get('step')}] {s.get('description','?')} | URL: {s.get('url','?')} | "
            f"Suspicion: {s.get('ai_patterns',{}).get('suspicion_score','?')}%"
            for s in journey
        ) or "  (aucune interaction)"

        # Visual analysis
        visual = report_data.get('visual_analysis', {}) or {}
        visual_text = ""
        if visual:
            visual_text = (
                f"  Marque visuelle détectée : {visual.get('brand_detected','?')}\n"
                f"  Logos identifiés        : {visual.get('logos_found',[])}\n"
                f"  OCR extrait             : {str(visual.get('ocr_text',''))[:250]}\n"
            )

        # Collected scripts (from journey steps)
        all_scripts: list = []
        for s in journey:
            for sc in (s.get('scripts') or []):
                if sc not in all_scripts:
                    all_scripts.append(sc)
        scripts_text = "\n".join(f"  - {sc[:120]}" for sc in all_scripts[:15]) or "  Aucun"

        # Files extracted
        files_text = ""
        for f in report_data.get('files_extracted', [])[:6]:
            ai = f.get('analysis', {})
            files_text += (
                f"  [{f.get('type','?').upper()}] {f.get('url','?')}\n"
                f"    Obfuscation: {ai.get('obfuscation_detected', False)} | "
                f"Entropy: {ai.get('entropy_score',0):.2f}\n"
                f"    AI: {ai.get('ai_explanation','')[:150]}\n"
            )
        files_text = files_text or "  Aucun artefact"

        prompt = f"""Tu es un analyste CTI senior (OSCP/CEH). Tu rédiges un rapport forensique de qualité professionnelle.
Tes analyses sont citées dans des procédures judiciaires et des rapports d'incident d'entreprise.
Sois précis, factuel, technique. NE PAS inventer de données absentes. NE PAS sur-conclure.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DONNÉES BRUTES DU SCAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cible initiale    : {report_data.get('target_url')}
URL finale        : {final_url}
Région simulée    : {report_data.get('region','?')}

CHAÎNE DE REDIRECTIONS ({len(chain)} saut(s)):
{chain_text}

CHAMPS DE SAISIE DÉTECTÉS ({len(inputs)}):
{inputs_text}

SOUMISSIONS POST CAPTURÉES:
{post_text}

PARCOURS VICTIME SIMULÉ ({len(journey)} étapes):
{journey_text}

ANALYSE VISUELLE:
{visual_text or "  Non disponible"}

SCRIPTS DÉTECTÉS:
{scripts_text}

ARTEFACTS JS/HTML:
{files_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RÈGLES :
- Si c'est un site légitime connu → verdict SITE LÉGITIME, arrêt immédiat sans inventer d'attaque.
- Cite uniquement les preuves présentes dans les données ci-dessus.
- Utilise des termes techniques précis (typosquatting, credential harvesting, redirect chain, etc.)

Rédige le rapport forensique complet en Markdown, en français, avec ces sections EXACTES :

## 🏛️ Verdict
**[SITE LÉGITIME | PHISHING PROBABLE | PHISHING CONFIRMÉ]**
> Justification en 1-2 phrases factuelles.

## 📋 Résumé Exécutif
[2-3 phrases : nature de la campagne, marque usurpée, objectif final de l'attaquant]

## 🔬 Analyse Technique de la Chaîne d'Attaque
[Décris la mécanique complète : infrastructure → leurre → collecte → exfiltration. Cite les URLs exactes.]

## 🧬 Techniques d'Attaque Identifiées
| # | Technique | Description Technique | Preuve |
|---|-----------|----------------------|--------|
[Remplis ce tableau. Ex: Fake Package Tracking, Urgency Pressure, Multi-Step Credential Harvest, DOM Manipulation, Pixel Tracking]

## 🗺️ Mapping MITRE ATT&CK for Enterprise
| ID | Tactic | Technique | Justification |
|----|--------|-----------|---------------|
[Ex: T1566.002, T1204.001, T1056.003, T1071.001, T1036.005 — uniquement les IDs pertinents]

## 🎯 Indicateurs de Compromission (IOCs)
| Type | Valeur | Contexte |
|------|--------|---------|
[Domaines, IPs, URLs, hashes, patterns POST extraits des données. Type = DOMAIN/IP/URL/POST-ENDPOINT/TRACKING-PIXEL]

## 🛠️ Infrastructure & Hébergement
[Hébergeur, CDN détecté, géolocalisation probable, anomalies DNS/SSL, plateformes tierces utilisées (Google Storage, Cloudflare, etc.)]

## ⚖️ Évaluation de la Sévérité
**Sévérité globale** : [CRITIQUE | ÉLEVÉE | MOYENNE | FAIBLE | NON APPLICABLE]
**Impact potentiel victime** : [Vol d'identité / Vol financier / Credential stuffing / Aucun]
**Sophistication de l'attaque** : [1-10] — [justification courte]

## 💡 Recommandations
[Actions concrètes : blocage IOC, signalement plateformes, protection utilisateurs]
"""
        logger.info(f"[LLM] Envoi analyse forensique complète → Ollama ({self.model})…")
        result = self._call_ollama(
            {"model": self.model, "prompt": prompt, "stream": False},
            timeout=180
        )
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
        
        prompt = f"""Tu es une IA de détection de phishing. Analyse ces éléments interactifs d'une page web.
ATTENTION: Beaucoup de sites sont légitimes. Ne pas sur-scorer des boutons normaux.

URL: {url}
ÉLÉMENTS:
{elements_summary}

Attribue un "phishing_score" de 0-100 à chaque élément:
- 85-100: CTA phishing clairement malveillant ("Réclamez votre prix", "Vérifiez votre compte bancaire" sur site suspect)
- 60-84: Probablement phishing (sondage avec récompense, urgence artificielle)
- 30-59: Ambigu (bouton générique sur page suspecte)
- 0-29: Normal — navigation, connexion, inscription, fermeture, termes sur site légitime

RÈGLE CLEF: Sur un domaine légitime connu, TOUS les éléments obtiennent 0-20.
Un bouton "Se connecter" ou "S'abonner" sur un vrai site = score 5-15, JAMAIS 50+.

FORMAT (JSON array uniquement):
[
    {{"text": "Réclamez votre cadeau", "phishing_score": 92, "ai_reason": "Promesse de récompense classique phishing"}},
    {{"text": "Connexion", "phishing_score": 8, "ai_reason": "Bouton de connexion standard sur site légitime"}}
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
        prompt = f"""Tu es un expert en cybersécurité chargé d'analyser une page web.
Tu dois distinguer PRÉCISÉMENT les vrais sites de phishing des sites légitimes.

URL ANALYSÉE: {url}
CONTENU HTML (tronqué):
{html_content[:2500]}

RÈGLES IMPORTANTES ANTI-FAUX-POSITIFS:
- Les sites officiels connus (anthropic.com, google.com, microsoft.com, github.com, etc.) ont un score de 0-5.
- Un simple formulaire de connexion sur un domaine légitime N'EST PAS du phishing.
- Des boutons "Continuer", "S'abonner", "Se connecter" sur un site légitime ont un score de 0-20.
- Le phishing RÉEL se reconnaît à: domaine suspect + promesses de gains + urgence artificielle + collecte CB/mot de passe sur un faux site.
- Un site de documentation, blog, ou SaaS légitime doit avoir suspicion_score < 15.

VRAIS INDICATEURS DE PHISHING (score élevé uniquement si plusieurs présents):
1. Promesses de gains improbables ("vous avez gagné", "félicitations", "cadeau gratuit")
2. Urgence artificielle avec countdown + menace de perte
3. Collecte de données sensibles (CB, OTP, mot de passe) sur un domaine suspect/inconnu
4. Imitation visuelle d'une marque connue sur un domaine différent
5. Faux sondages avec récompense au bout
6. Domaine ressemblant à une marque (typosquatting)

FORMAT DE RÉPONSE (JSON uniquement):
{{
    "suspicion_score": 0-100,
    "detected_patterns": ["pattern1", "pattern2"],
    "brand_impersonation": "NomMarque ou null",
    "has_data_harvesting_form": true/false,
    "is_final_payload_page": true/false,
    "recommendation": "continue_exploration" ou "stop_reached_payload",
    "is_legitimate_site": true/false
}}
"""
        result = self._call_ollama_json(
            {"model": self.model, "prompt": prompt, "stream": False}, timeout=30
        )
        if isinstance(result, dict) and "suspicion_score" in result:
            # If the LLM marks it as a legitimate site, cap the score at 10
            if result.get("is_legitimate_site"):
                result["suspicion_score"] = min(result["suspicion_score"], 10)
                result["recommendation"] = "continue_exploration"
            return result
        return {"suspicion_score": 10, "detected_patterns": [], "recommendation": "continue_exploration"}

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

import asyncio
import argparse
import json
import logging
import os
import traceback
from datetime import datetime
from urllib.parse import urlparse

from core.browser import BrowserManager
from core.llm import LLMAnalyzer
from core.threat_intel import ThreatIntelligence, compute_risk_score
from analysis.java import JavaForensics
from analysis.javascript import JSAnalysis
from analysis.visual import VisualAnalysis

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PhishHunter")


def validate_url(url: str) -> str:
    """Validate and normalize the target URL."""
    url = url.strip()
    if not url:
        raise ValueError("URL cannot be empty.")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    if not parsed.netloc:
        raise ValueError(f"Invalid URL (no hostname): {url}")
    return url


async def analyze_phishing_url_region(url: str, headless: bool, region_code: str, output_dir: str, model: str = "mistral"):
    # Map regions to loc/tz
    REGIONS = {
        "US": {"locale": "en-US", "timezone": "America/New_York"},
        "FR": {"locale": "fr-FR", "timezone": "Europe/Paris"},
        "DE": {"locale": "de-DE", "timezone": "Europe/Berlin"},
        "JP": {"locale": "ja-JP", "timezone": "Asia/Tokyo"}
    }
    config = REGIONS.get(region_code, REGIONS["US"])

    logger.info(f"Starting analysis for: {url} (Region: {region_code})")

    browser = BrowserManager(headless=headless, region=region_code)
    java_analyzer = JavaForensics()
    js_analyzer = JSAnalysis()
    visual_analyzer = VisualAnalysis()
    llm = LLMAnalyzer(model=model)

    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "target_url": url,
        "region": region_code,
        "redirect_chain": [],
        "files_extracted": [],
        "visual_analysis": {},
        "obfuscation_flags": [],
        "links": [],
        "inputs": [],
        "interaction_journey": [],
    }

    try:
        await browser.start(locale=config["locale"], timezone_id=config["timezone"])
        result = await browser.analyze_url(url)

        raw_journey = result.get("interaction_journey", [])
        logger.info(f"Browser returned {len(raw_journey)} interaction steps.")

        for step in raw_journey:
            step_filename = os.path.join(output_dir, f"screenshot_{region_code}_{step['step']}.png")
            with open(step_filename, "wb") as f:
                f.write(step['screenshot'])

            html_filename = os.path.join(output_dir, f"html_{region_code}_{step['step']}.html")
            with open(html_filename, "w", encoding="utf-8", errors="ignore") as f:
                f.write(step.get('html', ''))

            report["interaction_journey"].append({
                "step": step['step'],
                "description": step['description'],
                "screenshot_path": step_filename,
                "html_path": html_filename,
                "url": step.get('url', 'unknown'),
                "ai_patterns": step.get('ai_patterns', {}),
            })

        logger.info(f"Captured {len(report['interaction_journey'])} interaction steps.")

        report["redirect_chain"] = result["redirect_chain"]
        report["links"] = result.get("links", [])
        report["inputs"] = result.get("inputs", [])
        # Keep a sanitised copy of the network log in the report for risk scoring
        # (bytes content is stripped to avoid JSON serialization issues)
        report["network_log"] = [
            {k: (v.decode("utf-8", errors="replace")[:500] if isinstance(v, (bytes, bytearray)) else v)
             for k, v in entry.items() if k != "headers"}
            for entry in result.get("network_log", [])
        ]

        # Network Artifacts
        network_log = result["network_log"]
        for entry in network_log:
            file_type = entry["type"]
            content = entry["content"]
            url_part = entry["url"].split("/")[-1] or f"unknown_{hash(entry['url'])}"
            filename = "".join(c for c in url_part if c.isalnum() or c in "._-") or "file.bin"

            if file_type == "java":
                java_res = java_analyzer.analyze_jar(content, filename)
                report["files_extracted"].append({"type": "java", "url": entry["url"], "analysis": java_res})
                try:
                    dump_dir = os.path.join(output_dir, "dump")
                    os.makedirs(dump_dir, exist_ok=True)
                    rep_path = os.path.join(dump_dir, f"{filename}_report.md")
                    with open(rep_path, "w", encoding="utf-8") as f:
                        f.write(f"# Java Analysis: {filename}\n\n")
                        f.write(f"**Source**: `{entry['url']}`\n\n")
                        f.write(f"## Metadata\n```json\n{json.dumps(java_res, indent=2)}\n```\n")
                except Exception:
                    pass

            elif file_type == "js":
                dump_dir = os.path.join(output_dir, "dump")
                os.makedirs(dump_dir, exist_ok=True)
                js_path = os.path.join(dump_dir, f"{filename}.js")
                with open(js_path, "wb") as f:
                    f.write(content)

                js_res = js_analyzer.analyze_js(content, filename)
                try:
                    js_text = content.decode('utf-8', errors='ignore')
                    js_res["ai_explanation"] = llm.analyze_javascript(js_text, filename)
                except Exception as e:
                    js_res["ai_explanation"] = f"Error: {e}"

                report["files_extracted"].append({"type": "javascript", "url": entry["url"], "analysis": js_res})
                try:
                    rep_path = os.path.join(dump_dir, f"{filename}_report.md")
                    with open(rep_path, "w", encoding="utf-8") as f:
                        f.write(f"# JS Forensic Analysis: {filename}\n\n")
                        f.write(f"**Source**: `{entry['url']}`\n")
                        f.write(f"**Entropy**: {js_res.get('entropy_score', 0):.2f}\n")
                        f.write(f"**Obfuscated**: {js_res.get('obfuscation_detected')}\n\n")
                        f.write("## AI Explanation\n")
                        f.write(f"{js_res.get('ai_explanation', 'N/A')}\n\n")
                        if js_res.get('deobfuscated_preview'):
                            f.write("## Deobfuscated Preview\n```javascript\n")
                            f.write(js_res['deobfuscated_preview'][:2000] + "\n```\n")
                except Exception as e:
                    logger.warning(f"Failed to write JS report for {filename}: {e}")

        # Visual
        screenshot = result["screenshot"]
        with open(os.path.join(output_dir, f"screenshot_{region_code}.png"), "wb") as f:
            f.write(screenshot)
        visual_res = visual_analyzer.analyze_screenshot(screenshot)
        report["visual_analysis"] = visual_res

    except Exception as e:
        logger.error(f"Analysis failed for {region_code}: {e}")
        traceback.print_exc()
        report["error"] = str(e)
    finally:
        await browser.close()

    return report


def generate_final_report(consolidated_data, llm_summary, output_dir: str, model: str = "mistral"):
    scan_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    target    = consolidated_data["target_url"]
    risk      = consolidated_data.get("risk_score", {})
    ti        = consolidated_data.get("threat_intel", {})
    ref_region = consolidated_data["regions"][0] if consolidated_data.get("regions") else {}

    score = risk.get("score", 0)
    level = risk.get("level", "unknown")
    level_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(level, "⚪")

    # ── Header ───────────────────────────────────────────────────────────
    md  = "# 🕵️ PhishHunter — Rapport Forensique\n\n"
    md += f"> **Cible** : `{target}`  \n"
    md += f"> **Date** : {scan_time}  \n"
    md += f"> **Moteur** : PhishHunter v2 · Modèle LLM : `{model}`\n\n"
    md += "---\n\n"

    # ── Risk Score banner ─────────────────────────────────────────────────
    md += f"## {level_emoji} Score de Risque : {score}/100 — {level.upper()}\n\n"
    factors = risk.get("factors", [])
    if factors:
        md += "| Facteur de scoring | |\n|---|---|\n"
        for fac in factors:
            md += f"| {fac} | |\n"
    md += "\n"

    # ── Threat Intelligence ───────────────────────────────────────────────
    md += "## 🔎 Threat Intelligence\n\n"
    md += "| Indicateur | Valeur | Statut |\n"
    md += "|------------|--------|--------|\n"

    # VirusTotal
    vt = ti.get("virustotal", {})
    if vt and not vt.get("skipped"):
        if vt.get("error"):
            md += f"| VirusTotal | Erreur : {vt['error'][:60]} | ⚠️ |\n"
        else:
            vt_mal = vt.get("malicious", 0)
            vt_sus = vt.get("suspicious", 0)
            vt_tot = vt.get("total", 0)
            vt_status = "🔴" if vt_mal > 0 else ("🟡" if vt_sus > 0 else "🟢")
            md += f"| VirusTotal | {vt_mal} malicious / {vt_sus} suspicious / {vt_tot} engines | {vt_status} |\n"
            # Top detections
            for eng in vt.get("top_detections", [])[:5]:
                md += f"| &nbsp;&nbsp;↳ {eng.get('engine','?')} | {eng.get('result','?')} | 🔴 |\n"
    else:
        md += "| VirusTotal | Non configuré (VT_API_KEY manquante) | ⚪ |\n"

    # WHOIS
    whois = ti.get("whois", {})
    if whois and not whois.get("error"):
        age = whois.get("age_days")
        age_str = f"{age} jours" if age is not None else "inconnu"
        age_status = "🔴" if (age is not None and age < 30) else ("🟡" if (age is not None and age < 180) else "🟢")
        md += f"| Âge du domaine | {age_str} (créé le {whois.get('registration_date','?')[:10]}) | {age_status} |\n"
        md += f"| Registrar | {whois.get('registrar','inconnu')} | |\n"
        if whois.get("registrant_country"):
            md += f"| Pays registrant | {whois['registrant_country']} | |\n"

    # SSL
    ssl_d = ti.get("ssl", {})
    if ssl_d:
        ssl_ok = ssl_d.get("valid")
        ssl_status = "🟢" if ssl_ok else "🔴"
        ssl_str = "Valide" if ssl_ok else ("Expiré" if ssl_d.get("is_expired") else "Invalide/Absent")
        md += f"| SSL/TLS | {ssl_str} — Émetteur : {ssl_d.get('issuer','?')}"
        if ssl_d.get("days_left") is not None:
            md += f" ({ssl_d['days_left']}j restants)"
        if ssl_d.get("is_self_signed"):
            md += " ⚠️ AUTO-SIGNÉ"
        md += f" | {ssl_status} |\n"
        if ssl_d.get("subject_alt_names"):
            md += f"| &nbsp;&nbsp;↳ SANs | `{'`, `'.join(ssl_d['subject_alt_names'][:5])}` | |\n"

    # URLScan
    urlscan = ti.get("urlscan") or {}
    if urlscan.get("found") and not urlscan.get("skipped"):
        flags = urlscan.get("malicious_flags", 0)
        us_status = "🔴" if flags else "🟢"
        md += f"| URLScan.io | {flags} flag(s) malicieux / {urlscan.get('total_prior_scans',0)} scans historiques | {us_status} |\n"
        for scan in (urlscan.get("recent_scans") or [])[:2]:
            if scan.get("report_url"):
                md += f"| &nbsp;&nbsp;↳ Scan [{scan.get('scan_date','?')[:10]}] | [{scan['report_url'][:60]}]({scan['report_url']}) | |\n"
    elif urlscan.get("found") is False:
        md += "| URLScan.io | Aucun scan historique | ⚪ |\n"

    # IP / ASN
    ip_info = ti.get("ip_info") or {}
    if ip_info and not ip_info.get("error"):
        ip_flags = []
        if ip_info.get("is_proxy"):   ip_flags.append("⚠️ Proxy/VPN")
        if ip_info.get("is_hosting"): ip_flags.append("⚠️ Hébergement dédié")
        ip_status = "🔴" if ip_flags else "🟢"
        md += f"| IP | `{ip_info.get('ip','?')}` | {ip_status} |\n"
        md += f"| ISP / Hébergeur | {ip_info.get('isp','?')} | |\n"
        md += f"| ASN | `{ip_info.get('asn','?')}` — {ip_info.get('org','?')} | |\n"
        md += f"| Géolocalisation | {ip_info.get('country','?')} / {ip_info.get('city','?')} | |\n"
        if ip_flags:
            md += f"| Flags infrastructure | {' · '.join(ip_flags)} | 🔴 |\n"

    md += "\n"

    # ── LLM Forensic Analysis (main) ─────────────────────────────────────
    md += "## 🧠 Analyse Forensique IA\n\n"
    md += f"{llm_summary}\n\n"

    # ── Network IOC ───────────────────────────────────────────────────────
    network_ioc = consolidated_data.get("network_ioc_analysis", "")
    if network_ioc:
        md += "## 🕸️ Artefacts Réseau & IOCs Dynamiques\n\n"
        md += f"{network_ioc}\n\n"

    # ── Network log — POST submissions table ──────────────────────────────
    network_log = ref_region.get("network_log", [])
    post_subs   = [e for e in network_log if e.get("type") == "post_submission"]
    if post_subs:
        md += "## 📤 Soumissions POST Capturées\n\n"
        md += "| # | Endpoint | Payload (extrait) |\n"
        md += "|---|----------|-------------------|\n"
        for idx, ps in enumerate(post_subs[:10], 1):
            raw = ps.get("content", b"")
            payload = (raw.decode("utf-8", errors="replace") if isinstance(raw, (bytes, bytearray)) else str(raw))[:200]
            payload = payload.replace("|", "\\|").replace("\n", " ")
            url_short = (ps.get("url") or "?")[:80]
            md += f"| {idx} | `{url_short}` | `{payload}` |\n"
        md += "\n"

    # ── Network log — all requests (condensed) ────────────────────────────
    all_requests = [e for e in network_log if e.get("type") in ("request", "response")]
    if all_requests:
        md += "<details>\n<summary>📡 Journal réseau complet ({} requêtes)</summary>\n\n".format(len(all_requests))
        md += "| Méthode | URL | Status | Type |\n"
        md += "|---------|-----|--------|------|\n"
        for req in all_requests[:80]:
            method = req.get("method", "GET")
            req_url = (req.get("url") or "?")[:90]
            status = req.get("status", "")
            ctype  = (req.get("content_type") or "")[:30]
            md += f"| {method} | `{req_url}` | {status} | {ctype} |\n"
        md += "\n</details>\n\n"

    # ── Deep Agentic Journey ──────────────────────────────────────────────
    md += "## 🤖 Parcours Agentique — Simulation Victime\n\n"
    md += ("> L'engine a simulé le parcours complet d'une victime, étape par étape, "
           "en cliquant automatiquement sur les CTAs, remplissant les formulaires "
           "et capturant chaque écran + artefact JS.\n\n")

    llm_obj = LLMAnalyzer(model=model)
    steps = ref_region.get("interaction_journey", [])

    if steps:
        logger.info(f"Generating technical step analysis for {len(steps)} steps.")

        # Journey timeline table
        md += "### Chronologie du parcours\n\n"
        md += "| # | Étape | URL | Suspicion | Scripts chargés |\n"
        md += "|---|-------|-----|-----------|------------------|\n"
        for i, step in enumerate(steps):
            desc_s = step["description"][:55] + ("…" if len(step["description"]) > 55 else "")
            url_s  = (step.get("url") or "N/A")[:55] + ("…" if len(step.get("url","")) > 55 else "")
            pats   = step.get("ai_patterns") or {}
            sc     = pats.get("suspicion_score")
            score_s = f"**{sc}%**" if sc is not None else "—"
            n_scripts = len(step.get("scripts") or [])
            md += f"| {i+1} | {desc_s} | `{url_s}` | {score_s} | {n_scripts} |\n"
        md += "\n"

        # Detailed steps
        for i, step in enumerate(steps):
            desc = step["description"]
            url  = step.get("url", "?")

            if "PAIEMENT" in desc.upper() or "PAYMENT" in desc.upper():
                marker = "💳"
            elif "captcha" in desc.lower():
                marker = "🛡️"
            elif "Form Auto-Fill" in desc or "formulaire" in desc.lower():
                marker = "📝"
            elif i == 0:
                marker = "🏁"
            elif "CTA" in desc:
                marker = "⚡"
            else:
                marker = "➡️"

            md += f"### {marker} Étape {i+1} — {desc}\n\n"
            md += f"**URL** : `{url}`\n\n"

            # AI patterns
            pats = step.get("ai_patterns") or {}
            if pats.get("detected_patterns"):
                md += "**Patterns détectés** : "
                md += " · ".join(f"`{p}`" for p in pats["detected_patterns"]) + "\n\n"
            brand = pats.get("brand_impersonation")
            if brand and brand not in ("null", "None", None, ""):
                md += f"**Marque usurpée** : `{brand}`\n\n"
            if pats.get("has_data_harvesting_form"):
                md += "> ⚠️ **Formulaire de collecte de données personnelles détecté**\n\n"

            # JS scripts loaded at this step
            scripts = step.get("scripts") or []
            if scripts:
                md += "<details>\n<summary>🔧 Scripts JS chargés à cette étape ({})</summary>\n\n".format(len(scripts))
                md += "```\n"
                for sc in scripts[:15]:
                    md += sc[:150] + "\n"
                md += "```\n\n</details>\n\n"

            # LLM technical analysis
            logger.info(f"Step {i+1}/{len(steps)} — LLM forensic analysis…")
            try:
                insight = llm_obj.analyze_journey_step(step)
            except Exception as e:
                logger.error(f"LLM step analysis failed: {e}")
                insight = "_Analyse indisponible (timeout)._"

            md += f"{insight}\n\n"

            # Screenshot
            img_name = os.path.basename(step.get("screenshot_path", ""))
            if img_name:
                md += f"![Étape {i+1} — {desc[:40]}]({img_name})\n\n"

            md += "---\n\n"
    else:
        md += "_Aucune étape interactive capturée._\n\n"

    # ── Regional summary ──────────────────────────────────────────────────
    md += "## 🌍 Analyse par Région\n\n"
    for r in consolidated_data["regions"]:
        code = r["region"]
        chain = r.get("redirect_chain", [])
        md += f"### Région : {code}\n\n"

        if chain:
            md += "**Chaîne de redirections :**\n\n"
            md += "| # | URL | Status |\n"
            md += "|---|-----|--------|\n"
            for j, hop in enumerate(chain):
                status = hop.get("status", "?")
                s_icon = "🔴" if str(status).startswith(("4","5")) else ("🟡" if str(status).startswith("3") else "🟢")
                md += f"| {j+1} | `{hop['url'][:90]}` | {s_icon} {status} |\n"
            md += "\n"

        inputs = r.get("inputs", [])
        if inputs:
            md += f"**Champs de saisie détectés** ({len(inputs)}) :\n\n"
            md += "| Nom | Type | ID |\n|-----|------|----|\n"
            for inp in inputs[:15]:
                md += f"| `{inp.get('name','?')}` | `{inp.get('type','text')}` | `{inp.get('id','')}` |\n"
            md += "\n"
        else:
            md += "**Collecte de données** : Aucun formulaire visible.\n\n"

        md += f"![Screenshot {code}](screenshot_{code}.png)\n\n"
        md += "---\n\n"

    # ── Artifacts & Obfuscation ───────────────────────────────────────────
    seen_urls: set = set()
    artifacts = []
    for r in consolidated_data["regions"]:
        for f in r.get("files_extracted", []):
            if f["url"] not in seen_urls:
                seen_urls.add(f["url"])
                artifacts.append(f)

    if artifacts:
        md += "## 🧩 Artefacts & Obfuscation\n\n"
        for f in artifacts:
            analysis = f.get("analysis", {})
            obf = analysis.get("obfuscation_detected", False)
            entropy = analysis.get("entropy_score", 0)
            obf_icon = "🔴 **OBFUSQUÉ**" if obf else "🟢 Clair"
            md += f"### `{f['type'].upper()}` — `{f['url']}`\n\n"
            md += f"| Attribut | Valeur |\n|----------|--------|\n"
            md += f"| Obfuscation | {obf_icon} |\n"
            md += f"| Entropie Shannon | `{entropy:.2f}` |\n"
            if analysis.get("ai_explanation"):
                md += f"| Analyse IA | {analysis['ai_explanation'][:200]} |\n"
            md += "\n"
            if analysis.get("deobfuscated_preview"):
                md += "<details>\n<summary>📄 Aperçu déobfusqué</summary>\n\n```javascript\n"
                md += analysis["deobfuscated_preview"][:1000] + "\n…\n```\n\n</details>\n\n"
            md += "\n"

    # ── Footer ─────────────────────────────────────────────────────────────
    md += "---\n\n"
    md += f"*Rapport généré automatiquement par PhishHunter · {scan_time}*\n"

    report_path = os.path.join(output_dir, "FINAL_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)
    logger.info(f"Final report generated: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="PhishHunter — Phishing Analysis Engine")
    parser.add_argument("url", help="Target URL to analyze")
    parser.add_argument("--visible", action="store_true", help="Show the browser (headed mode)")
    parser.add_argument("--regions", default="FR", help="Comma-separated regions: US,FR,DE,JP")
    parser.add_argument("--model", default="mistral", help="Ollama model to use")
    parser.add_argument("--no-vt", action="store_true", help="Disable VirusTotal lookup")
    args = parser.parse_args()

    # Validate URL
    try:
        target_url = validate_url(args.url)
    except ValueError as e:
        logger.error(f"Invalid URL: {e}")
        raise SystemExit(1)

    regions = [r.strip().upper() for r in args.regions.split(",") if r.strip()]
    if not regions:
        logger.error("No valid regions specified.")
        raise SystemExit(1)

    # Output directory
    domain = urlparse(target_url).netloc.replace(":", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{domain}_{timestamp}"
    output_dir = os.path.join("output", run_id)
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

    # 1. Threat Intelligence (before browser analysis)
    logger.info("=== Running Threat Intelligence ===")
    vt_key = "" if args.no_vt else os.getenv("VT_API_KEY", "")
    if args.no_vt:
        logger.info("VirusTotal disabled (--no-vt flag).")
    elif not vt_key:
        logger.info("VirusTotal skipped (VT_API_KEY not set).")
    ti = ThreatIntelligence(vt_api_key=vt_key)
    threat_intel = ti.analyze(target_url)
    logger.info(f"Threat Intel: VT={threat_intel.get('virustotal', {})}, "
                f"Domain age={threat_intel.get('whois', {}).get('age_days')} days, "
                f"SSL valid={threat_intel.get('ssl', {}).get('valid')}")

    # 2. Browser Analysis per region
    results = []
    for region in regions:
        res = asyncio.run(analyze_phishing_url_region(target_url, not args.visible, region, output_dir, model=args.model))
        results.append(res)

    # 3. Risk Score
    primary_result = results[0] if results else {}
    risk_score = compute_risk_score(primary_result, threat_intel)
    logger.info(f"Risk Score: {risk_score['score']}/100 ({risk_score['level']})")

    # 4. Consolidate
    consolidated = {
        "target_url": target_url,
        "regions": results,
        "threat_intel": threat_intel,
        "risk_score": risk_score,
    }

    with open(os.path.join(output_dir, "consolidated_data.json"), "w") as f:
        json.dump(consolidated, f, indent=4)

    # 5. AI Summary + network IOC analysis
    llm = LLMAnalyzer(model=args.model)
    summary = llm.analyze_report(primary_result) if results else "No analysis data captured."

    # Network artifact / IOC analysis (uses all regions' network logs)
    all_network_logs = []
    all_redirects = []
    for r in results:
        all_network_logs.extend(r.get("network_log") or [])
        all_redirects.extend(r.get("redirect_chain") or [])
    network_ioc_analysis = llm.analyze_network_artifacts(all_network_logs, all_redirects) if results else ""
    consolidated["network_ioc_analysis"] = network_ioc_analysis

    # 6. Generate Markdown Report
    generate_final_report(consolidated, summary, output_dir, model=args.model)

    # 7. Rename folder to brand name
    try:
        if results:
            brand_name = llm.extract_target_brand(primary_result)
            if brand_name and brand_name != "Unknown":
                new_folder_name = f"{brand_name}_{timestamp}"
                new_output_path = os.path.join("output", new_folder_name)
                if os.path.exists(new_output_path):
                    new_output_path = os.path.join("output", f"{brand_name}_{timestamp}_1")
                os.rename(output_dir, new_output_path)
                logger.info(f"Output directory renamed to brand: {new_output_path}")
    except Exception as e:
        logger.error(f"Failed to rename output directory: {e}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()

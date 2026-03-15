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


async def analyze_phishing_url_region(url: str, headless: bool, region_code: str, output_dir: str):
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
    llm = LLMAnalyzer(model="mistral")

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


def generate_final_report(consolidated_data, llm_summary, output_dir: str):
    md = "# PhishHunter Final Forensic Report\n\n"
    md += f"**Target**: `{consolidated_data['target_url']}`\n"
    md += f"**Scan Time**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"

    # Risk Score summary
    risk = consolidated_data.get("risk_score", {})
    if risk:
        score = risk.get("score", 0)
        level = risk.get("level", "unknown")
        level_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(level, "⚪")
        md += f"## {level_emoji} Risk Score: {score}/100 — {level.upper()}\n"
        factors = risk.get("factors", [])
        if factors:
            md += "**Scoring factors:**\n"
            for f in factors:
                md += f"- {f}\n"
        md += "\n"

    # Threat Intel
    ti = consolidated_data.get("threat_intel", {})
    if ti:
        md += "## Threat Intelligence\n\n"
        vt = ti.get("virustotal", {})
        if vt and not vt.get("skipped"):
            if vt.get("error"):
                md += f"**VirusTotal**: ⚠️ Error — {vt['error']}\n\n"
            else:
                md += f"**VirusTotal**: {vt.get('malicious', 0)} malicious / {vt.get('suspicious', 0)} suspicious / {vt.get('total', 0)} engines\n"
                if vt.get("permalink"):
                    md += f"[Voir le rapport VT]({vt['permalink']})\n\n"
        else:
            md += "**VirusTotal**: Non configuré (définir VT_API_KEY)\n\n"

        whois = ti.get("whois", {})
        if whois and not whois.get("error"):
            age = whois.get("age_days")
            age_str = f"{age} jours" if age is not None else "inconnu"
            md += f"**Domain Age**: {age_str} (enregistré le {whois.get('registration_date', '?')[:10]})\n"
            md += f"**Registrar**: {whois.get('registrar', 'inconnu')}\n\n"

        ssl_d = ti.get("ssl", {})
        if ssl_d:
            valid_str = "✅ Valide" if ssl_d.get("valid") else ("❌ Expiré" if ssl_d.get("is_expired") else "⚠️ Invalide/Absent")
            md += f"**SSL**: {valid_str} — Émetteur: {ssl_d.get('issuer', '?')}"
            if ssl_d.get("days_left") is not None:
                md += f" ({ssl_d['days_left']} jours restants)"
            if ssl_d.get("is_self_signed"):
                md += " ⚠️ AUTO-SIGNÉ"
            md += "\n\n"

        # URLScan.io
        urlscan = ti.get("urlscan") or {}
        if urlscan.get("found") and not urlscan.get("skipped"):
            malicious_flags = urlscan.get("malicious_flags", 0)
            flag_str = f"🔴 {malicious_flags} scan(s) malicieux" if malicious_flags else "✅ Aucun flag malicieux"
            md += f"**URLScan.io**: {flag_str} sur {urlscan.get('total_prior_scans', 0)} scan(s) historiques\n"
            if urlscan.get("recent_scans"):
                latest = urlscan["recent_scans"][0]
                if latest.get("report_url"):
                    md += f"  Dernier rapport: [{latest['scan_date'][:10]}]({latest['report_url']})\n"
            md += "\n"
        elif urlscan.get("found") is False:
            md += "**URLScan.io**: Aucun scan historique trouvé pour ce domaine\n\n"

        # IP / ASN info
        ip_info = ti.get("ip_info") or {}
        if ip_info and not ip_info.get("error"):
            flags = []
            if ip_info.get("is_proxy"):
                flags.append("⚠️ Proxy/VPN")
            if ip_info.get("is_hosting"):
                flags.append("⚠️ Hébergement dédié")
            flag_str = " ".join(flags) if flags else "✅"
            md += (f"**Infrastructure**: IP `{ip_info.get('ip')}` — "
                   f"{ip_info.get('country', '?')} — "
                   f"{ip_info.get('isp', '?')} — "
                   f"ASN: `{ip_info.get('asn', '?')}` {flag_str}\n\n")

    md += "## AI Forensic Analysis\n"
    md += f"{llm_summary}\n\n"

    # Network IOC section
    network_ioc = consolidated_data.get("network_ioc_analysis", "")
    if network_ioc:
        md += "## Analyse des Artefacts Réseau & IOCs\n"
        md += f"{network_ioc}\n\n"

    md += "## Deep Agentic Analysis (User Journey)\n"
    md += ("The automated engine performed a deep dive, simulating a victim's complete path to the payload. "
           "Below is the step-by-step analysis performed by the AI Agent.\n\n")

    ref_region = consolidated_data["regions"][0]
    llm = LLMAnalyzer(model="mistral")

    if ref_region.get("interaction_journey"):
        steps = ref_region["interaction_journey"]
        logger.info(f"Generating report for {len(steps)} steps.")

        # ── Summary table ──
        md += "### Résumé du parcours\n\n"
        md += "| # | Action | URL | Suspicion |\n"
        md += "|---|--------|-----|-----------|\n"
        for i, step in enumerate(steps):
            desc_short = step['description'][:60] + ("…" if len(step['description']) > 60 else "")
            url_short = (step.get('url') or 'N/A')
            url_short = url_short[:60] + ("…" if len(url_short) > 60 else "")
            patterns = step.get('ai_patterns') or {}
            score = patterns.get('suspicion_score')
            score_str = f"**{score}%**" if score is not None else "—"
            md += f"| {i+1} | {desc_short} | `{url_short}` | {score_str} |\n"
        md += "\n"

        # ── Detailed steps ──
        for i, step in enumerate(steps):
            logger.info(f"Agentic Analysis: Analyzing step {i+1}/{len(steps)}...")
            try:
                insight = llm.analyze_journey_step(step)
            except Exception as e:
                logger.error(f"LLM Step Analysis failed for step {i}: {e}")
                insight = "(Analysis failed due to LLM error)"

            # Step header with emoji marker
            desc = step['description']
            if "PAYMENT" in desc.upper() or "PAIEMENT" in desc.upper():
                marker = "💳"
            elif "captcha" in desc.lower() or "CAPTCHA" in desc:
                marker = "🛡️"
            elif "Form Auto-Fill" in desc:
                marker = "📝"
            elif i == 0:
                marker = "🏁"
            else:
                marker = "➡️"

            md += f"### {marker} Étape {i+1} : {step['description']}\n"
            md += f"**URL** : `{step.get('url', 'unknown')}`\n\n"
            md += f"> **Agent Insight** : {insight}\n\n"

            # AI patterns block
            patterns = step.get('ai_patterns') or {}
            if patterns and patterns.get('detected_patterns'):
                md += "**Patterns détectés** : "
                md += " · ".join([f"`{p}`" for p in patterns['detected_patterns']]) + "\n\n"
            if patterns.get('brand_impersonation') and patterns['brand_impersonation'] not in ('null', 'None', None):
                md += f"**Marque usurpée** : `{patterns['brand_impersonation']}`\n\n"
            if patterns.get('has_data_harvesting_form'):
                md += "> ⚠️ **Formulaire de collecte de données détecté**\n\n"

            img_name = os.path.basename(step['screenshot_path'])
            md += f"![Étape {i+1}]({img_name})\n\n"

            md += "---\n"
    else:
        md += "_No interactive steps triggered._\n\n"


    md += "## Regional Analysis\n"
    for r in consolidated_data["regions"]:
        code = r["region"]
        md += f"### Region: {code}\n"
        md += f"![Screenshot {code}](screenshot_{code}.png)\n\n"

        md += "**Redirect Chain:**\n"
        for i, hop in enumerate(r['redirect_chain']):
            md += f"{i+1}. `{hop['url']}` ({hop.get('status', '???')})\n"

        if r['inputs']:
            md += f"\n**Data Collection detected**: {len(r['inputs'])} inputs found.\n"
        else:
            md += "\n**Data Collection**: No forms visible.\n"

        md += "---\n\n"

    md += "## Artifacts & Obfuscation\n"
    seen_urls = set()
    for r in consolidated_data["regions"]:
        for f in r["files_extracted"]:
            if f["url"] not in seen_urls:
                seen_urls.add(f["url"])
                md += f"### {f['type'].upper()}: `{f['url']}`\n"
                analysis = f.get("analysis", {})
                if analysis.get("obfuscation_detected"):
                    md += "> **Obfuscation Detected**\n"
                    md += f"> Entropy: {analysis.get('entropy_score', 0):.2f}\n"
                if analysis.get("ai_explanation"):
                    md += f"> **AI Analysis**: {analysis.get('ai_explanation')}\n"
                if analysis.get("deobfuscated_preview"):
                    md += "#### Deobfuscated Preview:\n```javascript\n"
                    md += analysis["deobfuscated_preview"][:800] + "\n...\n```\n"
                md += "\n"

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
        res = asyncio.run(analyze_phishing_url_region(target_url, not args.visible, region, output_dir))
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
    generate_final_report(consolidated, summary, output_dir)

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

import asyncio
import argparse
import json
import logging
import os
from datetime import datetime

from core.browser import BrowserManager
from core.llm import LLMAnalyzer
from analysis.java import JavaForensics
from analysis.javascript import JSAnalysis
from analysis.visual import VisualAnalysis

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PhishHunter")

async def analyze_phishing_url_region(url: str, headless: bool, region_code: str):
    # Map regions to loc/tz
    REGIONS = {
        "US": {"locale": "en-US", "timezone": "America/New_York"},
        "FR": {"locale": "fr-FR", "timezone": "Europe/Paris"},
        "DE": {"locale": "de-DE", "timezone": "Europe/Berlin"},
        "JP": {"locale": "ja-JP", "timezone": "Asia/Tokyo"}
    }
    config = REGIONS.get(region_code, REGIONS["US"])
    
    logger.info(f"Starting analysis for: {url} (Region: {region_code})")
    
    browser = BrowserManager(headless=headless)
    java_analyzer = JavaForensics()
    js_analyzer = JSAnalysis()
    visual_analyzer = VisualAnalysis()
    
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "target_url": url,
        "region": region_code,
        "redirect_chain": [],
        "files_extracted": [],
        "visual_analysis": {},
        "obfuscation_flags": [],
        "links": [],
        "inputs": []
    }

    try:
        await browser.start(locale=config["locale"], timezone_id=config["timezone"])
        result = await browser.analyze_url(url)
        
        
        raw_journey = result.get("interaction_journey", [])
        print(f"DEBUG_CRITICAL: main.py received {len(raw_journey)} steps from browser.")
        if "interaction_journey" not in report: report["interaction_journey"] = []

        logger.info(f"DEBUG: Browser returned {len(raw_journey)} steps.")

        for step in raw_journey:
            # Save step screenshot
            step_filename = f"output/screenshot_{region_code}_{step['step']}.png"
            with open(step_filename, "wb") as f: f.write(step['screenshot'])
            
            # Save HTML to file to keep JSON light
            html_filename = f"output/html_{region_code}_{step['step']}.html"
            with open(html_filename, "w", encoding="utf-8", errors="ignore") as f: 
                f.write(step.get('html', ''))

            report["interaction_journey"].append({
                "step": step['step'],
                "description": step['description'],
                "screenshot_path": step_filename, # Relative for MD
                "html_path": html_filename,
                "url": step.get('url', 'unknown')
            })
        
        logger.info(f"DEBUG: Report['interaction_journey'] has {len(report['interaction_journey'])} steps.")
        logger.info(f"Report Generation: Captured {len(report['interaction_journey'])} interaction steps.")
            
        report["redirect_chain"] = result["redirect_chain"]
        report["links"] = result.get("links", [])
        report["inputs"] = result.get("inputs", [])
        
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
            elif file_type == "js":
                js_path = os.path.join("output/dump", f"{filename}.js")
                # Save only if unique? For now overwrite is okay or distinct names
                with open(js_path, "wb") as f: f.write(content)
                js_res = js_analyzer.analyze_js(content, filename)
                report["files_extracted"].append({"type": "javascript", "url": entry["url"], "analysis": js_res})

        # Visual
        screenshot = result["screenshot"]
        # Save screenshot with region prefix
        with open(f"output/screenshot_{region_code}.png", "wb") as f: f.write(screenshot)
        visual_res = visual_analyzer.analyze_screenshot(screenshot)
        report["visual_analysis"] = visual_res

    except Exception as e:
        logger.error(f"Analysis failed for {region_code}: {e}")
        traceback.print_exc()
        report["error"] = str(e)
    finally:
        await browser.close()
    
    return report

def generate_final_report(consolidated_data, llm_summary):
    md = "# 🕵️ PhishHunter Final Forensic Report\n\n"
    md += f"**Target**: `{consolidated_data['target_url']}`\n"
    md += f"**Scan Time**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
    
    md += "## 🧠 AI Forensic Analysis\n"
    md += f"{llm_summary}\n\n"
    
    md += "## 🕹️ Deep Agentic Analysis (User Journey)\n"
    md += "The automated engine performed a deep dive, simulating a victim's complete path to the payload. "
    md += "Below is the step-by-step analysis performed by the AI Agent.\n\n"
    
    # Use US region (first) as reference for visuals
    ref_region = consolidated_data["regions"][0]
    llm = LLMAnalyzer(model="mistral") # Re-init local analyzer for this phase
    


    # ... inside generate_final_report ...
    
    if ref_region.get("interaction_journey"):
        steps = ref_region["interaction_journey"]
        logger.info(f"DEBUG: Generating report for {len(steps)} steps.")
        for i, step in enumerate(steps):
            logger.info(f"Agentic Analysis: Analyzing step {i+1}/{len(steps)}...")
            try:
                insight = llm.analyze_journey_step(step)
            except Exception as e:
                logger.error(f"LLM Step Analysis failed for step {i}: {e}")
                insight = "(Analysis failed due to LLM error)"
            
            md += f"### Step {i+1}: {step['description']}\n"
            md += f"**URL**: `{step.get('url', 'unknown')}`\n\n"
            md += f"> 🤖 **Agent Insight**: {insight}\n\n"
            
            img_name = os.path.basename(step['screenshot_path'])
            md += f"![Step {i+1}]({img_name})\n\n"
            md += "---\n"
    else:
        md += "_No interactive steps triggered._\n\n"
    
    md += "## 🌍 Regional Analysis\n"
    for r in consolidated_data["regions"]:
        code = r["region"]
        md += f"### Region: {code}\n"
        md += f"![Screenshot {code}](screenshot_{code}.png)\n\n"
        
        # Kill Chain
        md += "**Redirect Chain:**\n"
        for i, hop in enumerate(r['redirect_chain']):
            md += f"{i+1}. `{hop['url']}` ({hop.get('status', '???')})\n"
        
        # Inputs
        if r['inputs']:
            md += f"\n**Data Collection detected**: {len(r['inputs'])} inputs found.\n"
        else:
            md += "\n**Data Collection**: No forms visible.\n"
        
        md += "---\n\n"

    md += "## 📦 Artifacts & Obfuscation\n"
    # Aggregate artifacts from all regions (deduplicated by URL)
    seen_urls = set()
    for r in consolidated_data["regions"]:
        for f in r["files_extracted"]:
            if f["url"] not in seen_urls:
                seen_urls.add(f["url"])
                md += f"### {f['type'].upper()}: `{f['url']}`\n"
                analysis = f.get("analysis", {})
                if analysis.get("obfuscation_detected"):
                    md += "> ⚠️ **Obfuscation Detected**\n"
                    md += f"> Entropy: {analysis.get('entropy_score', 0):.2f}\n"
                    if analysis.get("deobfuscated_preview"):
                        md += "#### Deobfuscated Preview:\n```javascript\n"
                        md += analysis["deobfuscated_preview"][:800] + "\n...\n```\n"
                md += "\n"

    with open("output/FINAL_REPORT.md", "w", encoding="utf-8") as f:
        f.write(md)
    logger.info("Final report generated: output/FINAL_REPORT.md")


def main():
    parser = argparse.ArgumentParser(description="PhishHunter")
    parser.add_argument("url", help="Target URL")
    parser.add_argument("--visible", action="store_true")
    parser.add_argument("--regions", default="US", help="Regions CSV (US,FR)")
    parser.add_argument("--model", default="llama3", help="Ollama model to use")
    args = parser.parse_args()
    
    regions = args.regions.split(",")
    results = []
    
    # 1. Run Analysis
    for region in regions:
        code = region.strip().upper()
        res = asyncio.run(analyze_phishing_url_region(args.url, not args.visible, code))
        results.append(res)
    
    # 2. Consolidate
    consolidated = {
        "target_url": args.url,
        "regions": results
    }
    
    # Save raw JSON
    os.makedirs("output", exist_ok=True)
    with open("output/consolidated_data.json", "w") as f:
        json.dump(consolidated, f, indent=4)
        
    # 3. AI Analysis
    # We pick the most 'complete' report (e.g. one with most inputs found) or just the first
    # to feed to the LLM to save context, or feed a summary.
    # Let's feed the first one for now.
    llm = LLMAnalyzer(model=args.model)
    # Check if we have data
    if results:
        summary = llm.analyze_report(results[0])
    else:
        summary = "No analysis data captured."
        
    # 4. Generate Markdown
    generate_final_report(consolidated, summary)

import traceback

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()

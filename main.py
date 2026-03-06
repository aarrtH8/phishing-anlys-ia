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
from analysis.java import JavaForensics
from analysis.javascript import JSAnalysis
from analysis.visual import VisualAnalysis

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PhishHunter")

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
    
    browser = BrowserManager(headless=headless)
    java_analyzer = JavaForensics()
    js_analyzer = JSAnalysis()
    visual_analyzer = VisualAnalysis()
    llm = LLMAnalyzer(model="mistral") # Use Mistral for file analysis
    
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
        "interaction_journey": []
    }

    try:
        await browser.start(locale=config["locale"], timezone_id=config["timezone"])
        result = await browser.analyze_url(url)
        
        
        raw_journey = result.get("interaction_journey", [])
        logger.info(f"Browser returned {len(raw_journey)} interaction steps.")

        for step in raw_journey:
            # Save step screenshot
            step_filename = os.path.join(output_dir, f"screenshot_{region_code}_{step['step']}.png")
            with open(step_filename, "wb") as f: f.write(step['screenshot'])
            
            # Save HTML to file to keep JSON light
            html_filename = os.path.join(output_dir, f"html_{region_code}_{step['step']}.html")
            with open(html_filename, "w", encoding="utf-8", errors="ignore") as f: 
                f.write(step.get('html', ''))

            report["interaction_journey"].append({
                "step": step['step'],
                "description": step['description'],
                "screenshot_path": step_filename, # Relative for MD
                "html_path": html_filename,
                "url": step.get('url', 'unknown')
            })
        
        logger.info(f"Captured {len(report['interaction_journey'])} interaction steps.")
            
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
                
                # Generate Report
                try:
                    dump_dir = os.path.join(output_dir, "dump")
                    os.makedirs(dump_dir, exist_ok=True)
                    rep_path = os.path.join(dump_dir, f"{filename}_report.md")
                    with open(rep_path, "w", encoding="utf-8") as f:
                        f.write(f"# Java Analysis: {filename}\n\n")
                        f.write(f"**Source**: `{entry['url']}`\n\n")
                        f.write(f"## Metadata\n```json\n{json.dumps(java_res, indent=2)}\n```\n")
                except Exception: pass
            elif file_type == "js":
                dump_dir = os.path.join(output_dir, "dump")
                os.makedirs(dump_dir, exist_ok=True)
                js_path = os.path.join(dump_dir, f"{filename}.js")
                with open(js_path, "wb") as f: f.write(content)
                
                # Static Analysis
                js_res = js_analyzer.analyze_js(content, filename)
                
                # AI Semantic Analysis (New)
                try:
                    js_text = content.decode('utf-8', errors='ignore')
                    js_res["ai_explanation"] = llm.analyze_javascript(js_text, filename)
                except Exception as e:
                    js_res["ai_explanation"] = f"Error: {e}"

                report["files_extracted"].append({"type": "javascript", "url": entry["url"], "analysis": js_res})
                
                # Generate Report
                try:
                    rep_path = os.path.join(dump_dir, f"{filename}_report.md")
                    with open(rep_path, "w", encoding="utf-8") as f:
                        f.write(f"# JS Forensic Analysis: {filename}\n\n")
                        f.write(f"**Source**: `{entry['url']}`\n")
                        f.write(f"**Entropy**: {js_res.get('entropy_score', 0):.2f}\n")
                        f.write(f"**Obfuscated**: {js_res.get('obfuscation_detected')}\n\n")
                        f.write("## 🧠 AI Explanation\n")
                        f.write(f"{js_res.get('ai_explanation', 'N/A')}\n\n")
                        if js_res.get('deobfuscated_preview'):
                             f.write("## Deobfuscated Preview\n```javascript\n")
                             f.write(js_res['deobfuscated_preview'][:2000] + "\n```\n")
                except Exception as e:
                    logger.warning(f"Failed to write JS report for {filename}: {e}")

        # Visual
        screenshot = result["screenshot"]
        # Save screenshot with region prefix
        with open(os.path.join(output_dir, f"screenshot_{region_code}.png"), "wb") as f: f.write(screenshot)
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
            
            if step.get("description", "").lower().startswith("form auto-fill"):
                 md += "✅ **Action**: Automated data entry to bypass detection.\n\n"
            
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
                
                if analysis.get("ai_explanation"):
                    md += f"> 🧠 **AI Analysis**: {analysis.get('ai_explanation')}\n"

                if analysis.get("deobfuscated_preview"):
                    md += "#### Deobfuscated Preview:\n```javascript\n"
                    md += analysis["deobfuscated_preview"][:800] + "\n...\n```\n"
                md += "\n"

    report_path = os.path.join(output_dir, "FINAL_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)
    logger.info(f"Final report generated: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="PhishHunter")
    parser.add_argument("url", help="Target URL")
    parser.add_argument("--visible", action="store_true")
    parser.add_argument("--regions", default="FR", help="Regions CSV (US,FR)")
    parser.add_argument("--model", default="mistral", help="Ollama model to use")
    args = parser.parse_args()
    
    regions = args.regions.split(",")
    results = []
    
    
    # Create specific output directory
    domain = urlparse(args.url).netloc.replace(":", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{domain}_{timestamp}"
    output_dir = os.path.join("output", run_id)
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"📁 Output directory: {output_dir}")

    # 1. Run Analysis
    for region in regions:
        code = region.strip().upper()
        res = asyncio.run(analyze_phishing_url_region(args.url, not args.visible, code, output_dir))
        results.append(res)
    
    # 2. Consolidate
    consolidated = {
        "target_url": args.url,
        "regions": results
    }
    
    # Save raw JSON
    with open(os.path.join(output_dir, "consolidated_data.json"), "w") as f:
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
    generate_final_report(consolidated, summary, output_dir)
    
    # 5. Connect Brand Name & Rename Folder
    # To correspond with user request: "dossier qui porte le nom de l'entreprise"
    try:
        if results:
            brand_name = llm.extract_target_brand(results[0])
            if brand_name and brand_name != "Unknown":
                new_folder_name = f"{brand_name}_{timestamp}"
                new_output_path = os.path.join("output", new_folder_name)
                
                # Check collision
                if os.path.exists(new_output_path):
                    new_output_path = os.path.join("output", f"{brand_name}_{timestamp}_1")
                
                os.rename(output_dir, new_output_path)
                logger.info(f"✨ Output directory renamed to target brand: {new_output_path}")
            else:
                logger.info(f"Brand unknown, keeping generic name: {output_dir}")
    except Exception as e:
        logger.error(f"Failed to rename output directory: {e}")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()

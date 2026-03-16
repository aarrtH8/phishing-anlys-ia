"""
PhishHunter GUI — Flask Backend
Serves the web dashboard and provides API endpoints to browse scan results and launch new scans.
"""

import os
import json
import pathlib
import subprocess
import threading
import glob
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory, abort

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Docker Compose project name — must match COMPOSE_PROJECT_NAME in run_all.bat
# so the built image is consistently named "phishhunter-analyzer"
COMPOSE_PROJECT_NAME = "phishhunter"


def _load_dotenv():
    """Load .env file into os.environ without requiring python-dotenv."""
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


_load_dotenv()

app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(__file__), "templates"),
            static_folder=os.path.join(os.path.dirname(__file__), "static"))

# Global scan state
_scan_lock = threading.Lock()
_current_scan = {
    "running": False,
    "url": None,
    "started_at": None,
    "process": None,
    "output": "",
    "return_code": None,
    "visible": False,   # True when launched with --visible (NoVNC active)
}


def _safe_folder_path(folder_name: str):
    """Resolve folder_name inside OUTPUT_DIR, abort(400) if traversal detected."""
    output_real = pathlib.Path(OUTPUT_DIR).resolve()
    folder_path = (output_real / folder_name).resolve()
    if not str(folder_path).startswith(str(output_real) + os.sep) and folder_path != output_real:
        abort(400)
    return folder_path


# ─────────────────────────── Pages ───────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ─────────────────────────── API ───────────────────────────

@app.route("/api/scans")
def list_scans():
    """List all scan result folders with metadata. Supports ?q= keyword filter."""
    scans = []
    if not os.path.isdir(OUTPUT_DIR):
        return jsonify(scans)

    for folder_name in os.listdir(OUTPUT_DIR):
        folder_path = os.path.join(OUTPUT_DIR, folder_name)
        if not os.path.isdir(folder_path):
            continue

        scan_info = {
            "id": folder_name,
            "folder": folder_name,
            "date": None,
            "target_url": None,
            "regions": [],
            "has_report": False,
            "screenshot_count": 0,
            "threat_level": "unknown"
        }

        # Try to read consolidated_data.json
        json_path = os.path.join(folder_path, "consolidated_data.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                scan_info["target_url"] = data.get("target_url", "Unknown")
                if data.get("regions"):
                    scan_info["regions"] = [r.get("region", "?") for r in data["regions"]]
                    # Extract date from first region timestamp
                    ts = data["regions"][0].get("timestamp", "")
                    if ts:
                        scan_info["date"] = ts
                    # Use pre-computed risk_score if available, else heuristic fallback
                    risk = data.get("risk_score", {})
                    if risk and risk.get("level"):
                        level_map = {"critical": "high", "high": "high", "medium": "medium", "low": "low"}
                        scan_info["threat_level"] = level_map.get(risk["level"], "unknown")
                        scan_info["risk_score"] = risk.get("score", 0)
                        scan_info["risk_level"] = risk.get("level", "unknown")
                        scan_info["risk_factors"] = risk.get("factors", [])
                    else:
                        region_data = data["regions"][0]
                        inputs_count = len(region_data.get("inputs", []))
                        redirects = len(region_data.get("redirect_chain", []))
                        obfuscated = sum(1 for f in region_data.get("files_extracted", [])
                                         if f.get("analysis", {}).get("obfuscation_detected"))
                        if obfuscated > 0 or inputs_count > 2 or redirects > 3:
                            scan_info["threat_level"] = "high"
                        elif inputs_count > 0 or redirects > 1:
                            scan_info["threat_level"] = "medium"
                        else:
                            scan_info["threat_level"] = "low"
                        scan_info["risk_score"] = 0
                        scan_info["risk_level"] = scan_info["threat_level"]
                        scan_info["risk_factors"] = []

                    # Threat Intel summary for cards
                    ti = data.get("threat_intel", {})
                    if ti:
                        whois = ti.get("whois") or {}
                        vt = ti.get("virustotal") or {}
                        ssl_d = ti.get("ssl") or {}
                        scan_info["ti_summary"] = {
                            "domain_age_days": whois.get("age_days"),
                            "is_very_young": whois.get("is_very_young", False),
                            "vt_malicious": vt.get("malicious") if not vt.get("skipped") and not vt.get("error") else None,
                            "vt_total": vt.get("total"),
                            "ssl_valid": ssl_d.get("valid"),
                            "ssl_issuer": ssl_d.get("issuer", ""),
                            "ssl_self_signed": ssl_d.get("is_self_signed", False),
                        }
            except Exception:
                pass

        # Check for report
        report_path = os.path.join(folder_path, "FINAL_REPORT.md")
        scan_info["has_report"] = os.path.exists(report_path)

        # Count screenshots
        screenshots = glob.glob(os.path.join(folder_path, "screenshot_*.png"))
        scan_info["screenshot_count"] = len(screenshots)

        # Fallback date from folder mtime
        if not scan_info["date"]:
            mtime = os.path.getmtime(folder_path)
            scan_info["date"] = datetime.fromtimestamp(mtime).isoformat()

        scans.append(scan_info)

    # Sort by date descending
    scans.sort(key=lambda s: s.get("date", ""), reverse=True)

    # Optional keyword filter
    q = request.args.get("q", "").lower().strip()
    if q:
        scans = [s for s in scans if q in (s.get("target_url") or "").lower()
                 or q in (s.get("folder") or "").lower()]

    return jsonify(scans)


@app.route("/api/scans/<folder_name>")
def get_scan(folder_name):
    """Get full details for a single scan."""
    folder_path = _safe_folder_path(folder_name)
    if not folder_path.is_dir():
        abort(404)
    folder_path = str(folder_path)

    result = {
        "id": folder_name,
        "report_md": None,
        "consolidated_data": None,
        "screenshots": [],
        "html_files": [],
        "dump_files": []
    }

    # Read report
    report_path = os.path.join(folder_path, "FINAL_REPORT.md")
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            result["report_md"] = f.read()

    # Read consolidated data
    json_path = os.path.join(folder_path, "consolidated_data.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            result["consolidated_data"] = json.load(f)

    # List screenshots
    for fname in sorted(os.listdir(folder_path)):
        if fname.endswith(".png"):
            result["screenshots"].append(fname)
        elif fname.endswith(".html"):
            result["html_files"].append(fname)

    # List dump files
    dump_dir = os.path.join(folder_path, "dump")
    if os.path.isdir(dump_dir):
        for fname in sorted(os.listdir(dump_dir)):
            result["dump_files"].append(fname)

    return jsonify(result)


@app.route("/api/scans/<folder_name>/files/<path:filename>")
def serve_scan_file(folder_name, filename):
    """Serve any file from a scan folder (screenshots, HTML, etc.)."""
    # Prevent directory traversal: resolve both paths and check containment
    output_real = pathlib.Path(OUTPUT_DIR).resolve()
    folder_path = (output_real / folder_name).resolve()

    # folder_name must stay inside OUTPUT_DIR
    if not str(folder_path).startswith(str(output_real)):
        abort(400)
    if not folder_path.is_dir():
        abort(404)

    # Allow serving from dump subdirectory
    if filename.startswith("dump/"):
        sub_file = filename[5:]
        safe_path = (folder_path / "dump" / sub_file).resolve()
        if not str(safe_path).startswith(str(folder_path)):
            abort(400)
        return send_from_directory(str(folder_path / "dump"), sub_file)

    safe_path = (folder_path / filename).resolve()
    if not str(safe_path).startswith(str(folder_path)):
        abort(400)

    return send_from_directory(str(folder_path), filename)


@app.route("/api/preflight")
def preflight():
    """Check if Docker and Ollama are available."""
    checks = {"docker": False, "ollama": False, "image_built": False}

    # Check Docker
    try:
        r = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
        checks["docker"] = r.returncode == 0
    except Exception:
        pass

    # Check Ollama + list available models
    try:
        import urllib.request as _urllib_req
        req = _urllib_req.urlopen("http://localhost:11434/api/tags", timeout=3)
        if req.status == 200:
            checks["ollama"] = True
            raw = json.loads(req.read().decode())
            checks["ollama_models"] = [m["name"] for m in raw.get("models", [])]
        else:
            checks["ollama_models"] = []
    except Exception:
        checks["ollama_models"] = []

    # Check if image exists (use the project name forced by COMPOSE_PROJECT_NAME)
    if checks["docker"]:
        try:
            env = {**os.environ, "COMPOSE_PROJECT_NAME": COMPOSE_PROJECT_NAME}
            r = subprocess.run(
                ["docker", "images", "-q", f"{COMPOSE_PROJECT_NAME}-analyzer"],
                capture_output=True, text=True, timeout=5, env=env)
            if not r.stdout.strip():
                # Fallback: ask compose directly
                r = subprocess.run(
                    ["docker", "compose", "images", "-q"],
                    capture_output=True, text=True, timeout=5, cwd=BASE_DIR, env=env)
            checks["image_built"] = bool(r.stdout.strip())
        except Exception:
            pass

    return jsonify(checks)


@app.route("/api/vt-status")
def vt_status():
    """Return VirusTotal configuration status and quota information."""
    vt_key = os.environ.get("VT_API_KEY", "").strip()
    configured = bool(vt_key)

    # Mask key for display: show first 6 and last 4 chars
    key_masked = None
    if configured:
        key_masked = vt_key[:6] + "..." + vt_key[-4:]

    return jsonify({
        "configured": configured,
        "key_masked": key_masked,
        "plan": "Free — Public API",
        "quota": {
            "rate": "4 lookups / min",
            "daily": "500 lookups / day",
            "monthly": "15 500 lookups / month",
        },
        "usage_note": "Usage restreint aux usages non-commerciaux.",
        "upgrade_url": "https://www.virustotal.com/gui/my-apikey"
    })


@app.route("/api/scan", methods=["POST"])
def launch_scan():
    """Launch a new phishing URL scan via Docker."""
    with _scan_lock:
        if _current_scan["running"]:
            return jsonify({"error": "Un scan est déjà en cours."}), 409

    data = request.get_json()
    url = data.get("url", "").strip()
    regions = data.get("regions", "FR").strip()
    visible = data.get("visible", False)
    use_vt = data.get("use_vt", True)
    model = data.get("model", "mistral").strip() or "mistral"

    if not url:
        return jsonify({"error": "URL requise."}), 400

    def run_scan():
        with _scan_lock:
            _current_scan["running"] = True
            _current_scan["url"] = url
            _current_scan["started_at"] = datetime.now().isoformat()
            _current_scan["output"] = ""
            _current_scan["return_code"] = None
            _current_scan["visible"] = visible

        try:
            cmd_args = ["python", "main.py", url, "--regions", regions, "--model", model]
            if visible:
                cmd_args.append("--visible")
            if not use_vt:
                cmd_args.append("--no-vt")

            docker_cmd = [
                "docker", "compose", "run", "--rm",
                # --service-ports exposes all mapped ports (needed for NoVNC on :6080/:5900)
                "--service-ports",
                # Use a unique container name per scan to avoid "already in use" conflicts
                "--name", f"phish-scan-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "analyzer"
            ] + cmd_args

            _current_scan["output"] += f"[GUI] Lancement du scan...\n"
            _current_scan["output"] += f"[GUI] URL: {url}\n"
            _current_scan["output"] += f"[GUI] Régions: {regions}\n"
            _current_scan["output"] += f"[GUI] Modèle LLM: {model}\n"
            _current_scan["output"] += f"[GUI] VirusTotal: {'activé' if use_vt else 'désactivé'}\n"
            _current_scan["output"] += f"[GUI] Commande: {' '.join(docker_cmd)}\n"
            _current_scan["output"] += f"[GUI] {'='*50}\n\n"

            # Pass COMPOSE_PROJECT_NAME so docker compose uses the right image
            proc_env = {**os.environ, "COMPOSE_PROJECT_NAME": COMPOSE_PROJECT_NAME}
            proc = subprocess.Popen(
                docker_cmd,
                cwd=BASE_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=proc_env,
            )
            _current_scan["process"] = proc

            for line in proc.stdout:
                _current_scan["output"] += line

            proc.wait()
            _current_scan["return_code"] = proc.returncode

            if proc.returncode == 0:
                _current_scan["output"] += f"\n[GUI] {'='*50}\n"
                _current_scan["output"] += f"[GUI] Scan terminé avec succès.\n"
            else:
                _current_scan["output"] += f"\n[GUI] {'='*50}\n"
                _current_scan["output"] += f"[GUI] Scan terminé avec le code {proc.returncode}.\n"

        except FileNotFoundError:
            _current_scan["output"] += "\n[ERREUR] Docker n'est pas installé ou pas dans le PATH.\n"
            _current_scan["output"] += "Assurez-vous que Docker Desktop est lancé.\n"
            _current_scan["return_code"] = -1
        except Exception as e:
            _current_scan["output"] += f"\n[ERREUR] {str(e)}\n"
            _current_scan["return_code"] = -1
        finally:
            with _scan_lock:
                _current_scan["running"] = False
                _current_scan["process"] = None

    thread = threading.Thread(target=run_scan, daemon=True)
    thread.start()

    return jsonify({"status": "started", "url": url, "regions": regions, "use_vt": use_vt})


@app.route("/api/scan/stop", methods=["POST"])
def stop_scan():
    """Stop the current running scan."""
    with _scan_lock:
        if not _current_scan["running"]:
            return jsonify({"error": "Aucun scan en cours."}), 400
        proc = _current_scan.get("process")
        if proc:
            try:
                proc.terminate()
                _current_scan["output"] += "\n[GUI] Scan interrompu par l'utilisateur.\n"
            except Exception:
                pass
    return jsonify({"status": "stopped"})


@app.route("/api/scan/status")
def scan_status():
    """Check status of the current/last scan.
    Supports ?offset=N to return only new output lines since position N (incremental).
    """
    offset = request.args.get("offset", 0, type=int)
    full_output = _current_scan["output"] or ""
    # Return a sliding window: last 8 000 chars, or from offset if provided
    if offset > 0 and offset < len(full_output):
        partial = full_output[offset:]
    else:
        partial = full_output[-8000:]

    return jsonify({
        "running": _current_scan["running"],
        "url": _current_scan["url"],
        "started_at": _current_scan["started_at"],
        "output": partial,
        "output_length": len(full_output),
        "return_code": _current_scan["return_code"],
        "visible": _current_scan.get("visible", False),
    })


@app.route("/api/scans/<folder_name>/download/json")
def download_scan_json(folder_name):
    """Download the consolidated_data.json for a scan as a file attachment."""
    folder_path = _safe_folder_path(folder_name)
    if not folder_path.is_dir():
        abort(404)
    json_path = folder_path / "consolidated_data.json"
    if not json_path.exists():
        abort(404)
    return send_from_directory(
        str(folder_path),
        "consolidated_data.json",
        as_attachment=True,
        download_name=f"phishhunter_{folder_name}.json"
    )


@app.route("/api/scans/<folder_name>/download/report")
def download_scan_report(folder_name):
    """Download the FINAL_REPORT.md for a scan as a file attachment."""
    folder_path = _safe_folder_path(folder_name)
    if not folder_path.is_dir():
        abort(404)
    report_path = folder_path / "FINAL_REPORT.md"
    if not report_path.exists():
        abort(404)
    return send_from_directory(
        str(folder_path),
        "FINAL_REPORT.md",
        as_attachment=True,
        download_name=f"phishhunter_{folder_name}_report.md"
    )


@app.route("/api/scans/<folder_name>", methods=["DELETE"])
def delete_scan(folder_name):
    """Delete a scan result folder."""
    import shutil
    folder_path = _safe_folder_path(folder_name)
    if not folder_path.is_dir():
        abort(404)
    folder_path = str(folder_path)

    try:
        shutil.rmtree(folder_path)
        return jsonify({"status": "deleted", "folder": folder_name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────── Main ───────────────────────────

if __name__ == "__main__":
    print("  PhishHunter GUI — http://localhost:5000")
    print(f"  Reading scans from: {OUTPUT_DIR}")
    vt_configured = bool(os.environ.get("VT_API_KEY", "").strip())
    print(f"  VirusTotal: {'configuré' if vt_configured else 'non configuré (VT_API_KEY manquant)'}")
    app.run(host="0.0.0.0", port=5000, debug=True)

"""
PhishHunter GUI — Flask Backend
Serves the web dashboard and provides API endpoints to browse scan results and launch new scans.

Architecture:
  - The Docker container 'phish-hunter-visual' runs persistently (docker compose up -d).
  - This GUI uses 'docker exec' to run scans inside that container.
  - VNC/NoVNC is always available at http://localhost:6080/ while the container is running.
"""

import os
import json
import subprocess
import threading
import glob
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory, abort

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

CONTAINER_NAME = "phish-hunter-visual"

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
    "return_code": None
}


# ─────────────────────────── Pages ───────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ─────────────────────────── API ───────────────────────────

@app.route("/api/scans")
def list_scans():
    """List all scan result folders with metadata."""
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
                    ts = data["regions"][0].get("timestamp", "")
                    if ts:
                        scan_info["date"] = ts
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
            except Exception:
                pass

        report_path = os.path.join(folder_path, "FINAL_REPORT.md")
        scan_info["has_report"] = os.path.exists(report_path)

        screenshots = glob.glob(os.path.join(folder_path, "screenshot_*.png"))
        scan_info["screenshot_count"] = len(screenshots)

        if not scan_info["date"]:
            mtime = os.path.getmtime(folder_path)
            scan_info["date"] = datetime.fromtimestamp(mtime).isoformat()

        scans.append(scan_info)

    scans.sort(key=lambda s: s.get("date", ""), reverse=True)
    return jsonify(scans)


@app.route("/api/scans/<folder_name>")
def get_scan(folder_name):
    """Get full details for a single scan."""
    folder_path = os.path.join(OUTPUT_DIR, folder_name)
    if not os.path.isdir(folder_path):
        abort(404)

    result = {
        "id": folder_name,
        "report_md": None,
        "consolidated_data": None,
        "screenshots": [],
        "html_files": [],
        "dump_files": []
    }

    report_path = os.path.join(folder_path, "FINAL_REPORT.md")
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            result["report_md"] = f.read()

    json_path = os.path.join(folder_path, "consolidated_data.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            result["consolidated_data"] = json.load(f)

    for fname in sorted(os.listdir(folder_path)):
        if fname.endswith(".png"):
            result["screenshots"].append(fname)
        elif fname.endswith(".html"):
            result["html_files"].append(fname)

    dump_dir = os.path.join(folder_path, "dump")
    if os.path.isdir(dump_dir):
        for fname in sorted(os.listdir(dump_dir)):
            result["dump_files"].append(fname)

    return jsonify(result)


@app.route("/api/scans/<folder_name>/files/<path:filename>")
def serve_scan_file(folder_name, filename):
    """Serve any file from a scan folder (screenshots, HTML, etc.)."""
    folder_path = os.path.join(OUTPUT_DIR, folder_name)
    if not os.path.isdir(folder_path):
        abort(404)

    if filename.startswith("dump/"):
        return send_from_directory(os.path.join(folder_path, "dump"), filename[5:])

    return send_from_directory(folder_path, filename)


@app.route("/api/preflight")
def preflight():
    """Check if Docker, the analyzer container, and Ollama are available."""
    checks = {
        "docker": False,
        "container_running": False,
        "ollama": False,
    }

    # Check Docker daemon
    try:
        r = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
        checks["docker"] = r.returncode == 0
    except Exception:
        pass

    if not checks["docker"]:
        return jsonify(checks)

    # Check if the analyzer container is running
    try:
        r = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", CONTAINER_NAME],
            capture_output=True, text=True, timeout=5
        )
        checks["container_running"] = r.stdout.strip() == "true"
    except Exception:
        pass

    # Check Ollama
    try:
        import urllib.request
        req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        checks["ollama"] = req.status == 200
    except Exception:
        pass

    return jsonify(checks)


@app.route("/api/container/start", methods=["POST"])
def start_container():
    """Start the analyzer container in the background."""
    try:
        r = subprocess.run(
            ["docker", "compose", "up", "-d", "analyzer"],
            cwd=BASE_DIR,
            capture_output=True, text=True, timeout=120
        )
        if r.returncode == 0:
            return jsonify({"status": "started", "output": r.stdout})
        else:
            return jsonify({"status": "error", "output": r.stderr}), 500
    except Exception as e:
        return jsonify({"status": "error", "output": str(e)}), 500


@app.route("/api/scan", methods=["POST"])
def launch_scan():
    """Launch a new phishing URL scan via docker exec on the running container."""
    with _scan_lock:
        if _current_scan["running"]:
            return jsonify({"error": "Un scan est déjà en cours."}), 409

    data = request.get_json()
    url = data.get("url", "").strip()
    regions = data.get("regions", "FR").strip()
    visible = data.get("visible", False)

    if not url:
        return jsonify({"error": "URL requise."}), 400

    def run_scan():
        with _scan_lock:
            _current_scan["running"] = True
            _current_scan["url"] = url
            _current_scan["started_at"] = datetime.now().isoformat()
            _current_scan["output"] = ""
            _current_scan["return_code"] = None

        try:
            # Build python command to run inside the container
            py_args = ["python", "/app/main.py", url, "--regions", regions]
            if visible:
                py_args.append("--visible")

            # Use docker exec to run inside the already-running container
            docker_cmd = ["docker", "exec", CONTAINER_NAME] + py_args

            _current_scan["output"] += f"[GUI] Lancement du scan via docker exec...\n"
            _current_scan["output"] += f"[GUI] URL: {url}\n"
            _current_scan["output"] += f"[GUI] Régions: {regions}\n"
            _current_scan["output"] += f"[GUI] Mode visuel: {'oui (voir http://localhost:6080/)' if visible else 'non'}\n"
            _current_scan["output"] += f"[GUI] Commande: {' '.join(docker_cmd)}\n"
            _current_scan["output"] += f"[GUI] {'='*50}\n\n"

            proc = subprocess.Popen(
                docker_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
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
                if proc.returncode == 1:
                    _current_scan["output"] += (
                        f"[GUI] Astuce: Le conteneur '{CONTAINER_NAME}' doit être démarré.\n"
                        f"[GUI] Lancez: docker compose up -d\n"
                        f"[GUI] Ou cliquez 'Démarrer le conteneur' dans l'interface.\n"
                    )

        except FileNotFoundError:
            _current_scan["output"] += "\n[ERREUR] Docker n'est pas installé ou pas dans le PATH.\n"
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

    return jsonify({"status": "started", "url": url, "regions": regions})


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
    """Check status of the current/last scan."""
    return jsonify({
        "running": _current_scan["running"],
        "url": _current_scan["url"],
        "started_at": _current_scan["started_at"],
        "output": _current_scan["output"][-5000:] if _current_scan["output"] else "",
        "return_code": _current_scan["return_code"]
    })


@app.route("/api/scans/<folder_name>", methods=["DELETE"])
def delete_scan(folder_name):
    """Delete a scan result folder."""
    import shutil
    folder_path = os.path.join(OUTPUT_DIR, folder_name)
    if not os.path.isdir(folder_path):
        abort(404)

    try:
        shutil.rmtree(folder_path)
        return jsonify({"status": "deleted", "folder": folder_name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────── Main ───────────────────────────

if __name__ == "__main__":
    print("  PhishHunter GUI — http://localhost:5000")
    print(f"  Reading scans from: {OUTPUT_DIR}")
    print(f"  Expecting Docker container: {CONTAINER_NAME}")
    print(f"  Start container with: docker compose up -d")
    app.run(host="0.0.0.0", port=5000, debug=True)

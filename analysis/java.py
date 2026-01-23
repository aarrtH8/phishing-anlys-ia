import os
import subprocess
import logging
import zipfile
import shutil

logger = logging.getLogger(__name__)

class JavaForensics:
    def __init__(self, dump_dir: str = "output/dump", cfr_path: str = "tools/cfr.jar"):
        self.dump_dir = dump_dir
        self.cfr_path = cfr_path
        os.makedirs(self.dump_dir, exist_ok=True)

    def analyze_jar(self, content: bytes, filename: str):
        """Saves JAR/Class, decompiles it, and looks for Main-Class."""
        file_path = os.path.join(self.dump_dir, filename)
        
        # 1. Save file
        with open(file_path, "wb") as f:
            f.write(content)
        
        results = {
            "file": filename,
            "is_jar": False,
            "main_class": None,
            "decompilation_status": "skipped"
        }

        # Check if it is a zip (JAR)
        if not zipfile.is_zipfile(file_path):
            # It might be a raw .class file
            # For this task, we focus on JAR processing logic as requested for "Main-Class in Manifest"
            # But we can try to decompile .class too.
            pass
        else:
            results["is_jar"] = True
            # 2. Extract Manifest to find Main-Class
            try:
                with zipfile.ZipFile(file_path, 'r') as zf:
                    if "META-INF/MANIFEST.MF" in zf.namelist():
                        manifest_data = zf.read("META-INF/MANIFEST.MF").decode('utf-8', errors='ignore')
                        for line in manifest_data.splitlines():
                            if "Main-Class:" in line:
                                results["main_class"] = line.split("Main-Class:", 1)[1].strip()
            except Exception as e:
                logger.error(f"Error parsing JAR manifest structure: {e}")

            # 3. Decompile using CFR
            if os.path.exists(self.cfr_path):
                try:
                    # Decompile to a folder
                    output_dir = os.path.join(self.dump_dir, f"{filename}_src")
                    cmd = ["java", "-jar", self.cfr_path, file_path, "--outputdir", output_dir]
                    
                    # Run subprocess
                    process = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                    if process.returncode == 0:
                        results["decompilation_status"] = "success"
                        results["source_path"] = output_dir
                    else:
                        results["decompilation_status"] = "failed"
                        results["error"] = process.stderr
                except Exception as e:
                    results["decompilation_status"] = "error"
                    results["error"] = str(e)
            else:
                results["decompilation_status"] = "cfr_missing"
                logger.warning(f"cfr.jar not found at {self.cfr_path}")

        return results

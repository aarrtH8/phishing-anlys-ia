import logging
import math
import re
import esprima
import jsbeautifier

logger = logging.getLogger(__name__)

class JSAnalysis:
    def __init__(self):
        self.opts = jsbeautifier.default_options()
        self.opts.indent_size = 4

    def analyze_js(self, content: bytes, filename: str):
        """Analyzes JS content for obfuscation indicators and dangerous patterns."""
        try:
            js_text = content.decode('utf-8', errors='ignore')
        except:
            return {"file": filename, "error": "binary_content"}

        results = {
            "file": filename,
            "entropy_score": 0.0,
            "suspicious_functions": [],
            "obfuscation_detected": False,
            "hex_strings": 0,
            "deobfuscated_preview": None
        }

        # 1. AST Analysis
        try:
            tree = esprima.parseScript(js_text)
            
            def traverse(node):
                if node.type == 'CallExpression':
                    if node.callee.type == 'Identifier':
                        name = node.callee.name
                        if name in ['eval', 'unescape', 'setTimeout', 'setInterval']:
                            if name not in results["suspicious_functions"]:
                                results["suspicious_functions"].append(name)
                    # Check for document.write
                    elif node.callee.type == 'MemberExpression':
                        if hasattr(node.callee.object, 'name') and node.callee.object.name == 'document':
                             if hasattr(node.callee.property, 'name') and node.callee.property.name == 'write':
                                 if "document.write" not in results["suspicious_functions"]:
                                     results["suspicious_functions"].append("document.write")

                for key, value in node.items():
                    if hasattr(value, 'type'):
                        traverse(value)
                    elif isinstance(value, list):
                        for item in value:
                            if hasattr(item, 'type'):
                                traverse(item)

            traverse(tree)

        except Exception as e:
            # logger.warning(f"AST Parsing failed for {filename}: {e}") # Reduce noise
            # Fallback to Regex
            if re.search(r'eval\(', js_text): results["suspicious_functions"].append("eval")
            if re.search(r'document\.write\(', js_text): results["suspicious_functions"].append("document.write")
            if re.search(r'unescape\(', js_text): results["suspicious_functions"].append("unescape")

        # 2. Entropy Analysis
        strings = re.findall(r'([\'"])(.*?)\1', js_text)
        max_entropy = 0
        for _, s in strings:
            if re.match(r'(\\x[0-9a-fA-F]{2})+', s):
                results["hex_strings"] += 1
            
            e = self._shannon_entropy(s)
            if e > max_entropy:
                max_entropy = e
        
        results["entropy_score"] = max_entropy
        if max_entropy > 4.5 or results["hex_strings"] > 10:
            results["obfuscation_detected"] = True
            
            # DEOBFUSCATION Attempt
            try:
                beautified = jsbeautifier.beautify(js_text, self.opts)
                # Simple Hex Decode (naive)
                def hex_repl(match):
                    try: return bytes.fromhex(match.group(0).replace('\\x','')).decode('utf-8')
                    except: return match.group(0)
                
                decoded = re.sub(r'(\\x[0-9a-fA-F]{2})+', hex_repl, beautified)
                results["deobfuscated_preview"] = decoded[:2000] # Return first 2000 chars
            except Exception as e:
                results["deobfuscated_preview"] = f"Deobfuscation failed: {e}"

        if len(re.findall(r'\\x[0-9a-fA-F]{2}', js_text)) > 50:
            results["obfuscation_detected"] = True

        return results

    def _shannon_entropy(self, data):
        if not data:
            return 0
        entropy = 0
        for x in range(256):
            p_x = float(data.count(chr(x))) / len(data)
            if p_x > 0:
                entropy += - p_x * math.log(p_x, 2)
        return entropy

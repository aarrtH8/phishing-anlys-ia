"""
core/threat_intel.py
====================
Threat Intelligence module for PhishHunter.
Aggregates data from multiple sources:
  - VirusTotal (URL reputation, optional — requires VT_API_KEY env var)
  - RDAP / Whois (domain registration date, registrar, age)
  - SSL Certificate (validity, issuer, self-signed detection)
"""

import os
import ssl
import socket
import json
import logging
import requests
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ThreatIntelligence:
    def __init__(self, vt_api_key: str = None):
        self.vt_api_key = vt_api_key or os.getenv("VT_API_KEY", "")

    def analyze(self, url: str) -> dict:
        """Run all threat intelligence checks and return a unified dict."""
        parsed = urlparse(url)
        domain = parsed.netloc.split(":")[0]

        result = {
            "domain": domain,
            "virustotal": None,
            "whois": None,
            "ssl": None,
        }

        if self.vt_api_key:
            logger.info(f"[ThreatIntel] Running VirusTotal check for: {url}")
            result["virustotal"] = self._check_virustotal(url)
        else:
            result["virustotal"] = {"skipped": True, "reason": "VT_API_KEY not set"}

        logger.info(f"[ThreatIntel] RDAP Whois lookup for: {domain}")
        result["whois"] = self._check_whois_rdap(domain)

        logger.info(f"[ThreatIntel] SSL certificate check for: {domain}")
        result["ssl"] = self._check_ssl(domain)

        return result

    # ──────────────────────────────────────────────────────────────
    # VirusTotal
    # ──────────────────────────────────────────────────────────────
    def _check_virustotal(self, url: str) -> dict:
        headers = {"x-apikey": self.vt_api_key}
        try:
            # Submit URL
            resp = requests.post(
                "https://www.virustotal.com/api/v3/urls",
                headers=headers,
                data={"url": url},
                timeout=20,
            )
            if resp.status_code not in (200, 201):
                return {"error": f"VT submission HTTP {resp.status_code}"}

            analysis_id = resp.json()["data"]["id"]

            # Poll for result (max 5 attempts, 3s apart)
            for attempt in range(5):
                time.sleep(3)
                resp2 = requests.get(
                    f"https://www.virustotal.com/api/v3/analyses/{analysis_id}",
                    headers=headers,
                    timeout=20,
                )
                if resp2.status_code != 200:
                    continue
                data = resp2.json()["data"]
                status = data["attributes"].get("status", "")
                if status == "completed":
                    stats = data["attributes"]["stats"]
                    total = sum(stats.values()) or 1
                    malicious = stats.get("malicious", 0)
                    suspicious = stats.get("suspicious", 0)
                    return {
                        "malicious": malicious,
                        "suspicious": suspicious,
                        "harmless": stats.get("harmless", 0),
                        "undetected": stats.get("undetected", 0),
                        "total": total,
                        "detection_rate": round((malicious + suspicious) / total * 100, 1),
                        "permalink": f"https://www.virustotal.com/gui/url/{analysis_id}",
                    }

            return {"error": "VT analysis timed out (not completed after 5 attempts)"}
        except Exception as e:
            logger.error(f"[ThreatIntel] VirusTotal error: {e}")
            return {"error": str(e)}

    # ──────────────────────────────────────────────────────────────
    # RDAP / Whois
    # ──────────────────────────────────────────────────────────────
    # Known second-level components used before country-code TLDs (e.g. .co.uk, .com.au)
    _SECONDARY_TLDS = {"co", "com", "net", "org", "gov", "edu", "ac", "me", "ltd", "plc",
                       "mod", "sch", "police", "nhs", "gen", "firm", "web", "biz", "info"}
    _COUNTRY_CODES  = {"uk", "jp", "nz", "za", "au", "br", "in", "sg", "my", "hk",
                       "id", "ph", "th", "vn", "mx", "ar", "cl", "pe", "ve", "ec"}

    def _check_whois_rdap(self, domain: str) -> dict:
        # Strip to registrable domain — handle multi-label TLDs like .co.uk, .com.au
        parts = domain.split(".")
        if (len(parts) >= 3
                and parts[-1] in self._COUNTRY_CODES
                and parts[-2] in self._SECONDARY_TLDS):
            registrable = ".".join(parts[-3:])
        elif len(parts) >= 2:
            registrable = ".".join(parts[-2:])
        else:
            registrable = domain

        rdap_servers = [
            f"https://rdap.org/domain/{registrable}",
            f"https://rdap.iana.org/domain/{registrable}",
        ]

        data = None
        for url in rdap_servers:
            try:
                resp = requests.get(
                    url,
                    timeout=10,
                    headers={"Accept": "application/rdap+json, application/json"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    break
            except Exception:
                continue

        if data is None:
            return {"domain": registrable, "error": "RDAP lookup failed (all servers)"}

        # Parse events
        reg_date = None
        expiry_date = None
        updated_date = None
        for event in data.get("events", []):
            action = event.get("eventAction", "").lower()
            date_str = event.get("eventDate", "")
            if action == "registration":
                reg_date = date_str
            elif action in ("expiration", "expiry"):
                expiry_date = date_str
            elif action == "last changed":
                updated_date = date_str

        # Domain age
        domain_age_days = None
        if reg_date:
            try:
                reg_dt = datetime.fromisoformat(reg_date.replace("Z", "+00:00"))
                domain_age_days = (datetime.now(timezone.utc) - reg_dt).days
            except Exception:
                pass

        # Registrar
        registrar = None
        for entity in data.get("entities", []):
            if "registrar" in entity.get("roles", []):
                vcard = entity.get("vcardArray", [])
                if vcard and len(vcard) > 1:
                    for field in vcard[1]:
                        if field[0] == "fn":
                            registrar = field[3]
                            break
                if not registrar:
                    registrar = entity.get("handle")

        status = data.get("status", [])

        return {
            "domain": registrable,
            "registration_date": reg_date,
            "expiry_date": expiry_date,
            "updated_date": updated_date,
            "age_days": domain_age_days,
            "registrar": registrar,
            "status": status,
            "is_young": domain_age_days is not None and domain_age_days < 30,
            "is_very_young": domain_age_days is not None and domain_age_days < 7,
        }

    # ──────────────────────────────────────────────────────────────
    # SSL Certificate
    # ──────────────────────────────────────────────────────────────
    def _check_ssl(self, domain: str) -> dict:
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=8) as raw_sock:
                with ctx.wrap_socket(raw_sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()

            # Parse fields
            issuer = {k: v for pair in cert.get("issuer", []) for k, v in pair}
            subject = {k: v for pair in cert.get("subject", []) for k, v in pair}
            san = [v for _, v in cert.get("subjectAltName", [])]
            not_after = cert.get("notAfter", "")

            # Days left
            days_left = None
            is_expired = False
            try:
                expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(
                    tzinfo=timezone.utc
                )
                days_left = (expiry - datetime.now(timezone.utc)).days
                is_expired = days_left < 0
            except Exception:
                pass

            issuer_org = issuer.get(
                "organizationName", issuer.get("O", issuer.get("commonName", "Unknown"))
            )
            subject_cn = subject.get("commonName", domain)

            is_lets_encrypt = "Let's Encrypt" in issuer_org or "Let's Encrypt" in issuer.get("commonName", "")
            is_self_signed = (
                issuer.get("commonName") == subject_cn
                and not is_lets_encrypt
                and issuer.get("organizationName") == subject.get("organizationName")
            )

            return {
                "valid": not is_expired,
                "issuer": issuer_org,
                "issuer_cn": issuer.get("commonName", ""),
                "subject_cn": subject_cn,
                "not_after": not_after,
                "days_left": days_left,
                "is_expired": is_expired,
                "is_lets_encrypt": is_lets_encrypt,
                "is_self_signed": is_self_signed,
                "san": san[:8],
                "san_count": len(san),
            }

        except ssl.SSLCertVerificationError as e:
            return {"valid": False, "error": "Cert verification failed", "details": str(e)}
        except (ConnectionRefusedError, OSError):
            return {"valid": None, "error": "No HTTPS / port 443 unreachable"}
        except Exception as e:
            logger.warning(f"[ThreatIntel] SSL check error for {domain}: {e}")
            return {"valid": None, "error": str(e)}


# ──────────────────────────────────────────────────────────────────────────────
# Unified Risk Score
# ──────────────────────────────────────────────────────────────────────────────
def compute_risk_score(report_data: dict, threat_intel: dict = None) -> dict:
    """
    Compute a unified 0-100 risk score from all analysis signals.
    Returns: {"score": int, "level": str, "factors": list[str]}
    """
    score = 0
    factors = []
    ti = threat_intel or {}

    # ── VirusTotal ──
    vt = ti.get("virustotal") or {}
    if not vt.get("skipped") and not vt.get("error"):
        malicious = vt.get("malicious", 0)
        suspicious = vt.get("suspicious", 0)
        if malicious >= 10:
            pts = 40
        elif malicious >= 5:
            pts = 30
        elif malicious >= 1:
            pts = 20
        elif suspicious >= 1:
            pts = 10
        else:
            pts = 0
        if pts:
            score += pts
            factors.append(f"VirusTotal: {malicious} malicieux, {suspicious} suspects (+{pts})")

    # ── Domain Age ──
    whois = ti.get("whois") or {}
    age = whois.get("age_days")
    if age is not None and not whois.get("error"):
        if age < 3:
            pts, label = 30, "< 3 jours"
        elif age < 7:
            pts, label = 25, "< 7 jours"
        elif age < 30:
            pts, label = 15, "< 30 jours"
        elif age < 90:
            pts, label = 5, "< 90 jours"
        else:
            pts, label = 0, ""
        if pts:
            score += pts
            factors.append(f"Domaine très récent ({age} j, {label}) (+{pts})")

    # ── SSL ──
    ssl_data = ti.get("ssl") or {}
    if ssl_data:
        if ssl_data.get("is_self_signed"):
            score += 15
            factors.append("Certificat SSL auto-signé (+15)")
        elif ssl_data.get("is_expired"):
            score += 10
            factors.append("Certificat SSL expiré (+10)")
        elif ssl_data.get("valid") is False and not ssl_data.get("is_self_signed"):
            score += 10
            factors.append("Certificat SSL invalide (+10)")
        elif ssl_data.get("valid") is None:
            score += 5
            factors.append("Pas de HTTPS détecté (+5)")

    # ── Redirect Chain ──
    chain = report_data.get("redirect_chain", [])
    if len(chain) > 5:
        score += 15
        factors.append(f"Chaîne de {len(chain)} redirections (+15)")
    elif len(chain) > 2:
        score += 8
        factors.append(f"Chaîne de {len(chain)} redirections (+8)")

    # ── Sensitive Form Fields ──
    inputs = report_data.get("inputs", [])
    input_types = {str(i.get("type", "")).lower() for i in inputs}
    sensitive_overlap = input_types & {"password", "credit_card", "otp"}
    if sensitive_overlap:
        score += 20
        factors.append(f"Formulaires sensibles détectés: {', '.join(sensitive_overlap)} (+20)")
    elif inputs:
        score += 8
        factors.append(f"{len(inputs)} champs de saisie détectés (+8)")

    # ── JS Obfuscation (continuous entropy contribution) ──
    files = report_data.get("files_extracted", [])
    obfuscated = 0
    max_entropy = 0.0
    for f in files:
        analysis = f.get("analysis", {})
        if analysis.get("obfuscation_detected"):
            obfuscated += 1
        entropy = float(analysis.get("entropy_score", 0) or 0)
        if entropy > max_entropy:
            max_entropy = entropy
    if obfuscated:
        # 10 pts base + up to 10 pts from entropy (typical range 3.0–6.5, capped at 6.5)
        entropy_bonus = min(10, round((max_entropy / 6.5) * 10))
        pts = 10 + entropy_bonus
        score += pts
        factors.append(f"Obfuscation JS ({obfuscated} fichier(s), entropie max {max_entropy:.2f}) (+{pts})")
    elif max_entropy > 5.0:
        # High entropy without explicit flag is still suspicious
        pts = 5
        score += pts
        factors.append(f"Entropie JS élevée ({max_entropy:.2f}) (+{pts})")

    # ── Journey Depth ──
    journey = report_data.get("interaction_journey", [])
    depth = len(journey)
    if depth >= 10:
        pts = 10
    elif depth >= 5:
        pts = 5
    elif depth >= 3:
        pts = 3
    else:
        pts = 0
    if pts:
        score += pts
        factors.append(f"Parcours en profondeur ({depth} étapes) (+{pts})")

    # ── Visual Brand Impersonation ──
    visual = report_data.get("visual_analysis", {})
    if visual.get("brand_detected"):
        score += 10
        factors.append(f"Usurpation visuelle: {visual['brand_detected']} (+10)")

    score = min(100, score)

    if score >= 75:
        level = "critical"
    elif score >= 50:
        level = "high"
    elif score >= 25:
        level = "medium"
    else:
        level = "low"

    return {"score": score, "level": level, "factors": factors}

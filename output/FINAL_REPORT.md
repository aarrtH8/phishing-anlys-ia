# 🕵️ PhishHunter Final Forensic Report

**Target**: `https://storage.googleapis.com/salesflow25/eranewmar.html#?Z289MSZzMT0yMjI2NDMxJnMyPTYwOTc4MDkyNSZzMz1HTEI=`
**Scan Time**: 2026-01-22 08:33:01 UTC

## 🧠 AI Forensic Analysis
**Analysis Unavailable**: Could not connect to local Ollama instance (404 Client Error: Not Found for url: http://localhost:11434/api/generate). Please ensure 'ollama serve' is running.

## 🕹️ Deep Agentic Analysis (User Journey)
The automated engine performed a deep dive, simulating a victim's complete path to the payload. Below is the step-by-step analysis performed by the AI Agent.

### Step 1: Initial Page Load (AI Suspicion: ?%)
**URL**: `https://cesarsgadgets.info/?sub5=35398&source_id=21003&encoded_value=223GDT1&sub1=5b1ce6d9ee034097b022e36b903e79a1&sub2=&sub3=&sub4=&sub5=35398&source_id=21003&domain=www.babosur.com&ip=176.182.162.128`

> 🤖 **Agent Insight**: The attacker in this phishing interaction appears to be attempting to deceive users and extract sensitive information. They are using a URL disguised as `cesarsgadgets.info` to lure victims, while the actual domain being targeted is `www.babosur.com`. This suggests that the attacker is creating a fraudulent page with the intent of mimicking a legitimate site to phish for user data.

![Step 1](screenshot_US_step_00_initial.png)

---
## 🌍 Regional Analysis
### Region: US
![Screenshot US](screenshot_US.png)

**Redirect Chain:**
1. `http://185.80.128.102/??Z289MSZzMT0yMjI2NDMxJnMyPTYwOTc4MDkyNSZzMz1HTEI=` (302)
2. `http://185.80.128.102/public/?:nav=default::index&go=1&s1=2226431&s2=609780925` (302)
3. `http://185.80.128.102/?var=Om5hdj1jbGljazo6dHJhY2tlciZkZXBsb3k9MjIyNjQzMSZ1c2VyPWR5bGFuLmRyZXZvdDElNDBnbWFpbC5jb20mZW1haWxfaWQ9NjA5NzgwOTI1JnVybD1hSFIwY0hNNkx5OTNkM2N1Y205d2JHRmxjeTVqYjIwdk1qY3lTRkpYVVVvdk4wbzFUa1pDVkRJdlAzTnZkWEpqWlY5cFpEMHlNakkyTkRNeExVRk1URjlGVEV0TlFWSmZRMEZHWDBkTlFVbE1YMFpTWDFBeUxUUTVNamc0TXlaemRXSXhQVFl3T1RjNE1Ea3lOVjgwT1RJNE9USmZNZz09` (302)
4. `http://185.80.128.102/public/?:nav=click::tracker&deploy=2226431&user=dylan.drevot1%40gmail.com&email_id=609780925&url=aHR0cHM6Ly93d3cucm9wbGFlcy5jb20vMjcySFJXUUovN0o1TkZCVDIvP3NvdXJjZV9pZD0yMjI2NDMxLUFMTF9FTEtNQVJfQ0FGX0dNQUlMX0ZSX1AyLTQ5Mjg4MyZzdWIxPTYwOTc4MDkyNV80OTI4OTJfMg==` (302)
5. `https://www.roplaes.com/272HRWQJ/7J5NFBT2/?source_id=2226431-ALL_ELKMAR_CAF_GMAIL_FR_P2-492883&sub1=609780925_492892_2` (302)
6. `https://www.babosur.com/2W1Q1KK/37NKZJSM/?sub1=5b1ce6d9ee034097b022e36b903e79a1&source_id=21003&sub5=103409` (302)
7. `https://cesarsgadgets.info/jkgW7Hpz/?sub5=35398&source_id=21003&encoded_value=223GDT1&sub1=5b1ce6d9ee034097b022e36b903e79a1&sub2=&sub3=&sub4=&sub5=35398&source_id=21003&domain=www.babosur.com&ip=176.182.162.128` (302)
8. `http://cesarsgadgets.info/?sub5=35398&source_id=21003&encoded_value=223GDT1&sub1=5b1ce6d9ee034097b022e36b903e79a1&sub2=&sub3=&sub4=&sub5=35398&source_id=21003&domain=www.babosur.com&ip=176.182.162.128` (307)
9. `https://storage.googleapis.com/salesflow25/eranewmar.html` (200)

**Data Collection detected**: 1 inputs found.
---

## 📦 Artifacts & Obfuscation
### JAVASCRIPT: `https://pushstar.work/ace-push.min.js`

### JAVASCRIPT: `https://cesarsgadgets.info/js/setting.js`
> ⚠️ **Obfuscation Detected**
> Entropy: 4.77
#### Deobfuscated Preview:
```javascript
function datehax() {
    const mydate = new Date();
    mydate.setDate(mydate.getDate());
    let year = mydate.getFullYear(); // Use getFullYear instead of getYear
    let day = mydate.getDay();
    let month = mydate.getMonth();
    let daym = mydate.getDate();

    if (daym < 10) {
        daym = "0" + daym;
    }

    const dayarray = ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"];
    const montharray = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"];

    return `${montharray[month]} ${daym}, ${year}`;
}

function datenhax() {
    const mydate = new Date();
    mydate.setDate(mydate.getDate());
    let year = mydate.getFullYear(); // Use getFullYear instead of get
...
```

### JAVASCRIPT: `https://use.fontawesome.com/releases/v5.15.4/js/all.js`
> ⚠️ **Obfuscation Detected**
> Entropy: 5.95
#### Deobfuscated Preview:
```javascript
/*!
 * Font Awesome Free 5.15.4 by @fontawesome - https://fontawesome.com
 * License - https://fontawesome.com/license/free (Icons: CC BY 4.0, Fonts: SIL OFL 1.1, Code: MIT License)
 */
! function() {
    "use strict";
    var c = {},
        l = {};
    try {
        "undefined" != typeof window && (c = window), "undefined" != typeof document && (l = document)
    } catch (c) {}
    var h = (c.navigator || {}).userAgent,
        a = void 0 === h ? "" : h,
        z = c,
        v = l,
        m = (z.document, !!v.documentElement && !!v.head && "function" == typeof v.addEventListener && v.createElement, ~a.indexOf("MSIE") || a.indexOf("Trident/"), "___FONT_AWESOME___"),
        e = function() {
            try {
                return !0
            } catch (c) {
                return !1

...
```


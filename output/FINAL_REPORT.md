# 🕵️ PhishHunter Final Forensic Report

**Target**: `https://storage.googleapis.com/mastfox/masterxifo.html#4xlWqN70646FTvW621wykqvlobuw1133XXFRTYQVPVDZSWR102193WYWG39118I25`
**Scan Time**: 2026-01-23 13:37:46 UTC

## 🧠 AI Forensic Analysis
 **Forensic Report**

**1. Evidence-Based Analysis**

The initial page load (`step_00_initial`) indicates the user is directed to a domain `treskiva.online`, which further redirects the user to the final URL of interest (`https://herbnetpl.com/click.php...`) in `step_04_payload`. This redirection chain and suspicious URL pattern are clear indicators of a phishing attempt.

Upon reaching `step_04_payload`, a payload is detected containing reward promises and suspicious redirects, further reinforcing the assumption that this is a phishing scam.

**2. Technique Explanation**

The JavaScript file `datehead.js` found at `https://treskiva.online/vinci_autoroutes/assets//datehead.js` is obfuscated and contains multiple date-related functions such as `setInterval`, which could be used for time-limited actions or payload delivery (e.g., redirecting the victim to a malicious site after a specific time). This technique is employed to make the phishing attempt appear more legitimate, misleading victims into disclosing sensitive information.

**3. Severity**

The identified phishing scam represents a high severity threat due to its potential for data theft and unauthorized access. The use of obfuscated JavaScript code further increases the danger as it can be utilized for various malicious activities such as payload delivery, social engineering, or even data manipulation. It is crucial that users are made aware of this threat and advised to avoid interacting with suspicious links or websites.

## 🕹️ Deep Agentic Analysis (User Journey)
The automated engine performed a deep dive, simulating a victim's complete path to the payload. Below is the step-by-step analysis performed by the AI Agent.

### Step 1: Initial Page Load (AI Suspicion: 60%)
**URL**: `https://treskiva.online/vinci_autoroutes/index.php?device_name=Unknown&browser_name=Chrome&language=en-US&city=La%20Tronche&clickid=d5pnijae7qoc739dtvag&campaign=7704&user_id=1&clickcost=0&lander=2600&time=1769175373&browser_version=120.0.0&device_model=Unknown&device_brand=Unknown&resolution=Unknown&os_name=Windows&os_version=10&country=France&country_code=FR&isp=SIMSU&ip=130.190.116.188&user_agent=Mozilla/5.0%20(Windows%20NT%2010.0%20Win64%20x64)%20AppleWebKit/537.36%20(KHTML,%20like%20Gecko)%20Chrome/120.0.0.0%20Safari/537.36&lpkey=1769140a5ed445bde6d3bf27a1a182385b65975573&target=&device=DESKTOP&country=US&ts=&trafficsource=113&domain=herbnetpl.com#`

> 🤖 **Agent Insight**: The attacker is attempting to build trust by creating a phishing page that mimics a legitimate website (Vinci Autoroutes), likely with the intention of extracting user credentials or personal data.

![Step 1](screenshot_US_step_00_initial.png)

---
### Step 2: [PAYLOAD DETECTED] ['Reward promises', 'Suspicious redirects or URL patterns']
**URL**: `https://treskiva.online/vinci_autoroutes/index.php?device_name=Unknown&browser_name=Chrome&language=en-US&city=La%20Tronche&clickid=d5pnijae7qoc739dtvag&campaign=7704&user_id=1&clickcost=0&lander=2600&time=1769175373&browser_version=120.0.0&device_model=Unknown&device_brand=Unknown&resolution=Unknown&os_name=Windows&os_version=10&country=France&country_code=FR&isp=SIMSU&ip=130.190.116.188&user_agent=Mozilla/5.0%20(Windows%20NT%2010.0%20Win64%20x64)%20AppleWebKit/537.36%20(KHTML,%20like%20Gecko)%20Chrome/120.0.0.0%20Safari/537.36&lpkey=1769140a5ed445bde6d3bf27a1a182385b65975573&target=&device=DESKTOP&country=US&ts=&trafficsource=113&domain=herbnetpl.com#`

> 🤖 **Agent Insight**: The attacker in this phishing interaction is attempting to extract data by luring the user into clicking a suspicious URL disguised as Vinci Autoroutes, a French toll motorway company. This URL collects various user details such as IP address, user agent, and country information, likely for malicious purposes like account hijacking or identity theft.

![Step 2](screenshot_US_step_04_payload.png)

---
## 🌍 Regional Analysis
### Region: US
![Screenshot US](screenshot_US.png)

**Redirect Chain:**
1. `https://storage.googleapis.com/mastfox/masterxifo.html` (200)
2. `https://www.eartrissin.com/RMrDkPvluRG2tvvd5hGmOzti5AEBU7yLOyFj82TrP-psl-n1trLvwjpwZpPKQBw9EFMw-S21CO6mVP-svOj8kQ~~/25/621-70646/1133-102193-39118` (302)
3. `https://herbnetpl.com/click.php?key=dme69t4zaj0e1tgbp9cb&clickid=836915393&subid=823400` (307)

**Data Collection detected**: 1 inputs found.
---

## 📦 Artifacts & Obfuscation
### JAVASCRIPT: `https://treskiva.online/vinci_autoroutes/assets//datehead.js`
> 🧠 **AI Analysis**: This JavaScript file appears to contain multiple date-related functions. The primary purpose seems to be obfuscation and potentially data manipulation.

1. The `datehax()` function returns a formatted string of the current date using localized day and month names, while `datenhax()` returns the date in the format "dd/mm/yyyy". Both seem to be used for obfuscation purposes.

2. The `startTimer(duration, display)` function uses a timer that decrements every second, which could potentially be utilized for a time-limited action or payload delivery (e.g., redirecting the victim to a malicious site after a specific time). However, this function is not called anywhere in the provided code snippet, so it's unclear if it serves any malicious purpose.

3. This script tries to manipulate dates and potentially mislead victims into believing they are dealing with legitimate content. Depending on its implementation, it could be used for various malicious activities such as phishing, social engineering, or even payload delivery (via redirect).

### JAVASCRIPT: `https://code.jquery.com/jquery-1.11.1.min.js`
> ⚠️ **Obfuscation Detected**
> Entropy: 5.51
> 🧠 **AI Analysis**: 1. The purpose of this JavaScript file is to mimic the jQuery library (version 1.11.1) as a disguise for malicious activity. It uses obfuscation techniques to conceal its true intent.

2. Dangerous functions within this script include those related to manipulating the DOM (document object model), such as `each`, `map`, `first`, `last`, and `eq`. These functions can be used for various malicious activities like form grabbing, cookie theft, or redirecting users to phishing sites.

3. This script, when executed on a victim's browser, attempts to interact with the webpage DOM (document object model). By manipulating the page's elements and potentially stealing sensitive data, it can contribute to a broader attack, such as identity theft or unauthorized access.
#### Deobfuscated Preview:
```javascript
/*! jQuery v1.11.1 | (c) 2005, 2014 jQuery Foundation, Inc. | jquery.org/license */ ! function(a, b) {
    "object" == typeof module && "object" == typeof module.exports ? module.exports = a.document ? b(a, !0) : function(a) {
        if (!a.document) throw new Error("jQuery requires a window with a document");
        return b(a)
    } : b(a)
}("undefined" != typeof window ? window : this, function(a, b) {
    var c = [],
        d = c.slice,
        e = c.concat,
        f = c.push,
        g = c.indexOf,
        h = {},
        i = h.toString,
        j = h.hasOwnProperty,
        k = {},
        l = "1.11.1",
        m = function(a, b) {
            return new m.fn.init(a, b)
        },
        n = /^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g,
        o = /^-ms-/,
        p = /-([\da-z])/gi,
 
...
```

### JAVASCRIPT: `https://treskiva.online/vinci_autoroutes/assets//script.js`
> 🧠 **AI Analysis**: 1. This JavaScript file is designed for user interaction on a phishing site, obfuscated to hide its true purpose.
2. The script manipulates DOM elements (e.g., `document.getElementsByClassName`, `querySelectorAll`) and adds animations using the Animate.css library for a smoother user experience. A specific dangerous function could be `toNext()`, which hides previous question sections and reveals next ones.
3. Upon victim interaction, this script navigates through a sequence of questions on the phishing site, gradually revealing new content while hiding the previous one. The ultimate goal is to collect sensitive information from the user.

### JAVASCRIPT: `https://treskiva.online/redirect_bin_withoutcomm.js`
> ⚠️ **Obfuscation Detected**
> Entropy: 4.82
> 🧠 **AI Analysis**: This JavaScript file is designed for a variety of purposes within a phishing site, including manipulation and obfuscation of user interface elements.

1. The primary purpose appears to be redirection: It extracts the domain from the URL query string (`$_GET('domain')`) and constructs a redirect URL (`redirect_url`). This is likely used to direct victims to a malicious server for further data theft or exploitation.
2. The script also manipulates specific DOM elements, replacing certain text within messages ("For your chance to claim your reward" and "You’ve been chosen for the chance to receive a brand new") and changing the thank-you text ("Please don’t leave this page as products are limited"). This could be an attempt to make the phishing site more convincing and enticing to victims.
3. By manipulating the user interface, setting a slower setTimeout (`window.setTimeout = function(fn, t) { return originalSetTimeout(fn, t / 2); }`) and redirecting users to malicious servers, this script attempts to deceive victims into providing sensitive information or downloading additional malware.
#### Deobfuscated Preview:
```javascript
function $_GET(key) {
    var s = decodeURIComponent(window.location.search);
    s = s.match(new RegExp(key + '=([^&=]+)'));
    return s ? s[1] : false;
}
var dmn = $_GET('domain');
var redirect_url = 'https://' + dmn + '/click.php?lp=1';
var back_url_link = 'https://' + dmn + '/click.php?key=';
var
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
    time = ["12:01 am", "2:24 pm", "11:55 am", "8:47 am", "6:16 pm", "4:16 pm", "6:48 pm", "17:07"],
    d = new Date(),
    dateNow = months[d.getMonth()] + " " + d.getDate() + ", " + d.getFullYear();
if ($('.message').length) {
    var el = $('.message');
    el.html
...
```

### JAVASCRIPT: `https://treskiva.online/vinci_autoroutes/assets//all.js`
> ⚠️ **Obfuscation Detected**
> Entropy: 5.95
> 🧠 **AI Analysis**: 1. The purpose of this JavaScript file is to deliver a potentially malicious payload disguised as Font Awesome Free 5.15.4 library, exploiting the trust users have in popular libraries for web development. This script uses obfuscation techniques and attempts to execute code by manipulating the browser environment.

2. The function `M()` is responsible for either adding styles or hooking into Font Awesome's existing pack system. The usage of `h = void 0 === l && l` as a conditional check, which evaluates to `true` when the variable `l` is `undefined`, suggests bypassing certain checks or security measures in place.

3. This script tries to infect the victim's web browser with malicious code disguised as Font Awesome library. Once executed, it could potentially alter the appearance of websites visited by the user, deliver additional malware, or harvest sensitive data for unauthorized use.
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


import os
import requests
import logging

logging.basicConfig(level=logging.INFO)

def download_file(url, path):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    print(f"Downloading {url} to {path}...")
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        response = requests.get(url, headers=headers, stream=True, verify=False)
        response.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Success.")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

def main():
    # Tools
    # Attempt to download CFR. If BENF blocks, we might need a mirror or github release.
    # Trying github release for CFR if BENF fails might be an option, but let's try BENF with headers.
    download_file("https://www.benf.org/other/cfr/cfr-0.152.jar", "tools/cfr.jar")
    
    # Logos
    logos = {
        "google": "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png",
        "microsoft": "https://img-prod-cms-rt-microsoft-com.akamaized.net/cms/api/am/imageFileData/RE1Mu3b?ver=5c31", 
        "paypal": "https://www.paypalobjects.com/webstatic/mktg/logo/pp_cc_mark_111x69.jpg"
    }
    
    for name, url in logos.items():
        ext = url.split('.')[-1]
        if len(ext) > 4: ext = "png"
        path = f"resources/logos/{name}.{ext}"
        download_file(url, path)

if __name__ == "__main__":
    main()

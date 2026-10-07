import os
import urllib.request

fonts = {
    "CourierPrime-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/courierprime/CourierPrime-Regular.ttf",
    "EBGaramond-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/ebgaramond/static/EBGaramond-Regular.ttf",
    "Caveat-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/caveat/static/Caveat-Regular.ttf"
}

base_dir = os.path.dirname(os.path.abspath(__file__))

for filename, url in fonts.items():
    filepath = os.path.join(base_dir, filename)
    if not os.path.exists(filepath):
        print(f"Downloading {filename}...")
        try:
            urllib.request.urlretrieve(url, filepath)
        except Exception as e:
            print(f"Failed to download {filename}: {e}")
print("Fonts ready.")

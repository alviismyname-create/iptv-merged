import re
import sys
from collections import OrderedDict

INPUT_FILE = "merged.m3u"
OUTPUT_FILE = "output.m3u"

# --- PROTECTED GROUPS (These will NOT be re-categorized) ---
PROTECTED_GROUPS = ["Malayalam", "Tamil"]

# --- FILTER (Adult/NSFW) ---
FILTER_KEYWORDS = ["xxx", "adult", "18+", "porn", "sex", "fuck", "hardcore"]

# --- CATEGORY MAPPING for the OTHER 3 SOURCES ---
CATEGORY_MAP = {
    "News": ["cnn", "bbc", "sky news", "al jazeera", "fox news", "msnbc", "ndtv", "times now", "republic"],
    "Sports": ["espn", "sky sports", "nfl", "nba", "bein", "dazn", "moto gp", "f1", "formula", "cricket", "ipl"],
    "Movies": ["hbo", "starz", "cinemax", "amc", "paramount", "film", "movie", "cinema"],
    "Entertainment": ["mtv", "comedy", "discovery", "national geographic", "tlc", "e!", "vice"],
    "Music": ["stingray", "radio", "mtv live", "vivid", "music"],
    "Kids": ["cartoon", "disney", "nickelodeon", "paw patrol", "boomerang", "child"],
    "Documentary": ["nat geo", "history", "bbc earth", "documentary", "science"],
    "US Local": ["abc", "nbc", "cbs", "fox", "cw", "pbs", "usa", "us"],
}

def categorize_channel(name):
    name_lower = name.lower()
    for category, keywords in CATEGORY_MAP.items():
        for kw in keywords:
            if kw in name_lower:
                return category
    return "Uncategorized"

def is_filtered(name):
    name_lower = name.lower()
    for kw in FILTER_KEYWORDS:
        if kw in name_lower:
            return True
    return False

def parse_m3u(filepath):
    channels = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            extinf = line
            if i + 1 < len(lines):
                url = lines[i + 1].strip()
                if url.startswith("http"):
                    channels.append((extinf, url))
                i += 2
            else:
                i += 1
        else:
            i += 1
    return channels

def get_existing_group(extinf):
    match = re.search(r'group-title="([^"]*)"', extinf)
    return match.group(1) if match else None

def build_m3u(channels):
    # 1. Remove duplicates by URL
    seen_urls = OrderedDict()
    for extinf, url in channels:
        if url not in seen_urls:
            seen_urls[url] = extinf

    processed = []
    for url, extinf in seen_urls.items():
        if ',' in extinf:
            name = extinf.split(',')[-1].strip()
        else:
            name = "Unknown"

        if is_filtered(name):
            continue

        existing_group = get_existing_group(extinf)
        if existing_group in PROTECTED_GROUPS:
            # Keep Malayalam and Tamil exactly as they are
            processed.append((extinf, url, name, existing_group))
        else:
            # Categorize the other sources
            extinf_cleaned = re.sub(r'group-title="[^"]*"', '', extinf)
            category = categorize_channel(name)

            if 'tvg-logo="' in extinf_cleaned:
                extinf_new = extinf_cleaned.replace('tvg-logo="', f'tvg-logo="" group-title="{category}"', 1)
            else:
                extinf_new = extinf_cleaned.replace('#EXTINF:', f'#EXTINF: group-title="{category}"', 1)

            extinf_new = re.sub(r'\s+', ' ', extinf_new)
            processed.append((extinf_new, url, name, category))

    processed.sort(key=lambda x: x[2].lower())
    return processed

def write_m3u(output_path, channels):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for extinf, url, _, _ in channels:
            f.write(extinf + "\n")
            f.write(url + "\n")

if __name__ == "__main__":
    try:
        raw = parse_m3u(INPUT_FILE)
        print(f"✅ Parsed {len(raw)} channels from {INPUT_FILE}")

        final = build_m3u(raw)
        print(f"✅ After dedupe, filtering, and sorting: {len(final)} channels left")

        write_m3u(OUTPUT_FILE, final)
        print(f"✅ Successfully wrote categorized playlist to {OUTPUT_FILE}")

        counts = {}
        for _, _, _, cat in final:
            counts[cat] = counts.get(cat, 0) + 1

        print("\n📊 Final Category Breakdown:")
        for cat, count in sorted(counts.items(), key=lambda x: -x[1]):
            print(f"   {cat}: {count}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

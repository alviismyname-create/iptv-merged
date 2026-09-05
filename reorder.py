import re
import sys
from collections import OrderedDict

INPUT_FILE = "merged.m3u"
OUTPUT_FILE = "output.m3u"

# Optional: Filter out adult channels (remove these keywords if you don't want filtering)
FILTER_KEYWORDS = ["xxx", "adult", "18+", "porn", "sex", "fuck", "hardcore"]

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

def set_group(extinf, group_name):
    # Remove any existing group-title, then force the new one
    extinf = re.sub(r'group-title="[^"]*"', '', extinf)
    extinf = re.sub(r'\s+', ' ', extinf)  # Clean up spaces
    if 'tvg-logo="' in extinf:
        extinf = extinf.replace('tvg-logo="', f'tvg-logo="" group-title="{group_name}"', 1)
    else:
        extinf = extinf.replace('#EXTINF:', f'#EXTINF: group-title="{group_name}"', 1)
    return extinf

def write_m3u(output_path, channels):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for extinf, url in channels:
            f.write(extinf + "\n")
            f.write(url + "\n")

if __name__ == "__main__":
    raw = parse_m3u(INPUT_FILE)
    print(f"✅ Parsed {len(raw)} raw channels")

    # 1. Remove duplicates by URL (keeps the first occurrence)
    seen = OrderedDict()
    for extinf, url in raw:
        if url not in seen:
            seen[url] = extinf

    # 2. Separate into three buckets
    malayalam = []
    tamil = []
    others = []

    for url, extinf in seen.items():
        if ',' in extinf:
            name = extinf.split(',')[-1].strip()
        else:
            name = "Unknown"

        # Filter adult content (optional)
        if is_filtered(name):
            continue

        group = get_existing_group(extinf)

        if group == "Malayalam":
            extinf = set_group(extinf, "Malayalam")
            malayalam.append((extinf, url))
        elif group == "Tamil":
            extinf = set_group(extinf, "Tamil")
            tamil.append((extinf, url))
        else:
            # DO NOT MODIFY these channels. Keep their original group-title exactly as-is.
            others.append((extinf, url))

    # 3. Combine in the required order: MALAYALAM -> TAMIL -> EVERYONE ELSE
    final_channels = malayalam + tamil + others

    write_m3u(OUTPUT_FILE, final_channels)

    print(f"✅ Final playlist has {len(final_channels)} channels")
    print(f"   🟢 Malayalam: {len(malayalam)}")
    print(f"   🔴 Tamil: {len(tamil)}")
    print(f"   ⚪ Other sources (original categories kept): {len(others)}")

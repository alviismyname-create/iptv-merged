import re
import sys
from collections import OrderedDict

INPUT_FILE = "merged.m3u"
OUTPUT_FILE = "output.m3u"

# ---------- FILTER: Remove Adult/NSFW globally (optional) ----------
FILTER_KEYWORDS = ["xxx", "adult", "18+", "porn", "sex", "fuck", "hardcore"]

def is_filtered(name):
    name_lower = name.lower()
    for kw in FILTER_KEYWORDS:
        if kw in name_lower:
            return True
    return False

# ---------- APPROVED LIST: Only these channels stay in "Malayalam" ----------
APPROVED_MALAYALAM = {
    "24 News", "Amrita TV", "Anand TV", "Asianet HD", "Asianet Middle East",
    "Asianet Movies HD", "Asianet News", "Big TV 24x7", "DD Malayalam",
    "Flowers TV USA", "Harvest TV", "Jaihind TV", "Janam TV", "Jeevan TV",
    "Kairali Arabia", "Kairali News", "Kairali TV", "Kairali We", "Kappa TV",
    "KITE Victers (Kerala)", "Manorama News", "Mathrubhumi News", "Mazhavil Manorama",
    "Mazhavil Manorama HD", "Media One", "meWATCH LIVE 1", "News18 Kerala",
    "Reporter TV", "Safari TV", "Shalom", "Shalom Global", "Starnet", "UTV Palakkad"
}

def clean_channel_name(name):
    """Remove resolution tags like (720p), (1080p), [Not 24/7] etc. for matching only."""
    # Remove (720p), (1080p), (576p), (480p), (576i)
    name = re.sub(r'\s*\(\d{3,4}[pi]\)', '', name, flags=re.IGNORECASE)
    # Remove [Not 24/7] etc.
    name = re.sub(r'\s*\[[^]]*\]', '', name)
    # Remove trailing spaces and collapse multiple spaces
    name = re.sub(r'\s+', ' ', name)
    return name.strip()

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
    """Forcefully set the group-title (removes any existing one)."""
    extinf = re.sub(r'group-title="[^"]*"', '', extinf)
    extinf = re.sub(r'\s+', ' ', extinf)
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

    # 2. Separate into buckets
    malayalam = []
    tamil = []
    others = []

    for url, extinf in seen.items():
        if ',' in extinf:
            full_name = extinf.split(',')[-1].strip()
        else:
            full_name = "Unknown"

        # Global adult filter (optional - keep it)
        if is_filtered(full_name):
            continue

        group = get_existing_group(extinf)

        # ---------- ONLY filter the Malayalam group ----------
        if group == "Malayalam":
            # Clean the name for matching (ignore resolution/quality)
            cleaned = clean_channel_name(full_name)
            
            # Check if this channel is in our approved list
            if cleaned not in APPROVED_MALAYALAM:
                # ❌ REMOVE this channel (do NOT add it to any bucket)
                print(f"   🗑️ Removing from Malayalam: {full_name}")
                continue
            
            # ✅ APPROVED: Keep it, force group="Malayalam" just in case
            extinf = set_group(extinf, "Malayalam")
            malayalam.append((extinf, url))
        
        elif group == "Tamil":
            # ✨ DO NOTHING to Tamil - keep exactly as is
            tamil.append((extinf, url))
        
        else:
            # ✨ DO NOTHING to other groups - keep their original group-title exactly
            others.append((extinf, url))

    # 3. Combine in the required order: MALAYALAM -> TAMIL -> EVERYONE ELSE
    final_channels = malayalam + tamil + others

    write_m3u(OUTPUT_FILE, final_channels)

    print(f"\n✅ Final playlist has {len(final_channels)} channels")
    print(f"   🟢 Malayalam (kept only approved): {len(malayalam)}")
    print(f"   🔴 Tamil (unchanged): {len(tamil)}")
    print(f"   ⚪ Other sources (completely untouched): {len(others)}")

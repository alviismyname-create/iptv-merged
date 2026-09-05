import urllib.request
import re
import sys

# ------------------------------------------------------------
# YOUR APPROVED MALAYALAM CHANNELS
# ------------------------------------------------------------
APPROVED_MALAYALAM = [
    "24 News", "Amrita TV", "Anand TV", "Asianet HD",
    "Asianet Middle East", "Asianet Movies HD", "Asianet News",
    "Big TV 24x7", "DD Malayalam", "Flowers TV USA", "Harvest TV",
    "Jaihind TV", "Janam TV", "Jeevan TV", "Kairali Arabia",
    "Kairali News", "Kairali TV", "Kairali We", "Kappa TV",
    "KITE Victers (Kerala)", "Manorama News", "Mathrubhumi News",
    "Mazhavil Manorama", "Mazhavil Manorama HD", "Media One",
    "meWATCH LIVE 1", "News18 Kerala", "Reporter TV", "Safari TV",
    "Shalom", "Shalom Global", "Starnet", "UTV Palakkad"
]

# ------------------------------------------------------------
# YOUR APPROVED TAMIL CHANNELS
# ------------------------------------------------------------
APPROVED_TAMIL = [
    "7S Music", "Aaryaa TV", "Chithiram", "Colors Tamil HD",
    "DD Tamil HD", "Disney Channel HD", "Malai Murasu TV",
    "News18 Tamil Nadu", "Oli TV", "Polimer TV", "Raj Digital Plus",
    "Raj Musix Tamil", "Raj TV", "Sana Plus", "Star Movies HD",
    "Star Movies Select HD", "Star Sports 2 HD", "Subin TV",
    "Suriya TV", "Tamilan TV", "TamilVision-TV", "Thalaa TV",
    "Ultimate TV", "Vendhar TV", "YET TV", "Zee Tamil HD"
]

MALAYALAM_SET = {name.lower() for name in APPROVED_MALAYALAM}
TAMIL_SET = {name.lower() for name in APPROVED_TAMIL}

# ------------------------------------------------------------
# CUSTOM STREAM LINK & LOGO FOR MAZHAVIL MANORAMA HD
# ------------------------------------------------------------
CUSTOM_MAZHAVIL_URL = "https://mumt07.tangotv.in/zHjX9OFlMAZHAVILMANORAMAHD/tracks-v1a1/mono.m3u8"
CUSTOM_MAZHAVIL_LOGO = "https://i.imgur.com/xCHQrH0.png"

def clean_name(name):
    """Remove resolution tags like (720p), [Not 24/7] for matching."""
    name = re.sub(r'\s*\(\d{3,4}[pi]\)', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\[[^]]*\]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip().lower()

def download_playlist(url):
    """Download and return list of (extinf, url) pairs."""
    print(f"Downloading: {url}")
    try:
        response = urllib.request.urlopen(url, timeout=30)
        content = response.read().decode('utf-8', errors='ignore')
        lines = content.splitlines()
        channels = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("#EXTINF"):
                extinf = line
                if i + 1 < len(lines):
                    stream_url = lines[i + 1].strip()
                    if stream_url.startswith("http"):
                        channels.append((extinf, stream_url))
                    i += 2
                else:
                    i += 1
            else:
                i += 1
        return channels
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")
        return []

def set_group_and_logo(extinf, group_name, custom_logo=None):
    """Helper to set group and optionally logo."""
    extinf_new = re.sub(r'group-title="[^"]*"', '', extinf)
    extinf_new = re.sub(r'\s+', ' ', extinf_new)

    if custom_logo:
        if 'tvg-logo="' in extinf_new:
            extinf_new = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{custom_logo}"', extinf_new)
        else:
            extinf_new = extinf_new.replace('#EXTINF:', f'#EXTINF: tvg-logo="{custom_logo}"', 1)

    if 'group-title="' in extinf_new:
        extinf_new = re.sub(r'group-title="[^"]*"', f'group-title="{group_name}"', extinf_new)
    else:
        extinf_new = extinf_new.replace('#EXTINF:', f'#EXTINF: group-title="{group_name}"', 1)

    extinf_new = re.sub(r'\s+', ' ', extinf_new)
    return extinf_new

# ------------------------------------------------------------
# STEP 1: Download and FILTER Malayalam
# ------------------------------------------------------------
mal_channels = download_playlist("https://iptv-org.github.io/iptv/languages/mal.m3u")
malayalam_kept = []
mal_removed = 0

for extinf, url in mal_channels:
    if "," in extinf:
        full_name = extinf.split(",")[-1].strip()
    else:
        full_name = "Unknown"

    if clean_name(full_name) in MALAYALAM_SET:
        if clean_name(full_name) == "mazhavil manorama hd":
            extinf_new = set_group_and_logo(extinf, "Malayalam", CUSTOM_MAZHAVIL_LOGO)
            malayalam_kept.append((extinf_new, CUSTOM_MAZHAVIL_URL))
        else:
            extinf_new = set_group_and_logo(extinf, "Malayalam")
            malayalam_kept.append((extinf_new, url))
    else:
        mal_removed += 1

print(f"✅ Malayalam: Kept {len(malayalam_kept)} channels, Removed {mal_removed} channels")

# ------------------------------------------------------------
# STEP 2: Download and FILTER Tamil
# ------------------------------------------------------------
tam_channels = download_playlist("https://iptv-org.github.io/iptv/languages/tam.m3u")
tamil_kept = []
tam_removed = 0

for extinf, url in tam_channels:
    if "," in extinf:
        full_name = extinf.split(",")[-1].strip()
    else:
        full_name = "Unknown"

    if clean_name(full_name) in TAMIL_SET:
        extinf_new = set_group_and_logo(extinf, "Tamil")
        tamil_kept.append((extinf_new, url))
    else:
        tam_removed += 1

print(f"✅ Tamil: Kept {len(tamil_kept)} channels, Removed {tam_removed} channels")

# ------------------------------------------------------------
# STEP 3: Download DOMS9 - Force ALL channels into "dom9" group
# ------------------------------------------------------------
dom9_url = "https://raw.githubusercontent.com/doms9/iptv/refs/heads/default/M3U8/base.m3u8"
dom9_channels = download_playlist(dom9_url)
dom9_kept = []

for extinf, url in dom9_channels:
    extinf_new = set_group_and_logo(extinf, "dom9")
    dom9_kept.append((extinf_new, url))

print(f"✅ dom9: Added {len(dom9_kept)} channels (all in 'dom9' group)")

# ------------------------------------------------------------
# STEP 4: Download English International Playlist (NO FILTERING)
# ------------------------------------------------------------
eng_intl_url = "https://raw.githubusercontent.com/wizakorhd/iptv/main/playlist-english-intl.m3u"
eng_intl_channels = download_playlist(eng_intl_url)
eng_intl_kept = []

for extinf, url in eng_intl_channels:
    # Keep all channels, ensure they have a group-title
    extinf_new = extinf
    if 'group-title="' not in extinf_new:
        if 'tvg-logo="' in extinf_new:
            extinf_new = extinf_new.replace('tvg-logo="', 'tvg-logo="" group-title="Uncategorized"', 1)
        else:
            extinf_new = extinf_new.replace('#EXTINF:', '#EXTINF: group-title="Uncategorized"', 1)
    eng_intl_kept.append((extinf_new, url))

print(f"✅ English International: Added {len(eng_intl_kept)} channels (no filtering)")

# ------------------------------------------------------------
# STEP 5: Download English India Playlist (NO FILTERING)
# ------------------------------------------------------------
eng_india_url = "https://raw.githubusercontent.com/wizakorhd/iptv/main/playlist-english-india.m3u"
eng_india_channels = download_playlist(eng_india_url)
eng_india_kept = []

for extinf, url in eng_india_channels:
    # Keep all channels, ensure they have a group-title
    extinf_new = extinf
    if 'group-title="' not in extinf_new:
        if 'tvg-logo="' in extinf_new:
            extinf_new = extinf_new.replace('tvg-logo="', 'tvg-logo="" group-title="Uncategorized"', 1)
        else:
            extinf_new = extinf_new.replace('#EXTINF:', '#EXTINF: group-title="Uncategorized"', 1)
    eng_india_kept.append((extinf_new, url))

print(f"✅ English India: Added {len(eng_india_kept)} channels (no filtering)")

# ------------------------------------------------------------
# STEP 6: Download Anime Playlist (NO FILTERING)
# ------------------------------------------------------------
anime_url = "https://raw.githubusercontent.com/wizakorhd/iptv/main/playlist-anime.m3u"
anime_channels = download_playlist(anime_url)
anime_kept = []

for extinf, url in anime_channels:
    # Keep all channels, ensure they have a group-title
    extinf_new = extinf
    if 'group-title="' not in extinf_new:
        if 'tvg-logo="' in extinf_new:
            extinf_new = extinf_new.replace('tvg-logo="', 'tvg-logo="" group-title="Anime"', 1)
        else:
            extinf_new = extinf_new.replace('#EXTINF:', '#EXTINF: group-title="Anime"', 1)
    anime_kept.append((extinf_new, url))

print(f"✅ Anime: Added {len(anime_kept)} channels (no filtering)")

# ------------------------------------------------------------
# STEP 7: Merge and write final output.m3u
# ------------------------------------------------------------
all_final = malayalam_kept + tamil_kept + dom9_kept + eng_intl_kept + eng_india_kept + anime_kept

with open("output.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for extinf, url in all_final:
        f.write(extinf + "\n")
        f.write(url + "\n")

print(f"\n✅ FINAL: {len(all_final)} total channels in output.m3u")
print(f"   🟢 Malayalam (filtered): {len(malayalam_kept)}")
print(f"   🔴 Tamil (filtered): {len(tamil_kept)}")
print(f"   🟠 dom9 (all channels): {len(dom9_kept)}")
print(f"   🟡 English International (no filtering): {len(eng_intl_kept)}")
print(f"   🟢 English India (no filtering): {len(eng_india_kept)}")
print(f"   🟣 Anime (no filtering): {len(anime_kept)}")

"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
             TeamDev Project 
Project Name: Dailymotion M3U8 Resolver
Script By   : @MR_ARMAN_08
               
             Version => 1.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
"""

      USE IN YOUR OWN RISK WE DO NOT RESPONSIBLE FOR ANY VIOLATION!

"""
import re
import asyncio
import aiohttp
from typing import Optional, Dict, Any

METADATA_URL = (
    "https://www.dailymotion.com/player/metadata/video/{vid}"
    "?embedder=https%3A%2F%2Fwww.dailymotion.com&locale=en_US"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://www.dailymotion.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=20)

def extract_video_id(url_or_id: str) -> Optional[str]:

    if not url_or_id:
        return None

    url_or_id = url_or_id.strip()

    if re.match(r'^x[a-zA-Z0-9]+$', url_or_id):
        return url_or_id
        
    match = re.search(r'/video/([a-zA-Z0-9]+)', url_or_id)
    if match:
        return match.group(1)

    match = re.search(r'dai\.ly/([a-zA-Z0-9]+)', url_or_id)
    if match:
        return match.group(1)

    return None

async def resolve(
    url_or_id: str,
    session: Optional[aiohttp.ClientSession] = None
) -> Dict[str, Any]:

    video_id = extract_video_id(url_or_id)
    if not video_id:
        raise ValueError(f"Invalid Dailymotion URL Or ID: {url_or_id}")

    api_url = METADATA_URL.format(vid=video_id)
    external_session = session is not None

    if not session:
        session = aiohttp.ClientSession(timeout=DEFAULT_TIMEOUT)

    try:
        for attempt in range(2):
            try:
                async with session.get(
                    api_url,
                    headers={**HEADERS, "Referer": f"https://www.dailymotion.com/video/{video_id}"}
                ) as resp:

                    if resp.status != 200:
                        raise RuntimeError(f"HTTP {resp.status}")

                    data = await resp.json(content_type=None)
                    break

            except Exception as e:
                if attempt == 1:
                    raise RuntimeError(f"Request Failed After Retry: {e}")
                await asyncio.sleep(1)

    finally:
        if not external_session:
            await session.close()

    qualities = data.get("qualities") or {}
    auto_streams = qualities.get("auto") or []

    m3u8_url = None
    for item in auto_streams:
        if item.get("type") == "application/x-mpegURL":
            m3u8_url = item.get("url")
            break

    if not m3u8_url:
        raise ValueError("No M3U8 Stream Found In Metadata")

    thumbnails = data.get("thumbnails") or {}
    thumbnail = (
        thumbnails.get("720")
        or thumbnails.get("480")
        or thumbnails.get("360")
    )

    return {
        "video_id": video_id,
        "title": data.get("title"),
        "duration": data.get("duration"),
        "channel": data.get("channel"),
        "m3u8_url": m3u8_url,
        "thumbnail": thumbnail,
        "thumbnails": thumbnails,
        "owner": (data.get("owner") or {}).get("screenname"),
        "stream_formats": data.get("stream_formats") or {},
    }

async def main():
    print("\nDailymotion Video Link To M3U8 Link Fetcher\n")

    user_input = input("Enter Dailymotion URL Or Video ID: ").strip()

    if not user_input:
        print("⚠️ No Input Provided. Using Default URL...\n")
        user_input = "https://www.dailymotion.com/video/x8y314y" # This Is Default Url If User Input Is Empty Then Use This Link!!

    print(f"\n[*] Fetching Information From: {user_input}\n")

    try:
        result = await resolve(user_input)

        print("━━━━━━━━ RESULT ━━━━━━━━")
        print(f"• Title     : {result['title']}")
        print(f"• Duration  : {result['duration']}s")
        print(f"• Channel   : {result['channel']}")
        print(f"• Owner     : {result['owner']}")
        print(f"• M3U8 URL  : {result['m3u8_url']}")
        print(f"• Thumbnail : {result['thumbnail']}")
        print("━━━━━━━━━━━━━━━━━━━━━━━\n")

    except Exception as e:
        print(f"[❌] Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
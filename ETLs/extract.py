import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY   = os.getenv("RIOT_API_KEY")
GAME_NAME = os.getenv("GAME_NAME")
TAG_LINE  = os.getenv("TAG_LINE")
REGION    = os.getenv("REGION", "br1")
ROUTING   = os.getenv("ROUTING", "americas")

HEADERS = {"X-Riot-Token": API_KEY}

QUEUE_IDS   = [420, 1700]
MATCH_COUNT = 100
RATE_SLEEP  = 1.2

def _get(url: str) -> dict:
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 10))
        print(f"[extract] Rate limited — sleeping {retry_after}s")
        time.sleep(retry_after)
        return _get(url)

    response.raise_for_status()
    return response.json()

def get_puuid(game_name: str, tag_line: str) -> str:
    encoded_name = requests.utils.quote(game_name)
    encoded_tag  = requests.utils.quote(tag_line)

    url = (
        f"https://{ROUTING}.api.riotgames.com"
        f"/riot/account/v1/accounts/by-riot-id/{encoded_name}/{encoded_tag}"
    )

    data  = _get(url)
    puuid = data["puuid"]
    print(f"[extract] '{game_name}#{tag_line}' → PUUID: {puuid[:16]}...")
    return puuid

def run_extract() -> tuple[str, list[dict]]:
    print("[extract] Starting extract phase...")

    puuid     = get_puuid(GAME_NAME, TAG_LINE)
    match_ids = get_match_ids(puuid)
    matches   = get_all_matches(match_ids)

    return puuid, matches

if __name__ == "__main__":
    puuid, matches = run_extract()
    print(f"\nSample match keys: {list(matches[0].keys()) if matches else 'No matches'}")

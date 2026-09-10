import os
import time
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("RIOT_API_KEY")
GAME_NAME = os.getenv("GAME_NAME")
TAG_LINE = os.getenv("TAG_LINE")
REGION = os.getenv("REGION", "br1")
ROUTING = os.getenv("ROUTING", "americas")

HEADERS = {"X-Riot-Token": API_KEY}

QUEUE_IDS = [420, 1700]
MATCH_COUNT = 100
RATE_SLEEP = 1.2

def _get(url: str) -> dict:
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 10))
        logging.warning(f"Extract: Rate limited — sleeping {retry_after}s")
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
    logging.info(f"Extract: '{game_name}#{tag_line}' → PUUID: {puuid[:15]}...")
    return puuid

def get_match_ids(puuid: str) -> list[str]:
    all_ids = []

    for queue_id in QUEUE_IDS:
        url = (
            f"https://{ROUTING}.api.riotgames.com"
            f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
            f"?queue={queue_id}&count={MATCH_COUNT}"
        )
        ids = _get(url)
        logging.info(f"Extract: Queue {queue_id} → {len(ids)} match IDs fetched")
        all_ids.extend(ids)

    seen       = set()
    unique_ids = [m for m in all_ids if not (m in seen or seen.add(m))]

    logging.info(f"Extract: Total unique match IDs: {len(unique_ids)}")
    return unique_ids

def get_match_detail(match_id: str) -> dict:
    url = (
        f"https://{ROUTING}.api.riotgames.com"
        f"/lol/match/v5/matches/{match_id}"
    )
    return _get(url)

def get_all_matches(match_ids: list[str]) -> list[dict]:
    matches = []

    for i, match_id in enumerate(match_ids):
        try:
            match = get_match_detail(match_id)
            matches.append(match)

            if (i + 1) % 10 == 0:
                logging.info(f"Extract: Fetched {i + 1}/{len(match_ids)} matches...")

            time.sleep(RATE_SLEEP)

        except requests.HTTPError as e:
            logging.error(f"Extract: WARNING — skipping {match_id}: {e}")
            continue

    logging.info(f"Extract: {len(matches)} matches successfully fetched!")
    return matches

def run_extract() -> tuple[str, list[dict]]:
    logging.info("Extract: Starting extract phase...")

    puuid = get_puuid(GAME_NAME, TAG_LINE)
    match_ids = get_match_ids(puuid)
    matches = get_all_matches(match_ids)

    return puuid, matches

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(levelname)s] - %(message)s'
    )
    puuid, matches = run_extract()
    print(f"\nSample match keys: {list(matches[0].keys()) if matches else 'No matches'}")

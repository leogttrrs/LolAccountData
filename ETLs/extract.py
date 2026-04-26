

def run_extract() -> tuple[str, list[dict]]:
    print("[extract] Starting extract phase...")

    puuid     = get_puuid(GAME_NAME, TAG_LINE)
    match_ids = get_match_ids(puuid)
    matches   = get_all_matches(match_ids)

    return puuid, matches

if __name__ == "__main__":
    puuid, matches = run_extract()
    print(f"\nSample match keys: {list(matches[0].keys()) if matches else 'No matches'}")

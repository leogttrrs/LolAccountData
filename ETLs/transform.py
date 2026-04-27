import pandas as pd

QUEUE_LABELS = {
    420: "RANKED",
    1700: "ARENA",
}

def run_transform(puuid: str, matches: list[dict]) -> pd.DataFrame:
    df = _explode_participants(puuid, matches)
    df = _filter_remakes(df)

    print(f"[transform] Done. {len(df)} rows ready to load.")
    return df

def _explode_participants(puuid: str, matches: list[dict]) -> pd.DataFrame:
    rows = []

    for match in matches:
        info = match["info"]
        metadata = match["metadata"]

        for participant in info["participants"]:
            if participant["puuid"] == puuid:
                row = {
                    "match_id": metadata["matchId"],
                    "queue_id": info["queueId"],
                    "game_duration": info["gameDuration"],
                    "game_version": info["gameVersion"],
                    "game_start_timestamp": info["gameStartTimestamp"],

                    "champion_name": participant["championName"],
                    "kills": participant["kills"],
                    "deaths": participant["deaths"],
                    "assists": participant["assists"],
                    "win": participant["win"],
                    "placement": participant.get("placement", None),
                    "damage_dealt": participant["totalDamageDealtToChampions"],
                    "vision_score": participant["visionScore"],
                    "total_minions_killed": participant["totalMinionsKilled"],
                    "neutral_minions_killed": participant["neutralMinionsKilled"],
                    "time_played": participant["timePlayed"],
                    "game_ended_in_early_surrender": participant["gameEndedInEarlySurrender"],
                }
                rows.append(row)
                break

    df = pd.DataFrame(rows)
    print(f"[transform] Exploded {len(df)} matches into rows.")
    return df

def _filter_remakes(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    mask = (df["game_ended_in_early_surrender"] == False) & (df["game_duration"] >= 300)
    df = df[mask].reset_index(drop=True)

    print(f"[transform] Filtered {before - len(df)} remakes. {len(df)} games remaining.")
    return df

def _select_final_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df[[
        "match_id",
        "queue_type",
        "champion_name",
        "kills",
        "deaths",
        "assists",
        "kda_score",
        "damage_dealt",
        "vision_score",
        "cs_per_min",
        "game_duration_min",
        "win",
        "placement",
        "performance_flag",
        "played_at",
        "patch",
    ]]

if __name__ == "__main__":
    from extract import run_extract

    puuid, matches = run_extract()
    df = run_transform(puuid, matches)
    print(df.head(10).to_string())
    print("\n--- dtypes ---")
    print(df.dtypes)
    print("\n--- performance_flag distribution ---")
    print(df.groupby(["queue_type", "performance_flag"]).size())
CREATE TABLE IF NOT EXISTS "events" (
    "event_name"    TEXT,
    "event_data"    BLOB
);


CREATE TABLE IF NOT EXISTS "matches" (
    "guild_id"    BLOB,
    "game_type"    TEXT,
    "date_time"    TEXT
);


CREATE TABLE IF NOT EXISTS "prefixes" (
    "guild_id"    int,
    "prefix"    text
);


CREATE TABLE IF NOT EXISTS "profiles" (
    "userid"    INTEGER,
    "name"    TEXT,
    "description"    TEXT,
    "matches_played"    INTEGER,
    "matches_won"    INTEGER,
    "matches_lost"    INTEGER,
    "runs"    INTEGER,
    "balls"    INTEGER,
    "wickets"    INTEGER,
    "wickets_lost"    INTEGER,
    "highest_score"    INTEGER,
    "hattricks"    INTEGER,
    "ducks"    INTEGER,
    "batting_average"    INTEGER,
    "match_log"    BLOB,
    "status"    TEXT,
    "created_at"    TEXT,
    "Field5"    BLOB,
    "Field6"    BLOB,
    "Field19"    BLOB,
    "Field20"    BLOB
);

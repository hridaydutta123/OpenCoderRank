-- coding_platform_flask/schema.sql
DROP TABLE IF EXISTS scoreboard;
CREATE TABLE scoreboard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    challenge_id TEXT NOT NULL,
    score INTEGER NOT NULL,
    time_taken_seconds INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_scoreboard_challenge_score_time ON scoreboard (challenge_id, score DESC, time_taken_seconds ASC);
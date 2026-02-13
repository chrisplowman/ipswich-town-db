-- Ipswich Town FC Database Schema
-- PostgreSQL 12+

-- Drop existing tables if they exist (for clean reinstall)
DROP TABLE IF EXISTS player_match_stats CASCADE;
DROP TABLE IF EXISTS cards CASCADE;
DROP TABLE IF EXISTS goals CASCADE;
DROP TABLE IF EXISTS lineups CASCADE;
DROP TABLE IF EXISTS match_statistics CASCADE;
DROP TABLE IF EXISTS matches CASCADE;
DROP TABLE IF EXISTS players CASCADE;
DROP TABLE IF EXISTS teams CASCADE;
DROP TABLE IF EXISTS competitions CASCADE;
DROP TABLE IF EXISTS seasons CASCADE;

-- Seasons table
CREATE TABLE seasons (
    id SERIAL PRIMARY KEY,
    season_name VARCHAR(20) NOT NULL UNIQUE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Competitions table
CREATE TABLE competitions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    competition_type VARCHAR(50) NOT NULL, -- 'League', 'Cup', 'Playoff'
    country VARCHAR(50) DEFAULT 'England',
    tier INTEGER, -- 1 for top division, 2 for Championship, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Teams table
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL UNIQUE,
    short_name VARCHAR(50),
    stadium VARCHAR(100),
    city VARCHAR(100),
    country VARCHAR(50) DEFAULT 'England',
    founded_year INTEGER,
    api_id_thesportsdb VARCHAR(50),
    api_id_football_data VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Players table
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    player_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    nationality VARCHAR(50),
    position VARCHAR(50), -- 'Goalkeeper', 'Defender', 'Midfielder', 'Forward'
    squad_number INTEGER,
    joined_date DATE,
    left_date DATE,
    api_id_thesportsdb VARCHAR(50),
    api_id_football_data VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Matches table
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    season_id INTEGER REFERENCES seasons(id) ON DELETE CASCADE,
    competition_id INTEGER REFERENCES competitions(id) ON DELETE CASCADE,
    match_date DATE NOT NULL,
    kick_off_time TIME,
    home_team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    away_team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    home_score INTEGER,
    away_score INTEGER,
    half_time_home_score INTEGER,
    half_time_away_score INTEGER,
    venue VARCHAR(100),
    attendance INTEGER,
    referee VARCHAR(100),
    match_status VARCHAR(20) DEFAULT 'scheduled', -- 'scheduled', 'live', 'finished', 'postponed', 'cancelled'
    match_round VARCHAR(50), -- 'Round 1', 'Quarter-final', etc.
    api_id_thesportsdb VARCHAR(50),
    api_id_football_data VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_score CHECK (
        (home_score IS NULL AND away_score IS NULL) OR 
        (home_score >= 0 AND away_score >= 0)
    )
);

-- Match Statistics table
CREATE TABLE match_statistics (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE UNIQUE,
    ipswich_possession INTEGER, -- Percentage
    opposition_possession INTEGER,
    ipswich_shots INTEGER,
    opposition_shots INTEGER,
    ipswich_shots_on_target INTEGER,
    opposition_shots_on_target INTEGER,
    ipswich_corners INTEGER,
    opposition_corners INTEGER,
    ipswich_fouls INTEGER,
    opposition_fouls INTEGER,
    ipswich_offsides INTEGER,
    opposition_offsides INTEGER,
    ipswich_passes INTEGER,
    opposition_passes INTEGER,
    ipswich_pass_accuracy DECIMAL(5,2),
    opposition_pass_accuracy DECIMAL(5,2),
    ipswich_tackles INTEGER,
    opposition_tackles INTEGER,
    ipswich_saves INTEGER,
    opposition_saves INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lineups table
CREATE TABLE lineups (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    player_id INTEGER REFERENCES players(id) ON DELETE CASCADE,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    position VARCHAR(50),
    is_starter BOOLEAN DEFAULT TRUE,
    substituted_on_minute INTEGER,
    substituted_off_minute INTEGER,
    formation_position VARCHAR(20), -- 'GK', 'LB', 'CB', 'RB', 'CM', 'LW', 'ST', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(match_id, player_id)
);

-- Player Match Statistics table
CREATE TABLE player_match_stats (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    player_id INTEGER REFERENCES players(id) ON DELETE CASCADE,
    minutes_played INTEGER DEFAULT 0,
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    shots INTEGER DEFAULT 0,
    shots_on_target INTEGER DEFAULT 0,
    passes INTEGER DEFAULT 0,
    pass_accuracy DECIMAL(5,2),
    tackles INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    fouls_committed INTEGER DEFAULT 0,
    fouls_won INTEGER DEFAULT 0,
    offsides INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0, -- For goalkeepers
    rating DECIMAL(3,1), -- Match rating out of 10
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(match_id, player_id)
);

-- Goals table
CREATE TABLE goals (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    player_id INTEGER REFERENCES players(id) ON DELETE CASCADE,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    minute INTEGER NOT NULL,
    goal_type VARCHAR(50), -- 'Open Play', 'Penalty', 'Free Kick', 'Header', 'Own Goal'
    is_penalty BOOLEAN DEFAULT FALSE,
    is_own_goal BOOLEAN DEFAULT FALSE,
    assist_player_id INTEGER REFERENCES players(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_minute CHECK (minute >= 0 AND minute <= 150)
);

-- Cards table
CREATE TABLE cards (
    id SERIAL PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id) ON DELETE CASCADE,
    player_id INTEGER REFERENCES players(id) ON DELETE CASCADE,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    card_type VARCHAR(10) NOT NULL, -- 'Yellow', 'Red', 'Yellow-Red'
    minute INTEGER NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_card CHECK (card_type IN ('Yellow', 'Red', 'Yellow-Red')),
    CONSTRAINT valid_minute CHECK (minute >= 0 AND minute <= 150)
);

-- Create indexes for better query performance
CREATE INDEX idx_matches_date ON matches(match_date);
CREATE INDEX idx_matches_season ON matches(season_id);
CREATE INDEX idx_matches_home_team ON matches(home_team_id);
CREATE INDEX idx_matches_away_team ON matches(away_team_id);
CREATE INDEX idx_matches_competition ON matches(competition_id);
CREATE INDEX idx_goals_match ON goals(match_id);
CREATE INDEX idx_goals_player ON goals(player_id);
CREATE INDEX idx_cards_match ON cards(match_id);
CREATE INDEX idx_lineups_match ON lineups(match_id);
CREATE INDEX idx_lineups_player ON lineups(player_id);
CREATE INDEX idx_player_stats_match ON player_match_stats(match_id);
CREATE INDEX idx_player_stats_player ON player_match_stats(player_id);

-- Create views for common queries

-- View: Ipswich Town matches with results
CREATE VIEW ipswich_matches AS
SELECT 
    m.id,
    m.match_date,
    s.season_name,
    c.name AS competition,
    CASE 
        WHEN t1.team_name = 'Ipswich Town' THEN 'Home'
        ELSE 'Away'
    END AS venue,
    CASE 
        WHEN t1.team_name = 'Ipswich Town' THEN t2.team_name
        ELSE t1.team_name
    END AS opponent,
    CASE 
        WHEN t1.team_name = 'Ipswich Town' THEN m.home_score
        ELSE m.away_score
    END AS ipswich_score,
    CASE 
        WHEN t1.team_name = 'Ipswich Town' THEN m.away_score
        ELSE m.home_score
    END AS opponent_score,
    CASE 
        WHEN m.home_score IS NULL THEN 'Scheduled'
        WHEN t1.team_name = 'Ipswich Town' AND m.home_score > m.away_score THEN 'Win'
        WHEN t2.team_name = 'Ipswich Town' AND m.away_score > m.home_score THEN 'Win'
        WHEN m.home_score = m.away_score THEN 'Draw'
        ELSE 'Loss'
    END AS result,
    m.attendance,
    m.match_status
FROM matches m
JOIN seasons s ON m.season_id = s.id
JOIN competitions c ON m.competition_id = c.id
JOIN teams t1 ON m.home_team_id = t1.id
JOIN teams t2 ON m.away_team_id = t2.id
WHERE t1.team_name = 'Ipswich Town' OR t2.team_name = 'Ipswich Town'
ORDER BY m.match_date DESC;

-- View: Top scorers
CREATE VIEW top_scorers AS
SELECT 
    p.player_name,
    COUNT(g.id) as total_goals,
    COUNT(CASE WHEN g.is_penalty THEN 1 END) as penalties,
    COUNT(CASE WHEN g.is_penalty THEN NULL ELSE 1 END) as open_play_goals,
    MIN(s.season_name) as first_season,
    MAX(s.season_name) as last_season
FROM goals g
JOIN players p ON g.player_id = p.id
JOIN matches m ON g.match_id = m.id
JOIN seasons s ON m.season_id = s.id
JOIN teams t ON g.team_id = t.id
WHERE t.team_name = 'Ipswich Town'
  AND g.is_own_goal = FALSE
GROUP BY p.player_name
ORDER BY total_goals DESC;

-- View: Season statistics
CREATE VIEW season_statistics AS
SELECT 
    s.season_name,
    c.name AS competition,
    COUNT(m.id) as matches_played,
    COUNT(CASE 
        WHEN (t1.team_name = 'Ipswich Town' AND m.home_score > m.away_score) OR
             (t2.team_name = 'Ipswich Town' AND m.away_score > m.home_score)
        THEN 1 END) as wins,
    COUNT(CASE WHEN m.home_score = m.away_score THEN 1 END) as draws,
    COUNT(CASE 
        WHEN (t1.team_name = 'Ipswich Town' AND m.home_score < m.away_score) OR
             (t2.team_name = 'Ipswich Town' AND m.away_score < m.home_score)
        THEN 1 END) as losses,
    SUM(CASE 
        WHEN t1.team_name = 'Ipswich Town' THEN m.home_score
        ELSE m.away_score END) as goals_for,
    SUM(CASE 
        WHEN t1.team_name = 'Ipswich Town' THEN m.away_score
        ELSE m.home_score END) as goals_against
FROM matches m
JOIN seasons s ON m.season_id = s.id
JOIN competitions c ON m.competition_id = c.id
JOIN teams t1 ON m.home_team_id = t1.id
JOIN teams t2 ON m.away_team_id = t2.id
WHERE (t1.team_name = 'Ipswich Town' OR t2.team_name = 'Ipswich Town')
  AND m.match_status = 'finished'
GROUP BY s.season_name, c.name
ORDER BY s.season_name DESC, c.name;

-- Insert Ipswich Town as the primary team
INSERT INTO teams (team_name, short_name, stadium, city, founded_year) 
VALUES ('Ipswich Town', 'Ipswich', 'Portman Road', 'Ipswich', 1878)
ON CONFLICT (team_name) DO NOTHING;

-- Insert common competitions
INSERT INTO competitions (name, competition_type, tier) VALUES
    ('Premier League', 'League', 1),
    ('Championship', 'League', 2),
    ('League One', 'League', 3),
    ('FA Cup', 'Cup', NULL),
    ('League Cup', 'Cup', NULL),
    ('Europa League', 'Cup', NULL),
    ('Championship Playoffs', 'Playoff', 2)
ON CONFLICT DO NOTHING;

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_seasons_updated_at BEFORE UPDATE ON seasons
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_players_updated_at BEFORE UPDATE ON players
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_matches_updated_at BEFORE UPDATE ON matches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_match_statistics_updated_at BEFORE UPDATE ON match_statistics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_player_match_stats_updated_at BEFORE UPDATE ON player_match_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

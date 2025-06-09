-- Conversations table
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(50),
    message TEXT,
    source VARCHAR(20),
    context JSONB,
    session_id VARCHAR(100)
);

-- Personality state table
CREATE TABLE personality_state (
    id SERIAL PRIMARY KEY,
    trait_name VARCHAR(50) UNIQUE,
    value FLOAT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User preferences
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    preference_key VARCHAR(100),
    preference_value JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System improvements log
CREATE TABLE improvement_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    category VARCHAR(50),
    description TEXT,
    implementation_status VARCHAR(20) DEFAULT 'pending',
    priority INTEGER DEFAULT 5
);

-- Offline conversation sync
CREATE TABLE offline_conversations (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50),
    conversation_data JSONB,
    sync_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
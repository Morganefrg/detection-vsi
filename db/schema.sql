-- Supprime les tables si elles existent déjà (utile pour recommencer proprement)
DROP TABLE IF EXISTS violation;
DROP TABLE IF EXISTS tracked_object;

-- Table des objets trackés (personnes et véhicules)
CREATE TABLE tracked_object (
    id          SERIAL PRIMARY KEY,
    track_id    INTEGER UNIQUE NOT NULL,
    object_type VARCHAR(10) NOT NULL CHECK (object_type IN ('person', 'vehicle')),
    first_seen  TIMESTAMP NOT NULL DEFAULT NOW(),
    last_seen   TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Table des violations détectées
CREATE TABLE violation (
    id          SERIAL PRIMARY KEY,
    object_id   INTEGER NOT NULL REFERENCES tracked_object(id),
    type        VARCHAR(30) NOT NULL CHECK (type IN ('loitering', 'fall_detected', 'parking_violation')),
    zone        VARCHAR(50),
    timestamp   TIMESTAMP NOT NULL DEFAULT NOW()
);
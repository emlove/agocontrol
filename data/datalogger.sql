PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE data(id INTEGER PRIMARY KEY AUTOINCREMENT, uuid TEXT, environment TEXT, level REAL, timestamp LONG);
CREATE INDEX timestamp_idx ON data(timestamp);
CREATE INDEX environment_idx ON data(environment);
CREATE INDEX uuid_idx ON data(uuid);
COMMIT;

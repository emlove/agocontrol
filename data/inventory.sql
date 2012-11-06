PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE rooms (uuid text, name text, location text);
CREATE TABLE devices (uuid text, name text, room text);
COMMIT;

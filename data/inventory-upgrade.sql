PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE floorplans (uuid text, name text);
CREATE TABLE devicesfloorplan (floorplan text, device text, x integer, y integer);
COMMIT;

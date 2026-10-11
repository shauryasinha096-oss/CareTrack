-- Run as schema administrator. DDL implicitly commits in MySQL.
-- Only caretrack_lab objects are destroyed; operational tables are untouched.
CREATE DATABASE IF NOT EXISTS caretrack_lab;
USE caretrack_lab;
CREATE TABLE IF NOT EXISTS ddl_notes (note_id INT PRIMARY KEY, label VARCHAR(50) NOT NULL) ENGINE=InnoDB;
ALTER TABLE ddl_notes ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
INSERT INTO ddl_notes(note_id,label) VALUES(1,'Fictional DDL exercise');
RENAME TABLE ddl_notes TO ddl_notes_renamed;
TRUNCATE TABLE ddl_notes_renamed;
DROP TABLE ddl_notes_renamed;
USE caretrack;

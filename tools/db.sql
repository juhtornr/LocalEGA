DROP DATABASE IF EXISTS lega;
CREATE DATABASE lega;

\connect lega

DROP TABLE IF EXISTS files;
DROP TABLE IF EXISTS submissions;

CREATE TYPE status AS ENUM ('Received', 'In progress', 'Archived', 'Error');
CREATE TYPE hashAlgo AS ENUM ('md5', 'sha256');

CREATE TABLE submissions (
        id            INTEGER NOT NULL, PRIMARY KEY(id), UNIQUE (id),
	user_id       INTEGER NOT NULL,
	created_at    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
	completed_at  TIMESTAMP WITH TIME ZONE
);

CREATE TABLE files (
        id           SERIAL, PRIMARY KEY(id), UNIQUE (id),
	submission_id INTEGER REFERENCES submissions (id) ON DELETE CASCADE,
	filename     TEXT NOT NULL,
	filehash     TEXT NOT NULL,
	hash_algo    hashAlgo,
	status       status,
	error        TEXT,
	stable_id    INTEGER,
	reencryption TEXT,
	created_at   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
	last_modified TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
);

-- Updating the timestamp when the status is modified
CREATE FUNCTION status_updated() RETURNS TRIGGER
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.last_modified := current_date;
  RETURN NEW;
END;
$$;

CREATE TRIGGER trigger_status_updated
  BEFORE UPDATE ON files
  FOR EACH ROW
  WHEN (OLD.status IS DISTINCT FROM NEW.status)
  EXECUTE PROCEDURE status_updated();

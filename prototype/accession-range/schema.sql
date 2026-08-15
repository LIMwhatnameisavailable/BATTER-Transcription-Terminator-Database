PRAGMA foreign_keys = ON;

CREATE TABLE assemblies (
  accession TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  reference_name TEXT NOT NULL,
  reference_length INTEGER NOT NULL CHECK (reference_length > 0),
  release_version TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pilot', 'published', 'withdrawn'))
);

CREATE TABLE assets (
  asset_key TEXT PRIMARY KEY,
  assembly_accession TEXT NOT NULL REFERENCES assemblies(accession),
  role TEXT NOT NULL,
  format TEXT NOT NULL,
  object_path TEXT NOT NULL UNIQUE,
  origin_url TEXT,
  content_type TEXT NOT NULL,
  byte_size INTEGER NOT NULL CHECK (byte_size >= 0),
  sha256 TEXT NOT NULL CHECK (length(sha256) = 64),
  active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);

CREATE TABLE tracks (
  track_id TEXT PRIMARY KEY,
  assembly_accession TEXT NOT NULL REFERENCES assemblies(accession),
  source_id TEXT NOT NULL,
  name TEXT NOT NULL,
  assay TEXT NOT NULL,
  evidence_class TEXT NOT NULL,
  record_count INTEGER NOT NULL CHECK (record_count >= 0),
  asset_key TEXT NOT NULL REFERENCES assets(asset_key),
  display_order INTEGER NOT NULL
);

CREATE INDEX assets_by_assembly ON assets(assembly_accession, role);
CREATE INDEX tracks_by_assembly ON tracks(assembly_accession, display_order);

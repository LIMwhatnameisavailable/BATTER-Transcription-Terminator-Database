-- Asset-level redistribution correction for the four Lalanne Rend-seq sources.
-- Article access status no longer hides independently public NCBI/GEO assets
-- or BTED-standardized outputs. S1_002 and author-specific fields stay private.

UPDATE sources
SET redistribution_status = 'verified_redistributable'
WHERE release_version = 'v0.2.0'
  AND source_id IN ('BATTER_S1_001', 'BATTER_S1_003', 'BATTER_S1_004', 'BATTER_S1_005');

UPDATE tracks
SET is_public = 1
WHERE release_version = 'v0.2.0'
  AND source_id IN ('BATTER_S1_001', 'BATTER_S1_003', 'BATTER_S1_004', 'BATTER_S1_005');

UPDATE assets
SET origin_url = replace(
      origin_url,
      '/resolve/d12190e434057edaf2c2bdbf19132f1e41873c38/',
      '/resolve/463cfc8bd582a5ed9d2c426822148c3f1e56c4d0/'
    )
WHERE release_version = 'v0.2.0';

UPDATE assets
SET redistribution_status = 'verified_redistributable',
    is_public = 1,
    supports_range = 1
WHERE release_version = 'v0.2.0'
  AND (
    source_id IN ('BATTER_S1_001', 'BATTER_S1_003', 'BATTER_S1_004', 'BATTER_S1_005')
    OR assembly_accession IN ('GCF_000005845.1', 'GCF_000009045.1', 'GCF_000022005.1', 'GCF_001456255.1')
  );

INSERT INTO assemblies VALUES (
  'GCF_000739105.1', 'Streptomyces lividans TK24', 'CP009124.1', 8345283,
  'v0.2.0-prototype', 'pilot'
);

INSERT INTO assets VALUES
('GCF_000739105.1/reference/reference.fna', 'GCF_000739105.1', 'reference_sequence', 'FASTA', 'assemblies/GCF_000739105.1/reference/reference.fna', NULL, 'text/plain', 8484410, '14f117887bc4c29f9336aef4b8ace10fef9cec66a92d37076c396b4aff8017af', 1),
('GCF_000739105.1/reference/reference.fna.fai', 'GCF_000739105.1', 'reference_index', 'FAI', 'assemblies/GCF_000739105.1/reference/reference.fna.fai', NULL, 'text/plain', 28, '755121207de0dc2542b2c2a642208e78152ae32901713869b8f54f0b4ed55987', 1),
('GCF_000739105.1/reference/genes.gff3.gz', 'GCF_000739105.1', 'gene_annotation', 'GFF3_BGZF', 'assemblies/GCF_000739105.1/reference/genes.gff3.gz', NULL, 'application/gzip', 142587, 'dcc5b339e6b8f31289c9db6cbb0eda99a51faf4d7be8d5076ff7a86b8f247893', 1),
('GCF_000739105.1/reference/genes.gff3.gz.tbi', 'GCF_000739105.1', 'gene_annotation_index', 'TBI', 'assemblies/GCF_000739105.1/reference/genes.gff3.gz.tbi', NULL, 'application/octet-stream', 1589, '042eb4a3095719cb60ec73fa8feb6ce808b908f7b1661af75dcbc6265b7f01b2', 1),
('GCF_000739105.1/tracks/BATTER_S1_007.endpoints.bed', 'GCF_000739105.1', 'endpoint_track', 'BED6', 'assemblies/GCF_000739105.1/tracks/BATTER_S1_007.endpoints.bed', NULL, 'text/plain', 74306, '8926da72886e01d8fd7c87ecb3b8a5851abca6fdf161be25b11c4f36a130f083', 1),
('GCF_000739105.1/tracks/BATTER_S1_013.endpoints.bed', 'GCF_000739105.1', 'endpoint_track', 'BED6', 'assemblies/GCF_000739105.1/tracks/BATTER_S1_013.endpoints.bed', NULL, 'text/plain', 41063, 'a2037893175f9498f1e11c47a903bf5f9845ec178486349e600abb2e4995247d', 1);

INSERT INTO tracks VALUES
('BATTER_S1_007_termseq_teps', 'GCF_000739105.1', 'BATTER_S1_007', 2019, '31555254', 'records/BATTER_S1_007.html', 'Author-called Term-seq TEPs (Lee 2019)', 'Term-seq / dRNA-seq', 'author_called_endpoint', 1640, 'GCF_000739105.1/tracks/BATTER_S1_007.endpoints.bed', 1),
('BATTER_S1_013_termseq_tts', 'GCF_000739105.1', 'BATTER_S1_013', 2020, '33319794', 'records/BATTER_S1_013.html', 'Author-called Term-seq TTS (Lee 2020)', 'Term-seq / dRNA-seq', 'author_called_endpoint', 1208, 'GCF_000739105.1/tracks/BATTER_S1_013.endpoints.bed', 2);

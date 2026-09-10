#!/usr/bin/env python3
"""Parse terminators.flanked.fa.gz headers (streaming)."""
import csv, gzip, json, sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path('D:/SEU/实习/BATTER数据整理/BTED/repo/site/data/augmentation')
FASTA = HERE / 'terminators.flanked.fa.gz'
STATS = HERE / 'combined-statistics.txt'

def extract_otu(line):
    if not line.startswith('>'): return None
    rest = line[1:]
    colon = rest.find(':')
    if colon < 0: return None
    otu = rest[:colon]
    if not otu.startswith('OTU-'): return None
    parts = rest[colon+1:].split(':')
    gene = None
    if len(parts) >= 3:
        g = parts[1]
        if not g.isdigit() and not g.startswith('00'):
            gene = g.split(',')[0]
    rest2 = rest[colon+1:]
    dcol = rest2.find('::')
    strand = None
    if dcol >= 0:
        tail = rest2[dcol+2:]
        p = tail.rfind('(')
        if p >= 0 and p+2 < len(tail) and tail[p+1] in '+-':
            strand = tail[p+1]
    return otu, gene, strand

def main():
    oc = Counter()
    og = defaultdict(set)
    osd = defaultdict(lambda: Counter())
    total = skip = hcount = 0

    with gzip.open(FASTA, 'rt', encoding='utf-8') as f:
        for line in f:
            if not line.startswith('>'): continue
            hcount += 1
            r = extract_otu(line)
            if r is None:
                skip += 1
                if skip <= 3: sys.stderr.write('skip: %s\n' % line.rstrip()[:80])
                continue
            otu, gene, strand = r
            oc[otu] += 1
            if gene: og[otu].add(gene)
            if strand: osd[otu][strand] += 1
            total += 1
            if total % 500000 == 0:
                print('  ... %d parsed (%d headers)' % (total, hcount))

    print('Headers: %d' % hcount)
    print('Parsed: %d' % total)
    print('Skipped: %d' % skip)
    print('Unique OTU ids: %d' % len(oc))

    print('Loading combined-statistics.txt ...')
    tax = {}
    sta = {}
    with open(STATS, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            o = row['otu_id']
            tax[o] = row.get('taxonomy', '')
            sta[o] = {k: row.get(k, '') for k in ['genome_id','type','study','phylum','completeness','contamination','rho_homologs','number','genome_size']}

    per = []
    for otu, cnt in oc.most_common():
        s = sta.get(otu, {})
        per.append({
            'otu_id': otu,
            'augmented_instances': cnt,
            'forward': osd[otu].get('+', 0),
            'reverse': osd[otu].get('-', 0),
            'unique_genes': len(og[otu]),
            'example_genes': sorted(list(og[otu]))[:5],
            'taxonomy': tax.get(otu, ''),
            'phylum': s.get('phylum', ''),
            'genome_id': s.get('genome_id', ''),
            'completeness': s.get('completeness', ''),
            'contamination': s.get('contamination', ''),
            'rho_homologs': s.get('rho_homologs', ''),
            'number_predicted_3ends': s.get('number', '0'),
        })

    meta = {'source': 'BATTER augmentation pipeline', 'total_otus': len(per), 'total_instances': total, 'total_sequences': hcount}
    out = {'metadata': meta, 'otus': per}
    hp = HERE / 'per_otu_index.json'
    hp.write_text(json.dumps(out, indent=2), encoding='utf-8')
    print('Written %s (%d OTUs)' % (hp, len(per)))
    print('Total augmentation instances: %d' % sum(p['augmented_instances'] for p in per))

if __name__ == '__main__':
    main()

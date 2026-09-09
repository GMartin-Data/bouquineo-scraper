# Journal de bord — Brief scraping Bouquineo

## J1 — 2026-09-09

### Décisions de cadrage (avant-projet, 2026-09-08)
- Stack : Scrapy 2.18 / Python 3.14.7 (uv) / PostgreSQL 17 (Docker) / psycopg3.
- Architecture : deux spiders dédiés (`listing` puis `books`), sortie JSONL en
  écriture au fil de l'eau — le fichier de sortie sert d'état de reprise
  (aucune dépendance à la base pendant le crawl).
- Chargement découplé : `db/schema.sql` + `db/load.py`, upsert sur UPC.
- Layout Scrapy canonique (pas de `src/` : application, pas une lib).

### Scaffolding
- `git init` + `uv init` (Python 3.14.7 pinné), `scrapy startproject bouquineo .`.
- Vérifié sur PyPI : Scrapy 2.18.0 supporte officiellement Python 3.14.
- Postgres 17 en Docker (compose + healthcheck), credentials via `.env`
  (gabarit `env.example`).

### Blocages / résolutions
- (néant à ce stade)

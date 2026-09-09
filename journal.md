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

### Reconnaissance (Phase 1, matin)
- **robots.txt : n'existe pas (HTTP 404)** → par convention, aucune restriction
  de crawl. Notre politesse (délai, User-Agent) reste auto-imposée.
- Catalogue : 1 000 résultats annoncés sur l'accueil, pager « Page 1 of 50 »,
  20 livres/page. Pagination via lien « next » relatif (`catalogue/page-2.html`,
  puis `page-3.html`) ; les URLs `catalogue/page-N.html` sont prévisibles mais on
  suivra le lien next (robuste si la structure change).
- **Piège URLs relatives confirmé** : depuis l'accueil, les liens fiche sont
  `catalogue/xxx/index.html` ; depuis page-2, `xxx/index.html` (sans préfixe).
  Concaténation naïve = 404. Solution : `response.urljoin()`.
- **Piège note confirmé** : la note vit dans la classe CSS
  (`star-rating Three`), aucun chiffre dans le texte.
- Fiche produit : tous les champs localisés — h1 (titre), table striped (UPC,
  Price excl/incl tax, Tax, Availability avec « (N available) », Number of
  reviews), breadcrumb (catégorie, 3e li), description (p après
  #product_description).
- **Observation prix/taxe (4 fiches)** : Price excl. = Price incl., Tax = £0.00
  partout. **Number of reviews = 0 partout.** À confirmer sur les 1 000 en J2
  (jq) pour la note d'observation — mais ces champs semblent factices.

### Blocages / résolutions
- `scrapy shell -c` n'accepte qu'une *expression* Python (il passe par `eval`) :
  les `print(...)` multiples séparés par `;` lèvent une SyntaxError. Contourné
  avec un tuple de `print(...)`.
- Script de recon jetable avec `requests` : les `£` sortaient en `Â£` —
  mauvaise détection d'encodage par requests (latin-1 au lieu d'UTF-8), là où
  Scrapy détecte correctement. Sans conséquence (script jetable), mais bonne
  piqûre de rappel encodage.

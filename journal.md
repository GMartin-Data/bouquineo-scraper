# Journal de bord — Brief scraping Bouquineo

## Prochaine session (J2)

État : jalon J1 atteint et commité (1 000 livres dans `data/listing.jsonl`,
tests verts, historique poussé). Programme J2, dans l'ordre
(roadmap détaillée : `../brief_scraping/notes/00-roadmap-previsionnelle.md`) :

1. Spider `books` : un livre enrichi de bout en bout (UPC, prix, taxe, stock
   réel, avis, description, catégorie), vérifié contre le navigateur, puis
   généralisation. Sélecteurs déjà cartographiés dans la note 02.
2. Robustesse — le cœur évalué du brief : reprise par relecture du JSONL dans
   `async start()` (clé = URL, cf. « deux clés, deux moments » note 02),
   errback + erreurs journalisées/sautées, mode échantillon `-a limit=N`.
3. Crawl complet (~10 min) + test d'interruption volontaire (Ctrl-C, relance,
   preuve de reprise dans les logs).
4. Si le rythme tient : PostgreSQL (`db/schema.sql` + `db/load.py`, upsert
   `ON CONFLICT (upc)`) — sinon glisse en J3 sans douleur.

Rappel outillage : Postgres pas encore démarré (`cp env.example .env` puis
`docker compose up -d`, à faire au moment du point 4).

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

### Spider `listing` (Phase 1, après-midi)
- Implémenté : `items.py` (BookListItem), `parsing.py` (décodeurs prix/note/
  stock, `None` sur inattendu), `pipelines.py` (JSONL au fil de l'eau, flush
  par ligne), `spiders/listing.py` (pagination par `response.follow`).
- **Jalon J1 atteint** : `uv run scrapy crawl listing` → 50 pages parcourues
  (loggées), 1 000 items, 0 erreur, ~31 s. Vérifié au `jq` : 1 000 URLs
  distinctes, notes 1-5 bien distribuées, zéro champ null, relance idempotente.
- **6ᵉ piège découvert** : le texte du lien tronque les titres longs
  (`A Light in the ...`) — le titre complet ne vit que dans l'attribut
  `title` du `<a>`. Vérifié au shell avant d'écrire le spider.

### Tests (décidés en débrief)
- Positionnement : pour un scraper, la vérité vit sur le serveur — la
  **détection** (garde-fous d'exécution, logs, CLOSESPIDER_ERRORCOUNT) prime
  sur la prévention. Les tests unitaires ne gardent que la couche pure.
- Fait : 11 tests pytest sur `parsing.py` (contrat : inattendu → None, jamais
  d'exception) + 3 Scrapy contracts sur `parse()` (`scrapy check`, vérification
  *en ligne* contre le site réel). CI écartée (projet 2 jours, rien à protéger
  en continu).

### Blocages / résolutions
- `uv run pytest` → `ModuleNotFoundError: No module named 'bouquineo'` alors
  que `scrapy crawl` fonctionnait : layout applicatif flat = package jamais
  installé dans le venv ; scrapy ajoute lui-même la racine à `sys.path`
  (service du marqueur scrapy.cfg), pytest insère seulement `tests/`. Résolu
  par `[tool.pytest.ini_options] pythonpath = ["."]` — on règle l'outil, pas
  le projet (documenté en détail : `~/explain/`).
- Dépréciations Scrapy 2.18 rencontrées : `start_urls` → idiome moderne
  `async def start()` ; méthodes de pipeline sans argument `spider` → factory
  `from_crawler` + `self.crawler.spider`.
- Conflit Ruff (RUF012, attributs de classe mutables → `ClassVar`) vs Pyright
  (`start_urls` est une variable d'instance dans la classe de base) : résolu
  en adoptant `async def start()`, qui supprime l'objet du litige.
- `scrapy shell -c` n'accepte qu'une *expression* Python (il passe par `eval`) :
  les `print(...)` multiples séparés par `;` lèvent une SyntaxError. Contourné
  avec un tuple de `print(...)`.
- Script de recon jetable avec `requests` : les `£` sortaient en `Â£` —
  mauvaise détection d'encodage par requests (latin-1 au lieu d'UTF-8), là où
  Scrapy détecte correctement. Sans conséquence (script jetable), mais bonne
  piqûre de rappel encodage.

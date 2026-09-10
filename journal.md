# Journal de bord — Brief scraping Bouquineo

## Prochaine session (démo)

État : **projet fonctionnellement clos** — chaîne complète listing → books →
Postgres, robustesse prouvée, livrables rédigés. Reste pour la démo :

- Répétition : dérouler les auto-tests des notes 02, 06, 07, 08 ; savoir
  rejouer la séquence de preuve (crawl `-a limit=N` ×2 → reprise visible,
  `db/load.py` ×2 → idempotence).
- Findings [4]-[6] de la code-review laissés ouverts (arbitrages de
  convention : type hints sur callbacks Scrapy, `print()` de sortie de
  script, `assert` sous `-O`) — non bloquants, à trancher hors brief.
- `tasks/lessons-inbox.md` versionné (décision fin J2).

## J2 — 2026-09-10

### Programme réalisé (les 4 points, dans l'ordre)

1. **Spider `books`** (entamé fin J1) : les 11 champs enrichis parsés de bout
   en bout — table th/td lue en dict, décodeurs purs (`parse_count` ajouté,
   test-first), fiche témoin vérifiée champ à champ contre le navigateur
   (`scrapy parse`), 3 contracts live.
2. **Robustesse** : reprise par relecture de `books.jsonl` dans `start()`
   (`seen_urls`, ne lève jamais — testée fichier absent / ligne tronquée /
   séparateurs Unicode) ; seuil d'échecs **déplacé dans l'errback** —
   découverte vérifiée à la source : `CLOSESPIDER_ERRORCOUNT` n'écoute que
   les exceptions de callback, il ne compterait rien avec notre parsing
   tolérant (`max_failures = 10` + `CloseSpider`, le réglage Scrapy reste en
   filet anti-bug) ; mode `-a limit=N` compté *après* le filtre de reprise
   (deux runs `limit=5` → livres 1-5 puis 6-10, démontré en live).
3. **Crawl complet + interruption** : SIGINT en plein vol via `timeout`
   (arrêt brutal — double signal, cf. note 07) puis kill d'un second run →
   1 000 livres collectés en 3 runs (84 + 23 + 893), reprise loggée à chaque
   relance, **0 échec réseau**, 1 000 UPC et URLs distincts.
4. **PostgreSQL** : `db/schema.sql` (NUMERIC pour l'argent, CHECK sur rating,
   NULL stock = inconnu) + `db/load.py` (psycopg3, upsert `ON CONFLICT
   (upc)`, transaction unique, lecture stricte fail-fast). **Idempotence
   prouvée** : deux chargements → 1 000 rows les deux fois.

### Réponses du brief (détail : notes_obs.md, commitée)

- **Ruptures : aucune** (stock 1-22, zéro « Out of stock ») ; le signal
  réassort est le stock faible : **420 titres ≤ 5, dont 98 à l'unité**.
- **Mieux notés** : 196 titres à 5 étoiles ; par catégorie (≥ 10 livres) :
  Poetry 3,53 — distribution des notes quasi uniforme (données générées).
- **Champs morts confirmés n=1000** : tax = 0, num_reviews = 0, HT = TTC.
- **Doublon de titre prévu par le brief trouvé** : « The Star-Touched
  Queen » ×2 (999 titres distincts / 1 000 UPC) — même catégorie, seuls
  UPC/prix/stock les distinguent.

### Rituel de clôture

`/code-review high` sur la plage du jour (`6dda759..HEAD`) : 6 findings,
aucun ≥ HIGH. Corrigés : affirmation fausse dans notes_obs ([1]), conninfo
interpolée → kwargs psycopg ([2]), `__future__` manquants ([3]). Ouverts :
[4]-[6] (conventions, voir « Prochaine session »).

### Blocages / résolutions

### Blocages / résolutions

- **`splitlines()` casse du JSONL valide (U+2028/U+2029)** — `db/load.py`
  plante à sa première exécution (`JSONDecodeError: Unterminated string`)
  alors que `wc -l` et `jq` voient 1 000 lignes parfaitement valides. Le
  fichier est sain ; c'est la *lecture* qui casse : `str.splitlines()` coupe
  sur la définition **Unicode** de la ligne — donc aussi sur U+2028 (LINE
  SEPARATOR) et U+2029 (PARAGRAPH SEPARATOR), présents **bruts** dans deux
  descriptions (« Batman: Europa », « Having the Barbarian's Baby ») parce
  que `json.dumps(..., ensure_ascii=False)` ne les échappe pas — JSON
  légal. Résultat : 1 000 lignes réelles → 1 003 « lignes » Python, dont 5
  fragments imparsables.
  - **Gravité au-delà du loader** : le même idiome vivait dans `seen_urls`
    (reprise) — ces 2 URLs n'étaient jamais reconnues « vues », donc
    re-crawlées **et dupliquées à chaque reprise**. Invisible sur notre
    fichier final uniquement parce que les 2 livres sont tombés dans le
    dernier run, sans reprise après eux. Troisième site touché : le
    `start()` du spider (lecture de `listing.jsonl`).
  - **Fix** : itérer le fichier ouvert (`for line in file`), qui ne coupe
    que sur `\n` — trois sites corrigés d'un même geste, test de régression
    avec `\u2028`/`\u2029` littéraux, double chargement revérifié
    (1 000 lignes → 1 000 rows, deux fois).
  - **Leçon** : « ligne » a deux définitions — celle du contrat JSONL
    (`\n` seul) et celle d'Unicode (`splitlines()`). `jq` lisait la
    première, Python la seconde ; le bug vivait dans l'écart. Détail
    complet : note 07, section « Le contrat JSONL ».

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

# Notes d'observation — données books.toscrape.com

> Profilage réalisé sur le catalogue complet (n = 1 000), après chargement en
> base. Méthode : soupçons relevés sur 4 fiches en J1 (journal), transformés
> en faits par `jq` sur `data/books.jsonl` et SQL sur la table `books`.
> Principe appliqué : les champs sont collectés **bruts** (fidélité de la
> zone d'atterrissage) ; les conclusions sur leur utilisabilité vivent ici,
> pas dans le code de collecte.

## 1. Champs morts (constants sur les 1 000 livres)

| Champ | Constat (n = 1 000) | Verdict |
|---|---|---|
| `tax` | `£0.00` partout (0 exception) | **Mort** — aucune information |
| `price_excl_tax` vs `price_incl_tax` | strictement égaux partout | **Redondants** — un seul prix en analyse |
| `num_reviews` | `0` partout | **Mort** — la question « avis » du brief est sans objet sur ce site |

Un champ constant est un champ mort, quel que soit son nom : le schéma
(« Price excl./incl. tax ») promet une histoire comptable que les valeurs ne
tiennent pas. C'est du remplissage de bac à sable. **Conséquence analyse** :
utiliser `price_incl_tax` comme prix unique, ignorer `tax` et `num_reviews`.
Les trois restent en base par fidélité à la source (et le jour où le site
« s'anime », la chaîne les capte sans modification).

## 2. Stock : zéro rupture, mais 42 % du catalogue en stock faible

- `stock` va de **1 à 22** ; aucune fiche « Out of stock » (0 rupture,
  0 quantité inconnue). La question « quels titres en rupture ? » a une
  réponse exacte : **aucun** — réponse en soi, à énoncer telle quelle.
- **420 titres à stock ≤ 5** (42 % du catalogue), dont **98 à l'unité** —
  c'est là que vit le signal « réassort » pour la responsable des achats.
- Requête de référence (top stock faible) : `SELECT title, category, stock
  FROM books ORDER BY stock ASC LIMIT N;`

## 3. Notes : distribution quasi uniforme

226 / 196 / 203 / 179 / 196 livres pour les notes 1 → 5 : une distribution
plate, sans biais qualité — cohérente avec des données générées. « Les mieux
notés » = les **196 titres à 5 étoiles** (filtre `rating = 5`) ; par
catégorie (≥ 10 livres), Poetry (3.53), Humor (3.40) et Young Adult (3.30)
dominent — écarts faibles, à ne pas surinterpréter.

## 4. Titre ≠ clé : le doublon prévu par le brief existe

**999 titres distincts pour 1 000 livres** : « The Star-Touched Queen »
existe en deux exemplaires (UPC différents, catégories différentes). La
`PRIMARY KEY (upc)` a accepté les 1 000 lignes sans conflit — l'unicité de
l'UPC est *prouvée* par le chargement, pas supposée. Toute jointure ou
déduplication par titre aurait silencieusement perdu ou fusionné un livre.

## 5. Descriptions : trois artefacts de bac à sable

- **2 fiches sans description** (champ `NULL` en base — toléré à la collecte).
- **943 / 998 descriptions se terminent par « ...more »** : suffixe d'UI
  aspiré dans la donnée, sans « suite » réelle derrière.
- Sur échantillon : la description embarque parfois un **extrait tronqué
  suivi du texte complet** (duplication interne, ex. « Batman: Europa »).
- Deux descriptions contiennent des séparateurs Unicode **U+2028/U+2029
  bruts** — légaux en JSON, mais piégeux pour tout outil qui découpe « par
  lignes » à la mode Unicode (incident documenté au journal, section J2).

**Conséquence analyse** : la description est utilisable pour de l'affichage,
pas pour du NLP sérieux sans nettoyage (suffixe, duplication, séparateurs).

## 6. Fiabilité de la collecte (pour mémoire)

1 000 fiches collectées, **0 échec réseau**, 1 000 UPC distincts, 1 000 URLs
distinctes ; chargement idempotent vérifié (deux exécutions → 1 000 lignes).
Les chiffres de cette note sont reproductibles : `jq` sur
`data/books.jsonl`, SQL sur la table `books`.

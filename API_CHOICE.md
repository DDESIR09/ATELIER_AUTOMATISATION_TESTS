# API Choice

- **Étudiant :** Dylan Desir
- **API choisie :** Agify
- **URL base :** https://api.agify.io
- **Documentation officielle / README :** https://agify.io/
- **Auth :** None (aucune authentification requise)

## Endpoints testés

- `GET https://api.agify.io?name={prenom}` → prédit l'âge moyen statistique des personnes portant ce prénom
- `GET https://api.agify.io?name={prenom}&country_id={code_pays}` → même chose, mais filtré par pays (ex: `country_id=FR`)

## Hypothèses de contrat

La réponse est un objet JSON contenant :

| Champ | Type | Description |
|---|---|---|
| `name` | string | Le prénom envoyé en paramètre |
| `age` | integer ou null | L'âge moyen prédit (null si pas assez de données) |
| `count` | integer | Le nombre d'occurrences du prénom dans la base |
| `country_id` | string (optionnel) | Le code pays si fourni en paramètre |

**Codes HTTP attendus :**
- `200 OK` pour une requête valide
- `422 Unprocessable Entity` si le paramètre `name` est manquant
- `429 Too Many Requests` si le quota journalier est dépassé

## Limites / rate limiting connu

- **100 requêtes gratuites par jour** par IP (sans clé API)
- Au-delà, l'API renvoie un code `429`
- Pas de timeout strict côté serveur, mais on fixera un timeout client à 3 secondes

## Risques

- **Instabilité** : très faible, Agify est un service stable depuis plusieurs années
- **Downtime** : rare, mais à surveiller via le test de disponibilité
- **CORS** : non bloquant car on appelle l'API depuis Python (pas depuis un navigateur)
- **Quota** : la limite de 100 requêtes/jour impose un rythme prudent (1 run / 5 min, 20 requêtes max/run)
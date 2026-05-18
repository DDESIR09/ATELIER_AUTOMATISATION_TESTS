"""
Tests automatisés de l'API Agify.

Chaque fonction de test :
- prend un client (ApiClient) en paramètre
- retourne un dict { name, status: "PASS"|"FAIL", details, latency_ms }
"""


def _result(name, status, latency_ms=0, details=""):
    """Construit un dict de résultat de test au format standard."""
    return {
        "name": name,
        "status": status,
        "latency_ms": latency_ms,
        "details": details,
    }


# ============================================================
# A. Tests "Contrat" (fonctionnels)
# ============================================================

def test_status_200(client):
    """Vérifie que l'API renvoie bien un code HTTP 200 pour une requête valide."""
    r = client.get("", {"name": "michael"})
    if r["error"]:
        return _result("HTTP 200 attendu", "FAIL", r["latency_ms"], f"Erreur réseau : {r['error']}")
    if r["status_code"] == 200:
        return _result("HTTP 200 attendu", "PASS", r["latency_ms"])
    return _result("HTTP 200 attendu", "FAIL", r["latency_ms"],
                   f"Code reçu : {r['status_code']}")


def test_content_type_json(client):
    """Vérifie que la réponse est bien un JSON parsable."""
    r = client.get("", {"name": "alice"})
    if r["json"] is not None and isinstance(r["json"], dict):
        return _result("Content-Type JSON", "PASS", r["latency_ms"])
    return _result("Content-Type JSON", "FAIL", r["latency_ms"],
                   "Réponse non parsable en JSON")


def test_required_fields(client):
    """Vérifie la présence des 3 champs obligatoires : name, age, count."""
    r = client.get("", {"name": "bob"})
    if r["json"] is None:
        return _result("Champs obligatoires", "FAIL", r["latency_ms"], "Pas de JSON")
    required = ["name", "age", "count"]
    missing = [f for f in required if f not in r["json"]]
    if not missing:
        return _result("Champs obligatoires", "PASS", r["latency_ms"])
    return _result("Champs obligatoires", "FAIL", r["latency_ms"],
                   f"Champs manquants : {missing}")


def test_field_types(client):
    """Vérifie le typage des champs : name=str, count=int, age=int|None."""
    r = client.get("", {"name": "claire"})
    if r["json"] is None:
        return _result("Types des champs", "FAIL", r["latency_ms"], "Pas de JSON")

    data = r["json"]
    errors = []
    if not isinstance(data.get("name"), str):
        errors.append("name n'est pas un string")
    if not isinstance(data.get("count"), int):
        errors.append("count n'est pas un int")
    if data.get("age") is not None and not isinstance(data.get("age"), int):
        errors.append("age n'est ni int ni null")

    if not errors:
        return _result("Types des champs", "PASS", r["latency_ms"])
    return _result("Types des champs", "FAIL", r["latency_ms"], "; ".join(errors))


def test_name_echoed(client):
    """Vérifie que le prénom envoyé est bien renvoyé dans la réponse."""
    r = client.get("", {"name": "Dylan"})
    if r["json"] is None:
        return _result("Echo du prénom", "FAIL", r["latency_ms"], "Pas de JSON")
    returned_name = r["json"].get("name", "").lower()
    if returned_name == "dylan":
        return _result("Echo du prénom", "PASS", r["latency_ms"])
    return _result("Echo du prénom", "FAIL", r["latency_ms"],
                   f"Attendu 'dylan', reçu '{returned_name}'")


# ============================================================
# B. Tests "Robustesse" (cas d'erreur attendus)
# ============================================================

def test_missing_name_param(client):
    """
    Vérifie que l'absence du paramètre 'name' renvoie une erreur 4xx.
    Agify renvoie 422 dans ce cas.
    """
    r = client.get("", None)
    if r["error"]:
        return _result("Paramètre manquant → 4xx", "FAIL",
                       r["latency_ms"], f"Erreur réseau : {r['error']}")
    if 400 <= r["status_code"] < 500:
        return _result("Paramètre manquant → 4xx", "PASS", r["latency_ms"],
                       f"Code reçu : {r['status_code']}")
    return _result("Paramètre manquant → 4xx", "FAIL", r["latency_ms"],
                   f"Code reçu : {r['status_code']} (attendu 4xx)")


def test_country_filter(client):
    """Vérifie que le filtre par pays (country_id) fonctionne."""
    r = client.get("", {"name": "pierre", "country_id": "FR"})
    if r["json"] is None:
        return _result("Filtre pays (FR)", "FAIL", r["latency_ms"], "Pas de JSON")
    if r["json"].get("country_id") == "FR":
        return _result("Filtre pays (FR)", "PASS", r["latency_ms"])
    return _result("Filtre pays (FR)", "FAIL", r["latency_ms"],
                   f"country_id reçu : {r['json'].get('country_id')}")


# ============================================================
# C. Test "QoS" (performance)
# ============================================================

def test_latency_under_2s(client):
    """Vérifie que la latence reste sous 2 secondes."""
    r = client.get("", {"name": "anna"})
    if r["latency_ms"] < 2000:
        return _result("Latence < 2000 ms", "PASS", r["latency_ms"])
    return _result("Latence < 2000 ms", "FAIL", r["latency_ms"],
                   f"Latence trop élevée : {r['latency_ms']} ms")


# ============================================================
# Liste de tous les tests (utilisée par le runner)
# ============================================================

ALL_TESTS = [
    test_status_200,
    test_content_type_json,
    test_required_fields,
    test_field_types,
    test_name_echoed,
    test_missing_name_param,
    test_country_filter,
    test_latency_under_2s,
]
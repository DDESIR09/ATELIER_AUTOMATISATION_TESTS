"""
Runner : exécute tous les tests et calcule les métriques QoS.
"""

from datetime import datetime, timezone
from tester.client import ApiClient
from tester.tests import ALL_TESTS


def run_all_tests(base_url="https://api.agify.io"):
    """
    Exécute tous les tests sur l'API cible et retourne un dict structuré :
    {
        "api": ...,
        "timestamp": ...,
        "summary": { passed, failed, error_rate, latency_ms_avg, latency_ms_p95, availability },
        "tests": [ ... ]
    }
    """
    client = ApiClient(base_url, timeout=3, max_retries=1)
    results = []

    # 1. Exécution séquentielle de tous les tests
    for test_func in ALL_TESTS:
        try:
            result = test_func(client)
        except Exception as e:
            # Si un test plante de manière inattendue, on l'enregistre quand même
            result = {
                "name": test_func.__name__,
                "status": "FAIL",
                "latency_ms": 0,
                "details": f"Exception inattendue : {e}",
            }
        results.append(result)

    # 2. Calcul des métriques QoS
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    total = len(results)

    # Taux d'erreur : proportion de tests échoués (entre 0 et 1)
    error_rate = round(failed / total, 3) if total > 0 else 0

    # Disponibilité : 1 si au moins un test PASS (l'API répond), 0 sinon
    availability = 1 if passed > 0 else 0

    # Latence moyenne (sur les tests qui ont effectivement appelé l'API)
    latencies = [r["latency_ms"] for r in results if r["latency_ms"] > 0]
    if latencies:
        latency_avg = round(sum(latencies) / len(latencies))
        latency_p95 = _percentile(latencies, 95)
    else:
        latency_avg = 0
        latency_p95 = 0

    return {
        "api": "Agify",
        "base_url": base_url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "error_rate": error_rate,
            "availability": availability,
            "latency_ms_avg": latency_avg,
            "latency_ms_p95": latency_p95,
        },
        "tests": results,
    }


def _percentile(values, percent):
    """
    Calcule le percentile p (ex: p95) sur une liste de valeurs.
    Implémentation simple sans dépendre de numpy.
    """
    if not values:
        return 0
    sorted_values = sorted(values)
    index = int(len(sorted_values) * percent / 100)
    # On clampe pour éviter de sortir de la liste
    index = min(index, len(sorted_values) - 1)
    return sorted_values[index]
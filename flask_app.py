"""
Application Flask — Atelier Automatisation des Tests d'API.
Routes :
- /           : consignes de l'atelier
- /dashboard  : tableau de bord des runs
- /run        : déclenche un nouveau run de tests
- /health     : endpoint de santé (bonus)
- /api/runs   : export JSON de l'historique (bonus)
"""

from flask import Flask, render_template, redirect, url_for, jsonify
from datetime import datetime, timezone

from tester.runner import run_all_tests
from storage import save_run, list_runs, get_last_run, count_runs

app = Flask(__name__)

# Anti-spam : on garde en mémoire le timestamp du dernier run déclenché
# pour éviter qu'un utilisateur lance des runs à la chaîne
_last_run_timestamp = None
MIN_SECONDS_BETWEEN_RUNS = 10  # 10 secondes minimum entre deux runs manuels


@app.get("/")
def consignes():
    """Page d'accueil : affiche les consignes de l'atelier."""
    return render_template("consignes.html")


@app.get("/dashboard")
def dashboard():
    """Tableau de bord : affiche le dernier run en détail + l'historique."""
    last_run = get_last_run()
    history = list_runs(limit=20)
    total = count_runs()

    return render_template(
        "dashboard.html",
        last_run=last_run,
        history=history,
        total_runs=total,
    )


@app.get("/run")
def run():
    """Déclenche un nouveau run de tests, l'enregistre, puis redirige vers /dashboard."""
    global _last_run_timestamp

    # Anti-spam basique : pas plus d'un run toutes les 10 secondes
    now = datetime.now(timezone.utc)
    if _last_run_timestamp is not None:
        elapsed = (now - _last_run_timestamp).total_seconds()
        if elapsed < MIN_SECONDS_BETWEEN_RUNS:
            return (
                f"Trop de runs récents. Réessayez dans {int(MIN_SECONDS_BETWEEN_RUNS - elapsed)}s.",
                429,
            )

    _last_run_timestamp = now

    # Exécution + sauvegarde
    result = run_all_tests()
    save_run(result)

    return redirect(url_for("dashboard"))


@app.get("/health")
def health():
    """
    Endpoint de santé (bonus).
    Renvoie 200 OK si la solution est opérationnelle.
    Inclut quelques infos rapides sur l'état du système.
    """
    last_run = get_last_run()

    if last_run is None:
        status = "no_data"
        message = "Aucun run enregistré pour l'instant"
        last_timestamp = None
        last_availability = None
    else:
        status = "ok" if last_run["summary"]["availability"] == 1 else "degraded"
        message = (
            f"Dernier run : {last_run['summary']['passed']}/{last_run['summary']['total']} tests OK"
        )
        last_timestamp = last_run["timestamp"]
        last_availability = last_run["summary"]["availability"]

    return jsonify({
        "service": "Atelier Tests API Agify",
        "status": status,
        "message": message,
        "total_runs": count_runs(),
        "last_run_timestamp": last_timestamp,
        "last_availability": last_availability,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    })


@app.get("/api/runs")
def api_runs():
    """Export JSON de l'historique des runs (bonus)."""
    return jsonify({
        "total": count_runs(),
        "runs": list_runs(limit=100),
    })


if __name__ == "__main__":
    # Utile en local uniquement (PythonAnywhere a son propre lanceur)
    app.run(host="0.0.0.0", port=5000, debug=True)
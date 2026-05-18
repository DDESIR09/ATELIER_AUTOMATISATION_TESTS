"""
Wrapper HTTP pour les tests d'API.
Gère : timeout, retry, mesure de latence, gestion des erreurs 429/5xx.
"""

import time
import requests


class ApiClient:
    """Client HTTP simple pour interroger une API et mesurer sa qualité."""

    def __init__(self, base_url, timeout=3, max_retries=1):
        """
        :param base_url: URL de base de l'API (ex: "https://api.agify.io")
        :param timeout: timeout en secondes pour chaque requête
        :param max_retries: nombre maximum de re-tentatives en cas d'échec
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

    def get(self, path="", params=None):
        """
        Effectue un GET sur l'API et retourne un dictionnaire avec :
        - status_code : le code HTTP renvoyé (ou None en cas d'erreur réseau)
        - latency_ms : la latence en millisecondes
        - json : la réponse JSON (ou None)
        - error : message d'erreur (ou None si succès)
        """
        url = f"{self.base_url}{path}"
        attempt = 0
        last_error = None

        while attempt <= self.max_retries:
            start = time.time()
            try:
                response = requests.get(url, params=params, timeout=self.timeout)
                latency_ms = int((time.time() - start) * 1000)

                # Cas du rate limit : on attend un peu et on retente
                if response.status_code == 429 and attempt < self.max_retries:
                    time.sleep(1)
                    attempt += 1
                    continue

                # Tentative de parsing JSON (peut échouer si la réponse n'est pas du JSON)
                try:
                    body = response.json()
                except ValueError:
                    body = None

                return {
                    "status_code": response.status_code,
                    "latency_ms": latency_ms,
                    "json": body,
                    "error": None,
                }

            except requests.Timeout:
                last_error = f"Timeout après {self.timeout}s"
            except requests.RequestException as e:
                last_error = f"Erreur réseau : {e}"

            attempt += 1

        # Si on arrive ici, toutes les tentatives ont échoué
        return {
            "status_code": None,
            "latency_ms": int((time.time() - start) * 1000),
            "json": None,
            "error": last_error,
        }
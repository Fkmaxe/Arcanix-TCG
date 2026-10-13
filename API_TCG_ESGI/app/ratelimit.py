"""Limiteur de tentatives en mémoire (suffisant pour un seul processus uvicorn).

Protège la connexion et la définition de mot de passe contre le bourrage d'identifiants.
"""
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status


class Limiteur:
    def __init__(self, max_echecs: int, fenetre_s: int):
        self.max = max_echecs
        self.fenetre = fenetre_s
        self._echecs: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _purger(self, cle: str, maintenant: float) -> deque[float]:
        q = self._echecs[cle]
        while q and q[0] <= maintenant - self.fenetre:
            q.popleft()
        return q

    def verifier(self, cle: str) -> None:
        with self._lock:
            q = self._purger(cle, time.monotonic())
            if len(q) >= self.max:
                attente = int(q[0] + self.fenetre - time.monotonic()) + 1
                raise HTTPException(
                    status.HTTP_429_TOO_MANY_REQUESTS,
                    f"Trop de tentatives. Réessaie dans {max(1, attente // 60)} minute(s).",
                    headers={"Retry-After": str(attente)},
                )

    def echec(self, cle: str) -> None:
        with self._lock:
            self._purger(cle, time.monotonic()).append(time.monotonic())

    def reussite(self, cle: str) -> None:
        with self._lock:
            self._echecs.pop(cle, None)

    def reset(self) -> None:
        with self._lock:
            self._echecs.clear()


connexion = Limiteur(max_echecs=10, fenetre_s=15 * 60)


def ip_client(request: Request) -> str:
    return request.client.host if request.client else "inconnu"

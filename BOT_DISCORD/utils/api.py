"""Client HTTP unique vers l'API Arcanix."""
import logging
from typing import Any

import aiohttp

import config

log = logging.getLogger("arcanix.api")

MESSAGES = {
    401: "Le bot n'est pas autorisé par l'API (token mal configuré).",
    403: "Tu n'as pas les droits pour cette commande.",
    404: "Introuvable.",
    409: "Cet élément existe déjà.",
    422: "Certaines informations sont invalides.",
}


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


class ApiClient:
    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None

    async def start(self) -> None:
        self._session = aiohttp.ClientSession(
            base_url=config.API_BASE_URL,
            headers={"x-bot-token": config.API_BOT_TOKEN},
            timeout=aiohttp.ClientTimeout(total=10),
        )

    async def close(self) -> None:
        if self._session:
            await self._session.close()

    async def request(self, method: str, path: str, **kwargs) -> Any:
        assert self._session, "ApiClient non démarré"
        try:
            async with self._session.request(method, path, **kwargs) as resp:
                if resp.status == 204:
                    return None
                try:
                    data = await resp.json()
                except aiohttp.ContentTypeError:
                    data = None
                if resp.status >= 400:
                    detail = data.get("detail") if isinstance(data, dict) else None
                    if isinstance(detail, list) and detail:
                        champ = detail[0].get("loc", ["?"])[-1]
                        message = f"Champ « {champ} » invalide : {detail[0].get('msg', '')}"
                    elif isinstance(detail, str):
                        message = detail
                    else:
                        message = MESSAGES.get(resp.status, f"Erreur de l'API ({resp.status}).")
                    raise ApiError(resp.status, message)
                return data
        except aiohttp.ClientError as e:
            log.warning("API injoignable : %s", e)
            raise ApiError(0, "Le site Arcanix est injoignable pour le moment, réessaie plus tard.") from e

    # --- Compte -----------------------------------------------------------------
    async def inscription(self, discord_id: int, prenom: str, nom: str, email: str, classe: str) -> dict:
        return await self.request("POST", "/discord/inscription", json={
            "discord_id": str(discord_id), "prenom": prenom, "nom": nom, "adresse_mail": email, "classe": classe,
        })

    async def lier(self, discord_id: int, code: str) -> dict:
        return await self.request("POST", "/discord/lier", json={"discord_id": str(discord_id), "code": code})

    async def reinitialiser(self, discord_id: int) -> dict:
        return await self.request("POST", "/discord/reinitialiser", json={"discord_id": str(discord_id)})

    # --- Consultation -------------------------------------------------------------
    async def membre(self, discord_id: int) -> dict:
        return await self.request("GET", f"/discord/membres/{discord_id}")

    async def historique(self, discord_id: int, limit: int = 10) -> list[dict]:
        return await self.request("GET", f"/discord/membres/{discord_id}/historique", params={"limit": limit})

    async def classement(self, semestre_id: int | None = None, limit: int = 10) -> dict:
        params = {"limit": limit}
        if semestre_id:
            params["semestreId"] = semestre_id
        return await self.request("GET", "/discord/classement", params=params)

    async def semestres(self) -> list[dict]:
        return await self.request("GET", "/discord/semestres")

    async def seances_a_venir(self, limit: int = 5) -> list[dict]:
        return await self.request("GET", "/discord/seances/a-venir", params={"limit": limit})

    async def seance(self, seance_id: int) -> dict:
        return await self.request("GET", f"/seances/{seance_id}")

    async def seances_recherche(self, q: str = "") -> list[dict]:
        return await self.request("GET", "/discord/seances/recherche", params={"q": q} if q else None)

    # --- Modération ---------------------------------------------------------------
    async def creer_seance(self, auteur_id: int, **seance) -> dict:
        return await self.request("POST", "/discord/seances", json={"auteur_discord_id": str(auteur_id), **seance})

    async def presences(self, seance_id: int, auteur_id: int, discord_ids: list[int]) -> dict:
        return await self.request("POST", f"/discord/seances/{seance_id}/presences", json={
            "auteur_discord_id": str(auteur_id), "discord_ids": [str(i) for i in discord_ids],
        })

    async def inscription_seance(self, seance_id: int, discord_id: int, action: str) -> dict:
        return await self.request("POST", f"/discord/seances/{seance_id}/inscription",
                                  json={"discord_id": str(discord_id), "action": action})

    async def ajustement(self, auteur_id: int, discord_id: int, points: float, motif: str, categorie: str) -> dict:
        return await self.request("POST", "/discord/ajustements", json={
            "auteur_discord_id": str(auteur_id), "discord_id": str(discord_id), "points": points,
            "motif": motif, "categorie": categorie,
        })

    async def roles(self) -> dict:
        return await self.request("GET", "/discord/roles")

    # --- Annonces -----------------------------------------------------------------
    async def annonces_en_attente(self) -> list[dict]:
        return await self.request("GET", "/discord/annonces/en-attente")

    async def annonces_ack(self, annonces: list[dict]) -> None:
        await self.request("POST", "/discord/annonces/ack", json=annonces)

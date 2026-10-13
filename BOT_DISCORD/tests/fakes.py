"""Doubles de test : simulent Discord (interactions, salons) et l'API Arcanix, sans réseau."""
import asyncio
import functools
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

from utils.api import ApiError


def run_async(fn):
    """Exécute un test async (les View discord.py exigent une boucle active)."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return asyncio.run(fn(*args, **kwargs))
    return wrapper


@dataclass
class FakeUser:
    id: int = 100
    display_name: str = "Maxence"
    bot: bool = False

    @property
    def display_avatar(self):
        return SimpleNamespace(url="https://cdn.discordapp.com/avatar.png")

    def __eq__(self, other):
        return isinstance(other, FakeUser) and other.id == self.id

    def __hash__(self):
        return hash(self.id)


@dataclass
class Envoi:
    """Un message envoyé par le bot (réponse, suivi, édition)."""
    canal: str
    content: Any = None
    embed: Any = None
    view: Any = None
    ephemeral: bool = False

    @property
    def texte(self) -> str:
        """Tout le texte visible : titre, description et champs de l'embed."""
        e = self.embed
        if e is None:
            return str(self.content or "")
        parts = [e.title or "", e.description or ""] + [f"{f.name} {f.value}" for f in e.fields]
        return "\n".join(parts)

    @property
    def boutons(self) -> list:
        return list(self.view.children) if self.view and hasattr(self.view, "children") else []


class FakeResponse:
    def __init__(self, inter: "FakeInteraction"):
        self.inter = inter
        self._done = False
        self.modal = None
        self.deferred = None

    def is_done(self) -> bool:
        return self._done

    async def defer(self, ephemeral: bool = False, thinking: bool = False):
        self._done = True
        self.deferred = {"ephemeral": ephemeral, "thinking": thinking}

    async def send_message(self, content=None, *, embed=None, view=None, ephemeral=False, **_):
        import discord
        if view is discord.utils.MISSING:
            view = None
        self.inter.envois.append(Envoi("reponse", content, embed, view, ephemeral))
        self._done = True

    async def send_modal(self, modal):
        self._done = True
        self.modal = modal


class FakeFollowup:
    def __init__(self, inter: "FakeInteraction"):
        self.inter = inter

    async def send(self, content=None, *, embed=None, view=None, ephemeral=False, **_):
        import discord
        if view is discord.utils.MISSING:
            view = None
        if view is not None and self.inter.refuser_liens and any(getattr(b, "url", None) for b in view.children):
            # Comme Discord avec une URL de bouton invalide (ex. localhost)
            raise discord.HTTPException(SimpleNamespace(status=400, reason="Bad Request"), "Invalid Form Body: url")
        self.inter.envois.append(Envoi("suivi", content, embed, view, ephemeral))


class FakeMessage:
    """Message d'annonce sur lequel on clique (pour les boutons)."""
    def __init__(self, embed=None):
        self.embeds = [embed] if embed else []
        self.editions = []

    async def edit(self, *, embed=None, **_):
        self.editions.append(embed)
        self.embeds = [embed]


class FakeInteraction:
    def __init__(self, user: FakeUser | None = None, client=None, message: FakeMessage | None = None, guild=None):
        self.user = user or FakeUser()
        self.envois: list[Envoi] = []
        self.response = FakeResponse(self)
        self.followup = FakeFollowup(self)
        self.command = SimpleNamespace(name="test")
        self.client = client
        self.message = message
        self.guild = guild
        self.refuser_liens = False  # simule le refus des boutons-liens par Discord

    async def edit_original_response(self, *, embed=None, view=None, content=None):
        self.envois.append(Envoi("edition", content, embed, view))

    @property
    def dernier(self) -> Envoi:
        assert self.envois, "le bot n'a rien répondu"
        return self.envois[-1]


class FakeChannel:
    def __init__(self):
        self.messages: list[Envoi] = []

    async def send(self, content=None, *, embed=None, view=None, allowed_mentions=None):
        import discord
        if view is discord.utils.MISSING:
            view = None
        self.messages.append(Envoi("salon", content, embed, view))


class FakeApi:
    """Remplace ApiClient : chaque méthode renvoie `reponses[nom]` ou lève l'ApiError fournie."""

    def __init__(self, **reponses):
        self.reponses = reponses
        self.appels: list[tuple[str, tuple, dict]] = []

    def __getattr__(self, nom):
        async def methode(*args, **kwargs):
            self.appels.append((nom, args, kwargs))
            r = self.reponses.get(nom)
            if isinstance(r, ApiError):
                raise r
            if callable(r):
                return r(*args, **kwargs)
            return r
        return methode

    def appels_de(self, nom):
        return [(a, k) for n, a, k in self.appels if n == nom]


@dataclass
class FakeBot:
    api: Any
    channel: FakeChannel = field(default_factory=FakeChannel)
    mp: dict = field(default_factory=dict)  # messages privés envoyés : {user_id: [embed]}

    def get_channel(self, _id):
        return self.channel

    async def fetch_user(self, uid: int):
        bot = self

        class _U:
            id = uid

            async def send(self, embed=None, **_):
                bot.mp.setdefault(uid, []).append(embed)
        return _U()

    async def wait_until_ready(self):
        return None


def remplir(modal, **valeurs):
    """Simule la saisie dans un formulaire Discord."""
    for nom, valeur in valeurs.items():
        getattr(modal, nom)._value = valeur
    return modal


async def lancer(coro, inter: "FakeInteraction"):
    """Exécute une commande / un formulaire / un bouton comme Discord le ferait :
    une exception aboutit au gestionnaire d'erreurs du bot (le membre reçoit toujours un message)."""
    from utils.interactions import signaler
    try:
        await coro
    except Exception as e:  # noqa: BLE001
        await signaler(inter, e)

import asyncio
import contextlib
import logging
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from . import config, planificateur
from .database import engine
from .routers import ajustements, auth, discord, journal, me, participations, seances, semestres, stats_exports, users

logging.basicConfig(level=logging.DEBUG if config.DEBUG else logging.INFO)
log = logging.getLogger("arcanix")

_hote = urlparse(config.FRONTEND_URL).hostname or ""
if not config.DEBUG and (_hote in ("localhost", "127.0.0.1") or "." not in _hote):
    log.warning("FRONTEND_URL=%s n'est pas une adresse publique : les liens des emails, du bot et des QR codes "
                "ne fonctionneront pas pour les membres (voir docs/CONFIGURATION.md)", config.FRONTEND_URL)

@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI):
    tache = asyncio.create_task(planificateur.boucle())
    try:
        yield
    finally:
        tache.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await tache


app = FastAPI(title="Arcanix", version="2.0.0", debug=config.DEBUG, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=False,  # auth par en-tête Bearer, pas de cookies
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "Content-Disposition"],
)

for r in (auth, users, semestres, seances, participations, me, stats_exports, discord, ajustements, journal):
    app.include_router(r.router)
app.include_router(auth.config_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # On ne logue jamais le corps (il peut contenir des mots de passe)
    erreurs = [{"loc": e.get("loc"), "msg": e.get("msg"), "type": e.get("type")} for e in exc.errors()]
    log.info("422 sur %s %s : %s", request.method, request.url.path, erreurs)
    return JSONResponse(status_code=422, content={"detail": erreurs})


@app.get("/health")
def health():
    try:
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "db_unavailable"})

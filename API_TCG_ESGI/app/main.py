import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from . import config
from .database import engine
from .routers import auth, discord, me, participations, seances, semestres, stats_exports, users

logging.basicConfig(level=logging.DEBUG if config.DEBUG else logging.INFO)
log = logging.getLogger("arcanix")

app = FastAPI(title="Arcanix", version="2.0.0", debug=config.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=False,  # auth par en-tête Bearer, pas de cookies
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "Content-Disposition"],
)

for r in (auth, users, semestres, seances, participations, me, stats_exports, discord):
    app.include_router(r.router)


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

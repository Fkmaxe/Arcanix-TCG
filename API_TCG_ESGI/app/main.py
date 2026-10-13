import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, users, semestres, seances, participations, me, stats_exports , discord
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


# Env vars
db_host = os.environ.get("DB_HOST", "localhost")
api_key = os.environ.get("API_KEY", "default_key")
debug_mode = os.environ.get("DEBUG", "False").lower() == "true"

app = FastAPI(title="Arcanix", version="1.0.0", debug=debug_mode)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # 🌍 autorise toutes les origines
    allow_credentials=True,   # cookies/headers d'auth autorisés
    allow_methods=["*"],      # autorise toutes les méthodes HTTP (GET, POST, PUT, DELETE…)
    allow_headers=["*"],      # autorise tous les headers (Authorization, Content-Type…)
)
# Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(semestres.router)
app.include_router(seances.router)
app.include_router(participations.router)
app.include_router(me.router)
app.include_router(stats_exports.router)
app.include_router(discord.router)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    print("422 Request body:", body.decode("utf-8"))
    print("422 Errors:", exc.errors())
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

@app.get("/health")
def health():
    return {"status": "ok", "db_host": db_host}

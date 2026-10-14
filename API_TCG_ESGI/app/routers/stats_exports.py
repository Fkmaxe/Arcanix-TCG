import csv
import json
from datetime import date
from io import StringIO

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Participation, Seance, Semestre, Utilisateur
from ..schemas import Classement, SemestreOut
from ..security import get_current_user, is_staff, require_roles
from ..services import classement, lignes_publiques, resoudre_semestre

router = APIRouter(tags=["stats", "exports"])
staff = require_roles("admin", "moderator")


@router.get("/stats/points")
def stats_points(semestreId: int | None = None, classe: str | None = None, userId: int | None = None,
                 db: Session = Depends(get_db), _=Depends(staff)):
    """Points des élèves (y compris à 0) — réservé à la modération.

    Modérateurs et admins sont listés mais pas classés (`rang` vide) ; les externes n'y figurent pas.
    """
    lignes = classement(db, semestreId, inclure_zero=True, inclure_staff=True, classe=classe, user_id=userId)
    return [
        {"rang": l["rang"], "userId": l["userId"], "nom": l["nom"], "prenom": l["prenom"], "role": l["role"],
         "classe": l["classe"], "points": l["points"], "presences": l["presences"],
         "bonus": l["bonus"]}
        for l in lignes
    ]


@router.get("/stats/classement", response_model=Classement)
def stats_classement(semestreId: int | None = None, classe: str | None = None,
                     db: Session = Depends(get_db), user: Utilisateur = Depends(get_current_user)):
    """Classement visible par tous les membres connectés (noms abrégés, pas d'emails)."""
    semestre = resoudre_semestre(db, semestreId)
    if not semestre:
        return Classement(semestre=None, lignes=[])
    lignes = classement(db, semestre.id, classe=classe)
    return Classement(semestre=SemestreOut.model_validate(semestre),
                      lignes=lignes_publiques(lignes, user.id, is_staff(user)))


def _nom_fichier(db: Session, semestre_id: int | None, base: str, ext: str) -> str:
    s = db.get(Semestre, semestre_id) if semestre_id else None
    return f"{base}_{s.annee}_S{s.numero}.{ext}" if s else f"{base}_{date.today().isoformat()}.{ext}"


def _csv_response(rows: list[list], entetes: list[str], filename: str) -> StreamingResponse:
    buf = StringIO()
    buf.write("﻿")  # BOM : Excel ouvre correctement les accents
    w = csv.writer(buf, delimiter=";")
    w.writerow(entetes)
    w.writerows(rows)
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv; charset=utf-8",
                             headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/exports/participations.csv")
def export_participations_csv(semestreId: int | None = None, db: Session = Depends(get_db), _=Depends(staff)):
    q = (
        db.query(Participation, Seance, Utilisateur)
        .join(Seance, Seance.id == Participation.seance_id)
        .join(Utilisateur, Utilisateur.id == Participation.utilisateur_id)
        .filter(Utilisateur.externe.is_(False))  # le rendu de points ne concerne que les élèves
    )
    if semestreId:
        q = q.filter(Seance.semestre_id == semestreId)
    rows = [
        [s.date_seance.isoformat(), s.nom, s.jeu or "", u.nom, u.prenom, u.classe, u.adresse_mail,
         "oui" if p.present else "non", str(s.nb_point).replace(".", ","), p.commentaire or ""]
        for p, s, u in q.order_by(Seance.date_seance, Seance.id, Utilisateur.nom).all()
    ]
    return _csv_response(
        rows,
        ["date", "seance", "jeu", "nom", "prenom", "classe", "email", "present", "points_seance", "commentaire"],
        _nom_fichier(db, semestreId, "participations", "csv"),
    )


@router.get("/exports/points.csv")
def export_points_csv(semestreId: int | None = None, db: Session = Depends(get_db), _=Depends(staff)):
    lignes = classement(db, semestreId, inclure_zero=True, inclure_staff=True)
    rows = [[l["rang"] or "", l["nom"], l["prenom"], l["role"], l["classe"] or "",
             l["adresse_mail"], l["presences"], f'{l["bonus"]:g}'.replace(".", ","), f'{l["points"]:g}'.replace(".", ",")]
            for l in lignes]
    return _csv_response(rows, ["rang", "nom", "prenom", "role", "classe", "email", "presences", "bonus_malus", "points"],
                         _nom_fichier(db, semestreId, "points", "csv"))


@router.get("/exports/points.json")
def export_points_json(semestreId: int | None = None, db: Session = Depends(get_db), _=Depends(staff)):
    s = db.get(Semestre, semestreId) if semestreId else None
    lignes = classement(db, semestreId, inclure_zero=True, inclure_staff=True)
    payload = {
        "semestre": SemestreOut.model_validate(s).model_dump() if s else None,
        "exporte_le": date.today().isoformat(),
        "membres": [{k: l[k] for k in ("rang", "nom", "prenom", "role", "classe", "adresse_mail", "presences",
                                       "bonus", "points")}
                    for l in lignes],
    }
    return StreamingResponse(
        iter([json.dumps(payload, ensure_ascii=False, indent=2)]), media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{_nom_fichier(db, semestreId, "points", "json")}"'},
    )

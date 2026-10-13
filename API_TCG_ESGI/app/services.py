"""Requêtes partagées entre les routeurs (site + bot)."""
from datetime import date
from typing import Iterable

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from .models import Participation, Seance, Semestre, Utilisateur
from .schemas import (
    LigneClassement, ParticipantDetail, PointEvolution, SeanceDetail, SeanceOut, SemestreOut,
)


# --- Semestres -------------------------------------------------------------------
def semestre_actif(db: Session) -> Semestre | None:
    s = db.query(Semestre).filter(Semestre.actif.is_(True)).first()
    if s:
        return s
    return db.query(Semestre).order_by(Semestre.annee.desc(), Semestre.numero.desc()).first()


def resoudre_semestre(db: Session, semestre_id: int | None) -> Semestre | None:
    return db.get(Semestre, semestre_id) if semestre_id else semestre_actif(db)


# --- Séances ---------------------------------------------------------------------
def _compteurs(db: Session, ids: list[int]) -> dict[int, tuple[int, int]]:
    if not ids:
        return {}
    rows = db.execute(
        select(
            Participation.seance_id,
            func.count(),
            func.count().filter(Participation.present.is_(True)),
        ).where(Participation.seance_id.in_(ids)).group_by(Participation.seance_id)
    ).all()
    return {r[0]: (r[1], r[2]) for r in rows}


def seances_out(db: Session, seances: Iterable[Seance]) -> list[SeanceOut]:
    seances = list(seances)
    cpt = _compteurs(db, [s.id for s in seances])
    out = []
    for s in seances:
        total, presents = cpt.get(s.id, (0, 0))
        o = SeanceOut.model_validate(s)
        o.semestre = SemestreOut.model_validate(s.semestre) if s.semestre else None
        o.nb_participants, o.nb_presents = total, presents
        out.append(o)
    return out


def seance_out(db: Session, s: Seance) -> SeanceOut:
    return seances_out(db, [s])[0]


def seance_detail(db: Session, s: Seance, viewer: Utilisateur | None, staff: bool) -> SeanceDetail:
    base = seance_out(db, s)
    d = SeanceDetail(**base.model_dump())
    rows = (
        db.query(Participation, Utilisateur)
        .join(Utilisateur, Utilisateur.id == Participation.utilisateur_id)
        .filter(Participation.seance_id == s.id)
        .order_by(Utilisateur.prenom, Utilisateur.nom)
        .all()
    )
    if staff:
        d.participants = [
            ParticipantDetail(
                utilisateur_id=u.id, seance_id=s.id, present=p.present, commentaire=p.commentaire,
                nom=u.nom, prenom=u.prenom, classe=u.classe, adresse_mail=u.adresse_mail,
                discord_lie=bool(u.discord_id),
            )
            for p, u in rows
        ]
    if viewer:
        mine = next((p for p, u in rows if u.id == viewer.id), None)
        d.ma_participation = mine.present if mine else None
    return d


# --- Points & classement -------------------------------------------------------------
def _points_expr():
    return func.coalesce(
        func.sum(Seance.nb_point).filter(Participation.present.is_(True), Seance.id.isnot(None)), 0
    )


def _presences_expr():
    return func.count(Seance.id).filter(Participation.present.is_(True))


def rang_competition(lignes: list[dict]) -> None:
    """Classement « 1, 1, 3 » : les ex æquo partagent le même rang."""
    rang, precedent = 0, None
    for i, l in enumerate(lignes, start=1):
        if l["points"] != precedent:
            rang, precedent = i, l["points"]
        l["rang"] = rang


def classement(
    db: Session,
    semestre_id: int | None,
    *,
    inclure_zero: bool = False,
    classe: str | None = None,
    user_id: int | None = None,
) -> list[dict]:
    """Points par membre pour un semestre (None = tous semestres confondus)."""
    seance_join = Seance.id == Participation.seance_id
    if semestre_id:
        seance_join = and_(seance_join, Seance.semestre_id == semestre_id)
    q = (
        select(
            Utilisateur.id, Utilisateur.nom, Utilisateur.prenom, Utilisateur.classe,
            Utilisateur.adresse_mail, Utilisateur.discord_id,
            _points_expr().label("points"),
            _presences_expr().label("presences"),
        )
        .select_from(Utilisateur)
        .outerjoin(Participation, Participation.utilisateur_id == Utilisateur.id)
        .outerjoin(Seance, seance_join)
        .group_by(Utilisateur.id)
    )
    if classe:
        q = q.where(Utilisateur.classe == classe)
    if user_id:
        q = q.where(Utilisateur.id == user_id)
    rows = db.execute(q).all()
    lignes = [
        {
            "userId": r.id, "nom": r.nom, "prenom": r.prenom, "classe": r.classe,
            "adresse_mail": r.adresse_mail, "discord_id": r.discord_id,
            "points": float(r.points or 0), "presences": int(r.presences or 0),
        }
        for r in rows
    ]
    if not inclure_zero:
        lignes = [l for l in lignes if l["presences"] > 0 or l["points"] > 0]
    lignes.sort(key=lambda l: (-l["points"], -l["presences"], l["prenom"].lower(), l["nom"].lower()))
    rang_competition(lignes)
    return lignes


def lignes_publiques(lignes: list[dict], viewer_id: int | None, staff: bool) -> list[LigneClassement]:
    out = []
    for l in lignes:
        nom = l["nom"] if staff else (l["nom"][:1].upper() + "." if l["nom"] else "")
        out.append(LigneClassement(
            rang=l["rang"], userId=l["userId"], prenom=l["prenom"], nom=nom, classe=l["classe"],
            points=l["points"], presences=l["presences"], moi=l["userId"] == viewer_id,
        ))
    return out


def stats_membre(db: Session, user: Utilisateur, semestre: Semestre | None) -> dict:
    """Points, rang, présences et évolution d'un membre sur un semestre."""
    if not semestre:
        return {"semestre": None, "points": 0.0, "rang": None, "nb_membres_classes": 0,
                "seances_semestre": 0, "presences": 0, "taux_presence": 0.0, "evolution": []}
    lignes = classement(db, semestre.id)
    moi = next((l for l in lignes if l["userId"] == user.id), None)
    nb_seances = db.query(func.count(Seance.id)).filter(
        Seance.semestre_id == semestre.id, Seance.date_seance <= date.today()
    ).scalar() or 0
    rows = (
        db.query(Seance.date_seance, Seance.nom, Seance.nb_point)
        .join(Participation, Participation.seance_id == Seance.id)
        .filter(Participation.utilisateur_id == user.id, Participation.present.is_(True),
                Seance.semestre_id == semestre.id)
        .order_by(Seance.date_seance, Seance.id)
        .all()
    )
    cumul, evolution = 0.0, []
    for r in rows:
        cumul += float(r.nb_point)
        evolution.append(PointEvolution(date=r.date_seance, seance=r.nom, points=float(r.nb_point), cumul=cumul))
    presences = moi["presences"] if moi else 0
    return {
        "semestre": SemestreOut.model_validate(semestre),
        "points": moi["points"] if moi else 0.0,
        "rang": moi["rang"] if moi else None,
        "nb_membres_classes": len(lignes),
        "seances_semestre": nb_seances,
        "presences": presences,
        "taux_presence": round(presences / nb_seances, 3) if nb_seances else 0.0,
        "evolution": evolution,
    }


def points_par_semestre(db: Session, user_id: int) -> list[dict]:
    rows = db.execute(
        select(
            Semestre.id, Semestre.annee, Semestre.numero,
            func.coalesce(func.sum(Seance.nb_point).filter(Participation.present.is_(True)), 0).label("points"),
        )
        .join(Seance, Seance.semestre_id == Semestre.id)
        .join(Participation, Participation.seance_id == Seance.id)
        .where(Participation.utilisateur_id == user_id)
        .group_by(Semestre.id)
        .order_by(Semestre.annee.desc(), Semestre.numero.desc())
    ).all()
    return [{"semestre_id": r.id, "annee": r.annee, "numero": r.numero, "points": float(r.points or 0)} for r in rows]

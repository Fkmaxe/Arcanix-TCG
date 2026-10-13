"""Requêtes partagées entre les routeurs (site + bot)."""
from datetime import date
from typing import Iterable

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from .models import Ajustement, Inscription, Participation, Pointage, Resultat, Seance, Semestre, Utilisateur
from .schemas import (
    InscritDetail, LigneClassement, ParticipantDetail, PointageDetail, PointEvolution, ResultatOut, SeanceDetail,
    SeanceOut, SemestreOut,
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


def _compteurs_inscriptions(db: Session, ids: list[int]) -> dict[int, tuple[int, int]]:
    if not ids:
        return {}
    rows = db.execute(
        select(
            Inscription.seance_id,
            func.count().filter(Inscription.statut == "inscrit"),
            func.count().filter(Inscription.statut == "attente"),
        ).where(Inscription.seance_id.in_(ids)).group_by(Inscription.seance_id)
    ).all()
    return {r[0]: (r[1], r[2]) for r in rows}


def seances_out(db: Session, seances: Iterable[Seance], viewer: Utilisateur | None = None) -> list[SeanceOut]:
    seances = list(seances)
    ids = [s.id for s in seances]
    cpt = _compteurs(db, ids)
    ins = _compteurs_inscriptions(db, ids)
    mes_inscriptions: dict[int, str] = {}
    if viewer and ids:
        mes_inscriptions = dict(db.execute(
            select(Inscription.seance_id, Inscription.statut)
            .where(Inscription.utilisateur_id == viewer.id, Inscription.seance_id.in_(ids))
        ).all())
    avec_resultats = set(db.execute(
        select(Resultat.seance_id).where(Resultat.seance_id.in_(ids)).distinct()
    ).scalars()) if ids else set()
    out = []
    for s in seances:
        total, presents = cpt.get(s.id, (0, 0))
        o = SeanceOut.model_validate(s)
        o.semestre = SemestreOut.model_validate(s.semestre) if s.semestre else None
        o.nb_participants, o.nb_presents = total, presents
        o.nb_inscrits, o.nb_attente = ins.get(s.id, (0, 0))
        o.mon_inscription = mes_inscriptions.get(s.id)
        o.a_resultats = s.id in avec_resultats
        out.append(o)
    return out


def seance_out(db: Session, s: Seance, viewer: Utilisateur | None = None) -> SeanceOut:
    return seances_out(db, [s], viewer)[0]


def resultats_out(db: Session, seance_id: int, viewer: Utilisateur | None, staff: bool) -> list[ResultatOut]:
    bonus = dict(db.execute(
        select(Ajustement.utilisateur_id, Ajustement.points)
        .where(Ajustement.seance_id == seance_id, Ajustement.categorie == "tournoi")
    ).all())
    rows = (db.query(Resultat, Utilisateur).join(Utilisateur, Utilisateur.id == Resultat.utilisateur_id)
            .filter(Resultat.seance_id == seance_id).order_by(Resultat.place, Utilisateur.prenom).all())
    return [
        ResultatOut(
            utilisateur_id=u.id, prenom=u.prenom, nom=u.nom if staff else f"{u.nom[:1].upper()}.",
            place=r.place, victoires=r.victoires, defaites=r.defaites, nuls=r.nuls, deck=r.deck,
            bonus=float(bonus.get(u.id, 0)), moi=bool(viewer and viewer.id == u.id),
        )
        for r, u in rows
    ]


def seance_detail(db: Session, s: Seance, viewer: Utilisateur | None, staff: bool) -> SeanceDetail:
    from .vie import pointage_ouvert  # import local : évite un cycle services <-> vie

    base = seance_out(db, s, viewer)
    d = SeanceDetail(**base.model_dump())
    d.pointage_ouvert = pointage_ouvert(s)
    d.resultats = resultats_out(db, s.id, viewer, staff)
    if viewer:
        d.mon_pointage = db.get(Pointage, {"utilisateur_id": viewer.id, "seance_id": s.id}) is not None
    if staff:
        inscrits = (db.query(Inscription, Utilisateur).join(Utilisateur, Utilisateur.id == Inscription.utilisateur_id)
                    .filter(Inscription.seance_id == s.id).order_by(Inscription.statut.desc(), Inscription.cree_le).all())
        d.inscrits = [
            InscritDetail(utilisateur_id=u.id, prenom=u.prenom, nom=u.nom, classe=u.classe, discord_lie=bool(u.discord_id),
                          statut=i.statut, cree_le=i.cree_le)
            for i, u in inscrits
        ]
        pointages = (db.query(Pointage, Utilisateur).join(Utilisateur, Utilisateur.id == Pointage.utilisateur_id)
                     .filter(Pointage.seance_id == s.id).order_by(Pointage.cree_le).all())
        d.pointages = [
            PointageDetail(utilisateur_id=u.id, prenom=u.prenom, nom=u.nom, classe=u.classe,
                           discord_lie=bool(u.discord_id), cree_le=p.cree_le)
            for p, u in pointages
        ]
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


def bonus_par_membre(db: Session, semestre_id: int | None) -> dict[int, float]:
    q = select(Ajustement.utilisateur_id, func.sum(Ajustement.points)).group_by(Ajustement.utilisateur_id)
    if semestre_id:
        q = q.where(Ajustement.semestre_id == semestre_id)
    return {uid: float(total) for uid, total in db.execute(q).all()}


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
    bonus = bonus_par_membre(db, semestre_id)
    lignes = []
    for r in rows:
        b = bonus.get(r.id, 0.0)
        lignes.append({
            "userId": r.id, "nom": r.nom, "prenom": r.prenom, "classe": r.classe,
            "adresse_mail": r.adresse_mail, "discord_id": r.discord_id,
            "points": round(float(r.points or 0) + b, 2), "presences": int(r.presences or 0), "bonus": b,
        })
    if not inclure_zero:
        lignes = [l for l in lignes if l["presences"] > 0 or l["points"] != 0 or l["bonus"] != 0]
    lignes.sort(key=lambda l: (-l["points"], -l["presences"], l["prenom"].lower(), l["nom"].lower()))
    rang_competition(lignes)
    return lignes


def lignes_publiques(lignes: list[dict], viewer_id: int | None, staff: bool) -> list[LigneClassement]:
    out = []
    for l in lignes:
        nom = l["nom"] if staff else (l["nom"][:1].upper() + "." if l["nom"] else "")
        out.append(LigneClassement(
            rang=l["rang"], userId=l["userId"], prenom=l["prenom"], nom=nom, classe=l["classe"],
            points=l["points"], presences=l["presences"], bonus=l.get("bonus", 0), moi=l["userId"] == viewer_id,
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
    evenements = [(r.date_seance, 0, r.nom, float(r.nb_point), "presence") for r in rows]
    for a in db.query(Ajustement).filter(Ajustement.utilisateur_id == user.id, Ajustement.semestre_id == semestre.id):
        evenements.append((a.cree_le.date(), 1, a.motif, float(a.points), "ajustement"))
    evenements.sort(key=lambda e: (e[0], e[1]))
    cumul, evolution = 0.0, []
    for jour, _, libelle, pts, type_ in evenements:
        cumul = round(cumul + pts, 2)
        evolution.append(PointEvolution(date=jour, seance=libelle, points=pts, cumul=cumul, type=type_))
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
    presences = _points_presences_par_semestre(db, user_id)
    bonus = dict(db.execute(
        select(Ajustement.semestre_id, func.sum(Ajustement.points))
        .where(Ajustement.utilisateur_id == user_id).group_by(Ajustement.semestre_id)
    ).all())
    ids = {p["semestre_id"] for p in presences} | set(bonus)
    if not ids:
        return []
    par_id = {p["semestre_id"]: p for p in presences}
    out = []
    for sem in db.query(Semestre).filter(Semestre.id.in_(ids)).order_by(Semestre.annee.desc(), Semestre.numero.desc()):
        pts = par_id.get(sem.id, {}).get("points", 0.0) + float(bonus.get(sem.id, 0))
        out.append({"semestre_id": sem.id, "annee": sem.annee, "numero": sem.numero, "points": round(pts, 2)})
    return out


def _points_presences_par_semestre(db: Session, user_id: int) -> list[dict]:
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

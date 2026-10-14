from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Ajustement, Participation, Seance, Utilisateur
from ..schemas import CodeDiscord, MaParticipation, MeOut, MesStats, MeUpdate, MonAjustement, MyPointsOut, PasswordChange
from ..security import creer_jeton, get_current_user, hash_password, verify_password
from ..services import points_par_semestre, resoudre_semestre, stats_membre
from .auth import me_out

router = APIRouter(prefix="/me", tags=["me"])


@router.patch("", response_model=MeOut)
def update_me(body: MeUpdate, db: Session = Depends(get_db), user: Utilisateur = Depends(get_current_user)):
    data = body.model_dump(exclude_unset=True, exclude_none=True)
    if "classe" in data and user.externe:
        raise HTTPException(422, "Les membres externes n'ont pas de classe")
    for k, v in data.items():
        setattr(user, k, v)
    db.commit()
    return me_out(user)


@router.patch("/password", status_code=204)
def change_my_password(body: PasswordChange, db: Session = Depends(get_db),
                       user: Utilisateur = Depends(get_current_user)):
    # Le mot de passe actuel est exigé, sauf si le compte doit justement le changer
    if not user.doit_changer_mdp:
        if not body.current_password or not verify_password(body.current_password, user.mot_de_passe_hash):
            raise HTTPException(400, "Mot de passe actuel incorrect")
    user.mot_de_passe_hash = hash_password(body.new_password)
    user.doit_changer_mdp = False
    db.commit()


@router.get("/participations", response_model=list[MaParticipation])
def my_participations(semestreId: int | None = None, db: Session = Depends(get_db),
                      user: Utilisateur = Depends(get_current_user)):
    q = (
        db.query(Participation, Seance)
        .join(Seance, Seance.id == Participation.seance_id)
        .filter(Participation.utilisateur_id == user.id)
    )
    if semestreId:
        q = q.filter(Seance.semestre_id == semestreId)
    return [
        MaParticipation(
            seance_id=s.id, seance_nom=s.nom, date_seance=s.date_seance, jeu=s.jeu,
            nb_point=float(s.nb_point), present=p.present, commentaire=p.commentaire,
            semestre_id=s.semestre_id,
        )
        for p, s in q.order_by(Seance.date_seance.desc(), Seance.id.desc()).all()
    ]


@router.get("/points", response_model=MyPointsOut)
def my_points(db: Session = Depends(get_db), user: Utilisateur = Depends(get_current_user)):
    semestres = points_par_semestre(db, user.id)
    return {"userId": user.id, "semestres": semestres, "total": sum(s["points"] for s in semestres)}


@router.get("/stats", response_model=MesStats)
def my_stats(semestreId: int | None = None, db: Session = Depends(get_db),
             user: Utilisateur = Depends(get_current_user)):
    return stats_membre(db, user, resoudre_semestre(db, semestreId))


@router.post("/code-discord", response_model=CodeDiscord)
def code_discord(db: Session = Depends(get_db), user: Utilisateur = Depends(get_current_user)):
    """Code à taper dans Discord avec /lier pour associer ce compte."""
    code, minutes = creer_jeton(db, user, "lier_discord")
    db.commit()
    return CodeDiscord(code=code, expire_dans_minutes=minutes)


@router.delete("/discord", status_code=204)
def delier_discord(db: Session = Depends(get_db), user: Utilisateur = Depends(get_current_user)):
    user.discord_id = None
    db.commit()


@router.get("/ajustements", response_model=list[MonAjustement])
def mes_ajustements(semestreId: int | None = None, db: Session = Depends(get_db),
                    user: Utilisateur = Depends(get_current_user)):
    q = db.query(Ajustement).filter(Ajustement.utilisateur_id == user.id)
    if semestreId:
        q = q.filter(Ajustement.semestre_id == semestreId)
    return [
        MonAjustement(id=a.id, points=float(a.points), categorie=a.categorie, motif=a.motif,
                      semestre_id=a.semestre_id, seance_id=a.seance_id, cree_le=a.cree_le)
        for a in q.order_by(Ajustement.cree_le.desc())
    ]

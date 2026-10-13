"""Envoi d'emails transactionnels (SMTP), toujours en tâche de fond."""
import html
import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import make_msgid

from . import config

log = logging.getLogger("arcanix.mail")


def _gabarit(titre: str, paragraphes: list[str], bouton: tuple[str, str] | None, note: str | None) -> str:
    """Gabarit HTML compatible clients mail (tableaux + styles en ligne), aux couleurs d'Arcanix."""
    corps = "".join(
        f'<p style="margin:0 0 14px;font-size:15px;line-height:1.6;color:#e9dfc7">{p}</p>' for p in paragraphes
    )
    btn = ""
    if bouton:
        label, url = bouton
        btn = (
            '<table role="presentation" cellspacing="0" cellpadding="0" style="margin:22px 0">'
            f'<tr><td style="border-radius:8px;background:#ff7a1a;background-image:linear-gradient(135deg,#e8361f,#ff7a1a 45%,#ffd763)">'
            f'<a href="{html.escape(url)}" style="display:inline-block;padding:13px 26px;font-weight:700;font-size:15px;'
            f'color:#1a0d05;text-decoration:none;font-family:Arial,sans-serif">{html.escape(label)}</a></td></tr></table>'
            f'<p style="margin:0 0 14px;font-size:12px;color:#9c8f78">Si le bouton ne fonctionne pas, copie ce lien :<br>'
            f'<a href="{html.escape(url)}" style="color:#f5c24b;word-break:break-all">{html.escape(url)}</a></p>'
        )
    pied = f'<p style="margin:18px 0 0;font-size:12px;color:#9c8f78">{note}</p>' if note else ""
    logo = f"{config.FRONTEND_URL}/brand/carte-192.png"
    return f"""<!doctype html><html lang="fr"><body style="margin:0;padding:0;background:#0b0a0c">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#0b0a0c;padding:28px 12px">
<tr><td align="center">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:520px;background:#151113;border:1px solid #6b5220;border-radius:14px">
<tr><td style="padding:26px 26px 6px;text-align:center">
<img src="{logo}" width="56" height="56" alt="" style="display:inline-block">
<div style="font-family:Georgia,serif;font-size:22px;letter-spacing:4px;color:#f5c24b;margin-top:6px">ARCANIX</div>
</td></tr>
<tr><td style="padding:12px 26px 26px;font-family:Arial,sans-serif">
<h1 style="font-family:Georgia,serif;font-size:20px;color:#ffd98a;margin:0 0 16px">{html.escape(titre)}</h1>
{corps}{btn}{pied}
</td></tr></table>
<p style="font-family:Arial,sans-serif;font-size:11px;color:#6f6553;margin:14px 0 0">Arcanix · Association TCG</p>
</td></tr></table></body></html>"""


def _texte(titre: str, paragraphes: list[str], bouton: tuple[str, str] | None, note: str | None) -> str:
    import re
    nettoie = lambda t: re.sub(r"<[^>]+>", "", t)  # noqa: E731
    lignes = [titre, ""] + [nettoie(p) for p in paragraphes]
    if bouton:
        lignes += ["", f"{bouton[0]} : {bouton[1]}"]
    if note:
        lignes += ["", nettoie(note)]
    return "\n".join(lignes) + "\n\n— Arcanix · Association TCG\n"


def envoyer(destinataire: str, sujet: str, titre: str, paragraphes: list[str],
            bouton: tuple[str, str] | None = None, note: str | None = None) -> bool:
    if not config.SMTP_ACTIF:
        log.info("SMTP non configuré : email « %s » non envoyé", sujet)
        return False
    msg = EmailMessage()
    msg["Subject"] = sujet
    msg["From"] = config.SMTP_FROM
    msg["To"] = destinataire
    msg["Message-ID"] = make_msgid(domain="arcanix")
    msg.set_content(_texte(titre, paragraphes, bouton, note))
    msg.add_alternative(_gabarit(titre, paragraphes, bouton, note), subtype="html")
    try:
        if config.SMTP_SECURITE == "ssl":
            smtp = smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=15, context=ssl.create_default_context())
        else:
            smtp = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15)
        with smtp:
            if config.SMTP_SECURITE == "starttls":
                smtp.starttls(context=ssl.create_default_context())
            if config.SMTP_USER:
                smtp.login(config.SMTP_USER, config.SMTP_PASSWORD)
            smtp.send_message(msg)
        log.info("Email « %s » envoyé à %s", sujet, destinataire)
        return True
    except Exception as e:  # un email raté ne doit jamais faire échouer l'API
        log.error("Échec d'envoi de l'email « %s » à %s : %s", sujet, destinataire, e)
        return False


# --- Emails métier -------------------------------------------------------------------
def mail_reinitialisation(email: str, prenom: str, url: str, heures: int) -> None:
    envoyer(
        email, "Arcanix — choisis un nouveau mot de passe", f"Bonjour {html.escape(prenom)},",
        ["Tu as demandé à réinitialiser ton mot de passe Arcanix.",
         f"Ce lien est personnel, valable <strong>{heures} h</strong> et utilisable une seule fois."],
        ("Choisir mon mot de passe", url),
        "Si tu n'es pas à l'origine de cette demande, ignore simplement cet email : ton mot de passe reste inchangé.",
    )


def mail_invitation(email: str, prenom: str, url: str, heures: int, invite_par: str) -> None:
    envoyer(
        email, "Bienvenue dans l'association Arcanix 🔥", f"Bienvenue {html.escape(prenom)} !",
        [f"{html.escape(invite_par)} t'a créé un compte sur le site de l'association Arcanix.",
         "Tu pourras y suivre tes points, t'inscrire aux séances et grimper au classement.",
         f"Il te reste à choisir ton mot de passe (lien valable <strong>{heures} h</strong>)."],
        ("Activer mon compte", url),
    )


def mail_place_liberee(email: str, prenom: str, seance_nom: str, date_txt: str, url: str) -> None:
    envoyer(
        email, f"Une place s'est libérée : {seance_nom}", f"Bonne nouvelle {html.escape(prenom)} !",
        [f"Une place s'est libérée pour <strong>{html.escape(seance_nom)}</strong> ({html.escape(date_txt)}).",
         "Tu passes de la liste d'attente aux inscrits. Si tu ne peux plus venir, pense à te désinscrire."],
        ("Voir la séance", url),
    )

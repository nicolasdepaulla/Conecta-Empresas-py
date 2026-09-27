"""Envio de e-mails via SMTP (Gmail). Usado para redefinição de senha."""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger("conecta.email")


def enviar_email_redefinicao_senha(destinatario: str, link_redefinicao: str) -> None:
    if not settings.smtp_user or not settings.smtp_password:
        if settings.is_production:
            # Em produção, nunca loga o link (ele contém o token de reset) --
            # SMTP não configurado ali é um erro de configuração real, não
            # algo pra simular silenciosamente como em desenvolvimento.
            logger.error(
                "SMTP não configurado em produção -- e-mail de redefinição de senha NÃO enviado para %s",
                destinatario,
            )
            return

        # Em desenvolvimento, sem SMTP configurado, só loga o link no console
        # em vez de falhar -- assim dá pra testar o fluxo sem e-mail real.
        logger.info(
            "[EMAIL SIMULADO] Link de redefinição de senha para %s: %s",
            destinatario,
            link_redefinicao,
        )
        return

    mensagem = MIMEMultipart("alternative")
    mensagem["Subject"] = "Redefinição de senha — Conecta Empresas"
    mensagem["From"] = settings.smtp_from_email or settings.smtp_user
    mensagem["To"] = destinatario

    texto = f"Clique no link para redefinir sua senha: {link_redefinicao}\nEsse link expira em 30 minutos."
    html = f"""
    <div style="font-family: sans-serif; max-width: 480px;">
      <h2>Redefinição de senha</h2>
      <p>Recebemos uma solicitação para redefinir a senha da sua conta no Conecta Empresas.</p>
      <p><a href="{link_redefinicao}" style="background:#2F6F62;color:#fff;padding:10px 18px;
         border-radius:4px;text-decoration:none;">Redefinir minha senha</a></p>
      <p style="color:#888;font-size:0.85em;">Esse link expira em 30 minutos. Se você não solicitou isso,
      pode ignorar este e-mail.</p>
    </div>
    """
    mensagem.attach(MIMEText(texto, "plain"))
    mensagem.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as servidor:
        servidor.starttls()
        servidor.login(settings.smtp_user, settings.smtp_password)
        servidor.sendmail(mensagem["From"], destinatario, mensagem.as_string())

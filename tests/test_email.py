import logging
from unittest.mock import MagicMock

from app.core.config import settings
from app.core.email import enviar_email_redefinicao_senha

LINK_COM_TOKEN = "https://exemplo.com/redefinir-senha.html?token=SEGREDO123"


def test_sem_smtp_em_desenvolvimento_loga_o_link(monkeypatch, caplog):
    """
    Sem SMTP configurado, em desenvolvimento o link (com token) deve
    aparecer no log -- é assim que se testa o fluxo sem e-mail real.
    """
    monkeypatch.setattr(settings, "ambiente", "development")
    monkeypatch.setattr(settings, "smtp_user", "")
    monkeypatch.setattr(settings, "smtp_password", "")

    with caplog.at_level(logging.INFO, logger="conecta.email"):
        enviar_email_redefinicao_senha("user@teste.com", LINK_COM_TOKEN)

    assert "SEGREDO123" in caplog.text
    assert "EMAIL SIMULADO" in caplog.text


def test_sem_smtp_em_producao_nao_loga_o_link(monkeypatch, caplog):
    """
    Sem SMTP configurado, em produção o token NUNCA pode aparecer no log --
    deve sair só um erro genérico avisando que o e-mail não foi enviado.
    """
    monkeypatch.setattr(settings, "ambiente", "production")
    monkeypatch.setattr(settings, "smtp_user", "")
    monkeypatch.setattr(settings, "smtp_password", "")

    with caplog.at_level(logging.INFO, logger="conecta.email"):
        enviar_email_redefinicao_senha("user@teste.com", LINK_COM_TOKEN)

    assert "SEGREDO123" not in caplog.text
    assert LINK_COM_TOKEN not in caplog.text
    assert any(record.levelname == "ERROR" for record in caplog.records)


def test_com_smtp_configurado_envia_email_de_verdade_sem_logar_token(monkeypatch, caplog):
    """
    Com SMTP configurado (independente do ambiente), a função deve tentar
    enviar o e-mail de verdade via smtplib -- aqui simulamos o servidor
    SMTP (sem rede real) só pra confirmar que login/sendmail são chamados
    corretamente, e que esse caminho não loga o link em lugar nenhum.
    """
    monkeypatch.setattr(settings, "ambiente", "production")
    monkeypatch.setattr(settings, "smtp_user", "app@gmail.com")
    monkeypatch.setattr(settings, "smtp_password", "senha-de-app")
    monkeypatch.setattr(settings, "smtp_from_email", "app@gmail.com")
    monkeypatch.setattr(settings, "smtp_host", "smtp.gmail.com")
    monkeypatch.setattr(settings, "smtp_port", 587)

    servidor_falso = MagicMock()
    servidor_falso.__enter__.return_value = servidor_falso
    smtp_mock = MagicMock(return_value=servidor_falso)
    monkeypatch.setattr("app.core.email.smtplib.SMTP", smtp_mock)

    with caplog.at_level(logging.INFO, logger="conecta.email"):
        enviar_email_redefinicao_senha("user@teste.com", LINK_COM_TOKEN)

    smtp_mock.assert_called_once_with("smtp.gmail.com", 587)
    servidor_falso.starttls.assert_called_once()
    servidor_falso.login.assert_called_once_with("app@gmail.com", "senha-de-app")
    servidor_falso.sendmail.assert_called_once()

    remetente_chamada, destinatario_chamada, corpo_chamada = (
        servidor_falso.sendmail.call_args.args
    )
    assert remetente_chamada == "app@gmail.com"
    assert destinatario_chamada == "user@teste.com"
    assert LINK_COM_TOKEN in corpo_chamada

    # o link só deve existir dentro do corpo do e-mail simulado, não no log
    assert "SEGREDO123" not in caplog.text

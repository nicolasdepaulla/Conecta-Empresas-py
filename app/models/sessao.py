from pydantic import BaseModel


class Sessao(BaseModel):
    """
    Bloco de conteúdo reutilizável entre pacotes (ex.: 'Dados de Contato
    Empresarial'), para não repetir o mesmo texto em cada pacote.
    """
    titulo: str
    itens: list[str]

from pydantic import BaseModel


class Pacote(BaseModel):
    slug: str                 # ex.: "imobiliario" - usado na URL /pacotes/{slug}
    nome: str                 # ex.: "Pacote Premium Imobiliário"
    setor: str
    preco: float
    quantidade_contatos: int
    imagem: str
    sessao_id: str            # referência ao _id em 'sessoes'
    cobrar_id: str            # id da tabela de preço na cobrança/pagamento


class PacoteComSessao(Pacote):
    """Usado nas respostas da API, já com a sessão resolvida via $lookup."""
    sessao: Sessao

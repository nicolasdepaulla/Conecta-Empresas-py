# Conecta Empresas — API

![Testes](https://github.com/nicolasdepaulla/Conecta-Empresas-py/actions/workflows/tests.yml/badge.svg)

Sistema de venda de pacotes de dados personalizados para consórcios, com foco em setores como imobiliário, automotivo e turismo. Este repositório contém o backend, reescrito em Python como evolução de uma versão anterior em Node.js, com arquitetura em camadas e modelagem de dados otimizada para evitar duplicação de conteúdo entre pacotes.

## Stack

- **FastAPI** — framework web assíncrono, com documentação automática (Swagger/OpenAPI)
- **MongoDB** (via Motor, driver assíncrono) — persistência de dados
- **JWT + bcrypt** — autenticação e hash de senhas
- **Pydantic** — validação de dados e schemas

## Arquitetura

O projeto segue uma separação em camadas para manter a regra de negócio isolada do acesso a dados e das rotas HTTP:

```
app/
├── core/          # configuração, conexão com o banco, segurança
├── models/        # schemas Pydantic (formato dos dados)
├── routers/       # endpoints HTTP (camada de entrada)
├── services/       # regras de negócio
└── repositories/   # acesso ao banco de dados (queries)
```

**Fluxo de uma requisição:** `router` recebe a chamada → aciona o `service` correspondente → o `service` aplica as regras de negócio e usa o `repository` para consultar/gravar no banco.

## Modelagem de dados

Para evitar repetição de conteúdo entre pacotes (problema presente na versão anterior), as seções de conteúdo dos pacotes foram extraídas para uma collection própria (`sessoes`), referenciada pelos pacotes em vez de embutida — o equivalente, no MongoDB, a uma normalização de dados relacional. Junções são feitas via `$lookup` na aggregation pipeline.

## Como rodar localmente

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # preencher com suas credenciais
uvicorn app.main:app --reload
```

A documentação interativa da API fica disponível em `http://localhost:8000/docs`.

## Status do projeto

🚧 Em desenvolvimento — migração ativa do backend original em Node.js/Express para Python/FastAPI.

## Roadmap

- [x] Definição da arquitetura em camadas
- [x] Modelagem das collections `pacotes` e `sessoes`
- [x] Autenticação (JWT + bcrypt, cookie httpOnly)
- [x] Listagem/consulta de pacotes com sessão resolvida via `$lookup`
- [x] Script de seed com os dados reais migrados do projeto original
- [x] Migração do front-end (login, cadastro, listagem de pacotes, meus pedidos)
- [x] Integração de pagamento real (Mercado Pago Checkout Pro)
- [x] Testes automatizados

## Testes automatizados

Os testes usam `pytest` + `pytest-asyncio` e não dependem de um MongoDB real
nem do Mercado Pago de verdade — toda chamada externa é simulada, então
rodam rápido e sem precisar de `.env` configurado.

```bash
pip install -r requirements-dev.txt
pytest -v
```

Cobrem: hash de senha e JWT, cadastro/login (usuário duplicado, senha errada),
criação de checkout, e a lógica do webhook de pagamento (aprovado, rejeitado,
pendente) — essa última parte é a mais importante, porque o checkout do
Mercado Pago em sandbox tem travado no navegador (problema conhecido de
cookies de terceiros), então os testes automatizados são o que garante que a
lógica de confirmação de pagamento está correta.

## Correções feitas em relação ao projeto original

- Removida credencial de banco de dados exposta no código-fonte
- Corrigido: cadastro de usuário agora salva o e-mail informado (era ignorado)
- Pacotes de Turismo, Petshop e Fitness (R$ 1000) não são mais associados por engano ao checkout de R$ 130

## Licença

Este projeto está sob a licença ISC.

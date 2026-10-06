/**
 * Transforma a resposta de erro da API num texto legível pro usuário.
 *
 * A API devolve erro de duas formas bem diferentes, e cada página tratava
 * só uma delas (daí o "[object Object]" aparecendo na tela):
 *
 * - Erro "normal" da aplicação (HTTPException do FastAPI), ex.: senha
 *   errada, e-mail já cadastrado -> { "detail": "texto pronto pra mostrar" }
 * - Erro de validação do Pydantic (422), ex.: senha curta, e-mail mal
 *   formatado -> { "detail": [ { "loc": [...], "msg": "...", "type": "..." } ] }
 *   -- uma LISTA de objetos, não um texto.
 * - Limite de requisições (rate limiting, 429) -> { "error": "texto" },
 *   num campo diferente dos outros dois.
 */
function extrairMensagemDeErro(data, fallback) {
  if (!data) return fallback;

  if (Array.isArray(data.detail)) {
    const mensagens = data.detail.map(function (erro) {
      if (erro.type === 'string_too_short' && erro.ctx) {
        return 'Esse campo precisa ter pelo menos ' + erro.ctx.min_length + ' caracteres.';
      }
      if (erro.type === 'value_error' && (erro.loc || []).includes('email')) {
        return 'Informe um e-mail válido.';
      }
      return erro.msg || fallback;
    });
    return mensagens.join(' ');
  }

  if (typeof data.detail === 'string') {
    return data.detail;
  }

  if (typeof data.error === 'string') {
    return 'Muitas tentativas em pouco tempo. Aguarde um instante e tente novamente.';
  }

  return fallback;
}

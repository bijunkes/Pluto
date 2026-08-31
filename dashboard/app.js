
/**
 * Pluto · Dashboard
 *
 * Helper de API compartilhado entre login.html e index.html.
 *
 * O usuário é identificado pelo backend através da sessão autenticada.
 * O frontend não precisa enviar o usuarioId nas requisições.
 */

const API_BASE = "";


/**
 * Executa uma requisição para a API.
 */
async function apiFetch(caminho, opcoes = {}) {

  const resposta = await fetch(
    `${API_BASE}${caminho}`,
    {
      credentials: "include",

      headers: {
        "Content-Type": "application/json",
        ...(opcoes.headers || {})
      },

      ...opcoes
    }
  );


  if (!resposta.ok) {

    let detalhe = `Erro ${resposta.status}`;

    try {

      const corpo =
        await resposta.json();

      detalhe =
        corpo.detail || detalhe;

    } catch (_) {

      // Resposta sem JSON.
      // Mantém a mensagem genérica.

    }

    throw new Error(detalhe);
  }


  if (resposta.status === 204) {
    return null;
  }


  return resposta.json();
}


const PlutoAPI = {

  // =====================================================
  // AUTENTICAÇÃO
  // =====================================================

  trocarTokenPorSessao(token) {

    return apiFetch(
      "/auth/sessao",
      {
        method: "POST",

        body: JSON.stringify({
          token
        })
      }
    );

  },


  usuarioAtual() {

    return apiFetch(
      "/auth/me"
    );

  },


  sair() {

    return apiFetch(
      "/auth/logout",
      {
        method: "POST"
      }
    );

  },


  // =====================================================
  // COMPRAS
  // =====================================================

  listarCompras() {

    return apiFetch(
      "/compras"
    );

  },


  criarCompra(compra) {

    return apiFetch(
      "/compras",
      {
        method: "POST",

        body: JSON.stringify(
          compra
        )
      }
    );

  },


  // =====================================================
  // CATEGORIAS
  // =====================================================

  listarCategorias() {

    return apiFetch(
      "/categorias"
    );

  },


  criarCategoria(nome) {

    return apiFetch(
      "/categorias",
      {
        method: "POST",

        body: JSON.stringify({
          nome
        })
      }
    );

  }

};
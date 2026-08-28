/**
 * Pluto · Dashboard
 *
 * Helper de API compartilhado entre login.html e index.html.
 *
 * Por padrão assume que o dashboard é servido pela própria API
 * (FastAPI monta a pasta `dashboard/` na raiz — veja main.py), daí
 * os caminhos relativos abaixo. Se um dia o dashboard for hospedado
 * separado da API, troque API_BASE pela URL completa da API (ex:
 * "https://api.seudominio.com") e garanta que DASHBOARD_URL no
 * .env da API aponte pra origem do dashboard, pro CORS liberar.
 */

const API_BASE = "";

async function apiFetch(caminho, opcoes = {}) {

  const resposta = await fetch(`${API_BASE}${caminho}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...opcoes
  });

  if (!resposta.ok) {

    let detalhe = `Erro ${resposta.status}`;

    try {
      const corpo = await resposta.json();
      detalhe = corpo.detail || detalhe;
    } catch (_) {
      // resposta sem corpo JSON, mantém a mensagem genérica
    }

    throw new Error(detalhe);
  }

  if (resposta.status === 204) return null;

  return resposta.json();
}

const PlutoAPI = {

  trocarTokenPorSessao(token) {
    return apiFetch("/auth/sessao", {
      method: "POST",
      body: JSON.stringify({ token })
    });
  },

  usuarioAtual() {
    return apiFetch("/auth/me");
  },

  sair() {
    return apiFetch("/auth/logout", { method: "POST" });
  },

  listarCompras(usuarioId) {
    return apiFetch(`/usuarios/${usuarioId}/compras`);
  },

  criarCompra(usuarioId, compra) {
    return apiFetch(`/usuarios/${usuarioId}/compras`, {
      method: "POST",
      body: JSON.stringify(compra)
    });
  },

  listarCategorias(usuarioId) {
    return apiFetch(`/usuarios/${usuarioId}/categorias`);
  },

  criarCategoria(usuarioId, nome) {
    return apiFetch(`/usuarios/${usuarioId}/categorias`, {
      method: "POST",
      body: JSON.stringify({ nome })
    });
  }

};

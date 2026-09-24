const API_BASE = "";

let usuarioIdSessao = null;
let contas = [];
let categorias = [];
let compras = [];
let resumoFinanceiro = null;

// ============================================================
// API
// ============================================================

async function apiFetch(url, options = {}) {

    const resposta = await fetch(`${API_BASE}${url}`, {

        credentials: "include",

        ...options,

        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        }

    });


    if (!resposta.ok) {

        let mensagem = "Ocorreu um erro.";

        try {

            const erro = await resposta.json();

            mensagem =
                erro.detail ||
                erro.message ||
                mensagem;

        } catch (_) { }


        if (resposta.status === 401) {

            window.location.href = "/login.html";

        }


        throw new Error(mensagem);

    }


    if (resposta.status === 204) {
        return null;
    }


    return resposta.json();

}

// ============================================================
// AUTENTICAÇÃO
// ============================================================

async function usuarioAtual() {

    const sessao = await apiFetch("/auth/me");

    usuarioIdSessao = sessao.usuario_id;

    return sessao;

}

// ============================================================
// COMPRAS
// ============================================================

async function listarCompras() {


    compras = await apiFetch(
        `/usuarios/${usuarioIdSessao}/compras`
    );

    renderizarCompras();

    atualizarResumo();

}

async function carregarResumoFinanceiro() {

    resumoFinanceiro = await apiFetch(
        `/usuarios/${usuarioIdSessao}/resumo-financeiro`
    );

    atualizarResumo();

}

async function criarCompra(dados) {

    const compra = await apiFetch(
        `/usuarios/${usuarioIdSessao}/compras`,
        {
            method: "POST",
            body: JSON.stringify(dados)
        }
    );


    compras.unshift(compra);


    await Promise.all([
        listarCompras(),
        listarContas(),
        carregarResumoFinanceiro()
    ]);


    return compra;

}

// ============================================================
// CONTAS
// ============================================================

async function listarContas() {


    contas = await apiFetch(
        `/usuarios/${usuarioIdSessao}/contas`
    );


    renderizarContas();

    preencherSelectContas();

    atualizarResumo();

    await carregarResumoFinanceiro();

}

async function criarConta(dados) {

    const conta = await apiFetch(
        `/usuarios/${usuarioIdSessao}/contas`,
        {
            method: "POST",
            body: JSON.stringify(dados)
        }
    );


    contas.push(conta);

    renderizarContas();

    preencherSelectContas();

    atualizarResumo();

    return conta;

}

// ============================================================
// CATEGORIAS
// ============================================================

async function listarCategorias() {

    categorias = await apiFetch(
        `/usuarios/${usuarioIdSessao}/categorias`
    );


    renderizarCategorias();

    preencherSelectCategorias();

}

async function criarCategoria(dados) {

    const categoria = await apiFetch(
        `/usuarios/${usuarioIdSessao}/categorias`,
        {
            method: "POST",
            body: JSON.stringify(dados)
        }
    );


    categorias.push(categoria);

    renderizarCategorias();

    preencherSelectCategorias();

    return categoria;

}

// ============================================================
// RENDER CONTAS
// ============================================================

function renderizarContas() {

    const lista =
        document.getElementById("lista-contas");

    const vazio =
        document.getElementById("contas-vazio");


    if (!lista) return;


    lista.innerHTML = "";


    if (!contas.length) {

        if (vazio) {
            vazio.hidden = false;
        }

        return;
    }


    if (vazio) {
        vazio.hidden = true;
    }


    contas.forEach(conta => {

        const card =
            document.createElement("div");


        card.className = "conta-card";


        const tipo =
            formatarTipoConta(conta.tipo);


        const saldo =
            Number(conta.saldo ?? 0);


        card.innerHTML = `

        <div class="conta-card-topo">

            <span class="conta-icone">
                ${tipo.icone}
            </span>

            <span class="conta-tipo">
                ${tipo.nome}
            </span>

        </div>

        <h3>
            ${escapeHtml(conta.nome)}
        </h3>

        <p class="conta-saldo">
            ${formatarMoeda(saldo)}
        </p>

    `;


        lista.appendChild(card);

    });

}

// ============================================================
// SELECT DE CONTAS
// ============================================================

function preencherSelectContas() {

    const select =
        document.getElementById("campo-conta");


    if (!select) return;


    select.innerHTML = `

    <option value="">
        Selecione uma conta
    </option>

`;


    contas.forEach(conta => {

        const option =
            document.createElement("option");


        option.value = conta.id;


        option.textContent =
            `${conta.nome} — ${formatarMoeda(conta.saldo)}`;


        select.appendChild(option);

    });

}

// ============================================================
// SELECT DE CATEGORIAS
// ============================================================

function preencherSelectCategorias() {

    const select =
        document.getElementById("campo-categoria");


    if (!select) return;


    select.innerHTML = `

    <option value="">
        Selecione uma categoria
    </option>

`;


    categorias.forEach(categoria => {

        const option =
            document.createElement("option");


        option.value = categoria.nome;


        option.textContent =
            categoria.nome;


        select.appendChild(option);

    });

}

// ============================================================
// RENDER CATEGORIAS
// ============================================================

function renderizarCategorias() {

    const lista =
        document.getElementById("lista-categorias");


    if (!lista) return;


    lista.innerHTML = "";


    categorias.forEach(categoria => {

        const item =
            document.createElement("span");


        item.className =
            "categoria-item";


        item.textContent =
            categoria.nome;


        lista.appendChild(item);

    });

}

// ============================================================
// RENDER COMPRAS
// ============================================================

function renderizarCompras() {

    const lista =
        document.getElementById("lista-compras");

    const vazio =
        document.getElementById("compras-vazio");


    if (!lista) return;


    lista.innerHTML = "";


    if (!compras.length) {

        if (vazio) {
            vazio.hidden = false;
        }

        return;
    }


    if (vazio) {
        vazio.hidden = true;
    }


    compras.forEach(compra => {

        const item =
            document.createElement("li");


        item.className =
            "compra-item";


        item.innerHTML = `

        <div class="compra-info">

            <strong>
                ${escapeHtml(compra.produto)}
            </strong>

            <span>
                ${escapeHtml(compra.categoria)}
            </span>

        </div>

        <strong class="compra-valor">
            ${formatarMoeda(compra.valor)}
        </strong>

    `;


        lista.appendChild(item);

    });

}

// ============================================================
// RESUMO
// ============================================================

function atualizarResumo() {

    let totalGasto = compras.reduce(
        (total, compra) =>
            total + Number(compra.valor || 0),
        0
    );


    let saldoTotal = contas.reduce(
        (total, conta) =>
            total + Number(conta.saldo || 0),
        0
    );


    const totalGastoElemento =
        document.getElementById("total-gasto");


    const totalComprasElemento =
        document.getElementById("total-compras");


    const saldoTotalElemento =
        document.getElementById("saldo-total");


    const mediaDiariaElemento =
        document.getElementById("media-diaria");


    const projecaoMensalElemento =
        document.getElementById("projecao-mensal");


    const coberturaSaldoElemento =
        document.getElementById("cobertura-saldo");


    const variacaoMensalElemento =
        document.getElementById("variacao-mensal");


    const maiorCategoriaElemento =
        document.getElementById("maior-categoria");


    if (resumoFinanceiro) {

        totalGasto =
            Number(
                resumoFinanceiro.total_gasto || 0
            );


        saldoTotal =
            Number(
                resumoFinanceiro.saldo_total || 0
            );

    }


    if (totalGastoElemento) {

        totalGastoElemento.textContent =
            formatarMoeda(totalGasto);

    }


    if (totalComprasElemento) {

        totalComprasElemento.textContent =
            resumoFinanceiro
                ? resumoFinanceiro.quantidade_compras
                : compras.length;

    }


    if (saldoTotalElemento) {

        saldoTotalElemento.textContent =
            formatarMoeda(saldoTotal);

    }


    if (mediaDiariaElemento && resumoFinanceiro) {

        mediaDiariaElemento.textContent =
            formatarMoeda(
                resumoFinanceiro.media_diaria
            );

    }


    if (
        projecaoMensalElemento &&
        resumoFinanceiro
    ) {

        projecaoMensalElemento.textContent =
            formatarMoeda(
                resumoFinanceiro.projecao_mensal
            );

    }


    if (
        coberturaSaldoElemento &&
        resumoFinanceiro
    ) {

        const dias =
            resumoFinanceiro.dias_cobertura_saldo;


        coberturaSaldoElemento.textContent =
            dias === null
                ? "Sem estimativa"
                : `${dias} dias`;

    }


    if (
        variacaoMensalElemento &&
        resumoFinanceiro
    ) {

        const variacao =
            resumoFinanceiro
                .mes_anterior
                .variacao_percentual;


        variacaoMensalElemento.textContent =
            variacao === null
                ? "Sem comparação"
                : `${variacao > 0 ? "+" : ""}${variacao.toLocaleString("pt-BR")}%`;

    }


    if (
        maiorCategoriaElemento &&
        resumoFinanceiro
    ) {

        const categoria =
            resumoFinanceiro
                .gastos_por_categoria[0];


        maiorCategoriaElemento.textContent =
            categoria
                ? `${categoria.categoria} (${categoria.percentual.toLocaleString("pt-BR")}%)`
                : "Sem gastos";

    }

}

// ============================================================
// FORMULÁRIO DE CONTA
// ============================================================

function configurarFormularioConta() {


    const form =
        document.getElementById("form-conta");


    if (!form) return;


    form.addEventListener(
        "submit",
        async event => {

            event.preventDefault();


            const erro =
                document.getElementById("conta-erro");


            if (erro) {
                erro.textContent = "";
            }


            const nome =
                document
                    .getElementById("campo-nome-conta")
                    .value
                    .trim();


            const tipo =
                document
                    .getElementById("campo-tipo-conta")
                    .value;


            const saldo =
                Number(
                    document
                        .getElementById("campo-saldo-conta")
                        .value || 0
                );


            if (!nome) {

                if (erro) {
                    erro.textContent =
                        "Informe o nome da conta.";
                }

                return;
            }


            try {

                await criarConta({

                    nome,

                    tipo,

                    saldoInicial: saldo

                });


                form.reset();


            } catch (error) {

                if (erro) {
                    erro.textContent =
                        error.message;
                }

            }

        }
    );

}

// ============================================================
// FORMULÁRIO DE COMPRA
// ============================================================

function configurarFormularioCompra() {


    const form =
        document.getElementById("form-compra");


    if (!form) return;


    form.addEventListener(
        "submit",
        async event => {

            event.preventDefault();


            const erro =
                document.getElementById("compra-erro");


            if (erro) {
                erro.textContent = "";
            }


            const produto =
                document
                    .getElementById("campo-produto")
                    .value
                    .trim();


            const categoria =
                document
                    .getElementById("campo-categoria")
                    .value;


            const contaId =
                document
                    .getElementById("campo-conta")
                    .value;


            const valor =
                Number(
                    document
                        .getElementById("campo-valor")
                        .value
                );


            if (!produto) {

                if (erro) {
                    erro.textContent =
                        "Informe o produto.";
                }

                return;
            }


            if (!categoria) {

                if (erro) {
                    erro.textContent =
                        "Selecione uma categoria.";
                }

                return;
            }


            if (!contaId) {

                if (erro) {
                    erro.textContent =
                        "Selecione uma conta.";
                }

                return;
            }


            if (!Number.isFinite(valor) || valor < 0) {

                if (erro) {
                    erro.textContent =
                        "Informe um valor válido.";
                }

                return;
            }


            try {

                await criarCompra({

                    produto,

                    categoria,

                    valor,

                    contaId: Number(contaId)

                });


                form.reset();


            } catch (error) {

                if (erro) {
                    erro.textContent =
                        error.message;
                }

            }

        }
    );

}

// ============================================================
// FORMULÁRIO DE CATEGORIA
// ============================================================

function configurarFormularioCategoria() {


    const form =
        document.getElementById("form-categoria");


    if (!form) return;


    form.addEventListener(
        "submit",
        async event => {

            event.preventDefault();


            const erro =
                document.getElementById("categoria-erro");


            if (erro) {
                erro.textContent = "";
            }


            const nome =
                document
                    .getElementById("campo-nova-categoria")
                    .value
                    .trim();


            if (!nome) {

                if (erro) {
                    erro.textContent =
                        "Informe o nome da categoria.";
                }

                return;
            }


            try {

                await criarCategoria({
                    nome
                });


                form.reset();


            } catch (error) {

                if (erro) {
                    erro.textContent =
                        error.message;
                }

            }

        }
    );

}

// ============================================================
// LOGOUT
// ============================================================

function configurarLogout() {

    const botao =
        document.getElementById("btn-sair");


    if (!botao) return;


    botao.addEventListener(
        "click",
        async () => {

            try {

                await apiFetch(
                    "/auth/logout",
                    {
                        method: "POST"
                    }
                );


            } finally {

                window.location.href =
                    "/login.html";

            }

        }
    );

}

// ============================================================
// TEMA
// ============================================================

function configurarTema() {

    const botao =
        document.getElementById("btn-tema");

    const icone =
        document.getElementById("icone-tema");

    if (!botao) {
        console.warn("Botão de tema não encontrado.");
        return;
    }


    function aplicarTema(tema) {

        const temaFinal =
            tema === "light"
                ? "light"
                : "dark";


        // Aplica diretamente no BODY
        document.body.classList.toggle(
            "tema-claro",
            temaFinal === "light"
        );


        // Mantém também no HTML
        // para persistência/compatibilidade
        document.documentElement.setAttribute(
            "data-theme",
            temaFinal
        );


        localStorage.setItem(
            "pluto_tema",
            temaFinal
        );


        atualizarIcone(temaFinal);
    }


    function atualizarIcone(tema) {

        if (icone) {

            icone.textContent =
                tema === "dark"
                    ? "☀️"
                    : "🌙";

        }


        botao.setAttribute(
            "aria-label",
            tema === "dark"
                ? "Ativar modo claro"
                : "Ativar modo escuro"
        );


        botao.setAttribute(
            "title",
            tema === "dark"
                ? "Ativar modo claro"
                : "Ativar modo escuro"
        );

    }


    // Tema salvo
    const salvo =
        localStorage.getItem("pluto_tema");


    // Tema do sistema
    const sistema =
        window.matchMedia(
            "(prefers-color-scheme: light)"
        ).matches
            ? "light"
            : "dark";


    // Prioridade:
    // 1. escolha salva pelo usuário
    // 2. sistema operacional
    const temaInicial =
        salvo || sistema;


    aplicarTema(temaInicial);


    botao.addEventListener(
        "click",
        () => {

            const temaAtual =
                document.body.classList.contains(
                    "tema-claro"
                )
                    ? "light"
                    : "dark";


            const novoTema =
                temaAtual === "dark"
                    ? "light"
                    : "dark";


            aplicarTema(novoTema);


            console.log(
                "Pluto — tema:",
                novoTema
            );

        }
    );

}

// ============================================================
// UTILITÁRIOS
// ============================================================

function formatarMoeda(valor) {

    return new Intl.NumberFormat(
        "pt-BR",
        {
            style: "currency",
            currency: "BRL"
        }
    ).format(Number(valor) || 0);

}

function formatarTipoConta(tipo) {

    const tipos = {

        CARTEIRA: {
            nome: "Carteira",
            icone: "💵"
        },

        CONTA_CORRENTE: {
            nome: "Conta corrente",
            icone: "💳"
        },

        POUPANCA: {
            nome: "Poupança",
            icone: "🏦"
        },

        INVESTIMENTO: {
            nome: "Investimento",
            icone: "📈"
        }

    };


    return tipos[tipo] || {

        nome: tipo,

        icone: "💰"

    };

}

function escapeHtml(texto) {

    const div =
        document.createElement("div");


    div.textContent =
        texto ?? "";


    return div.innerHTML;

}

// ============================================================
// INICIALIZAÇÃO
// ============================================================

async function inicializarDashboard() {

    const telaCarregando =
        document.getElementById("tela-carregando");

    const pagina =
        document.getElementById("pagina");


    // O tema é configurado primeiro.
    configurarTema();


    try {

        await usuarioAtual();


        await Promise.all([
            listarContas(),
            listarCompras(),
            listarCategorias(),
            carregarResumoFinanceiro()
        ]);


        configurarFormularioConta();

        configurarFormularioCompra();

        configurarFormularioCategoria();

        configurarLogout();


        if (pagina) {
            pagina.hidden = false;
        }


    } catch (error) {

        console.error(
            "Erro ao inicializar dashboard:",
            error
        );

        window.location.href =
            "/login.html";


    } finally {

        if (telaCarregando) {
            telaCarregando.hidden = true;
        }

    }

}


document.addEventListener(
    "DOMContentLoaded",
    inicializarDashboard
);
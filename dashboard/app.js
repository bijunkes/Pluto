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

            if (!window.location.pathname.endsWith("login.html")) {
                window.location.href = "/login.html";
            }

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


        card.insertAdjacentHTML(
            "beforeend",
            `
            <div class="acoes-item">
                <button type="button" class="btn-mini" data-acao="editar-conta" data-id="${conta.id}" title="Editar conta" aria-label="Editar conta">✏️</button>
                <button type="button" class="btn-mini perigo" data-acao="excluir-conta" data-id="${conta.id}" title="Excluir conta" aria-label="Excluir conta">🗑️</button>
            </div>
            `
        );


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


        // Categorias padrão não podem ser alteradas nem excluídas.
        if (categoria.tipo === "PERSONALIZADA") {

            item.insertAdjacentHTML(
                "beforeend",
                `
                <button type="button" class="btn-mini" data-acao="editar-categoria" data-id="${categoria.id}" title="Editar categoria" aria-label="Editar categoria">✏️</button>
                <button type="button" class="btn-mini perigo" data-acao="excluir-categoria" data-id="${categoria.id}" title="Excluir categoria" aria-label="Excluir categoria">🗑️</button>
                `
            );

        }


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

        <div class="acoes-item">
            <button type="button" class="btn-mini" data-acao="editar-compra" data-id="${compra.id}" title="Editar compra" aria-label="Editar compra">✏️</button>
            <button type="button" class="btn-mini perigo" data-acao="excluir-compra" data-id="${compra.id}" title="Excluir compra" aria-label="Excluir compra">🗑️</button>
        </div>

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

        configurarAcoesItens();


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


// ============================================================
// EDITAR E EXCLUIR (CONTAS E COMPRAS)
// ============================================================

let contaEmEdicao = null;
let compraEmEdicao = null;

// ============================================================
// AVISOS (TOAST) E CONFIRMAÇÃO
// ============================================================

function mostrarAviso(mensagem, tipo = "erro") {

    let container =
        document.getElementById("toasts");

    if (!container) {

        container = document.createElement("div");
        container.id = "toasts";
        container.className = "toasts";
        container.setAttribute("role", "status");
        container.setAttribute("aria-live", "polite");

        document.body.appendChild(container);

    }

    const aviso = document.createElement("div");

    aviso.className = `toast ${tipo}`;
    aviso.textContent = mensagem;

    const remover = () => aviso.remove();

    aviso.addEventListener("click", remover);

    setTimeout(remover, 5000);

    container.appendChild(aviso);

}

function confirmar({ titulo, mensagem, textoConfirmar = "Confirmar" }) {

    return new Promise(resolve => {

        const modal = document.createElement("dialog");

        modal.className = "modal";

        modal.innerHTML = `
        <form class="modal-form">
            <h3></h3>
            <p class="modal-texto"></p>
            <div class="modal-acoes">
                <button type="button" class="botao-secundario" data-cancelar>Cancelar</button>
                <button type="submit" class="botao botao-perigo"></button>
            </div>
        </form>
        `;

        // textContent evita interpretar HTML vindo dos nomes digitados.
        modal.querySelector("h3").textContent = titulo;
        modal.querySelector(".modal-texto").textContent = mensagem;
        modal.querySelector(".botao-perigo").textContent = textoConfirmar;

        let confirmado = false;

        modal.querySelector("form").addEventListener("submit", event => {
            event.preventDefault();
            confirmado = true;
            modal.close();
        });

        modal.querySelector("[data-cancelar]").addEventListener(
            "click",
            () => modal.close()
        );

        modal.addEventListener("click", event => {
            if (event.target === modal) {
                modal.close();
            }
        });

        // Fecha por Cancelar, Esc, clique no fundo ou confirmação.
        modal.addEventListener("close", () => {
            modal.remove();
            resolve(confirmado);
        });

        document.body.appendChild(modal);

        modal.showModal();

    });

}

async function atualizarConta(contaId, dados) {

    await apiFetch(
        `/usuarios/${usuarioIdSessao}/contas/${contaId}`,
        {
            method: "PUT",
            body: JSON.stringify(dados)
        }
    );

    // O nome da conta aparece nas compras, então recarrega as duas listas.
    await Promise.all([
        listarContas(),
        listarCompras()
    ]);

}

async function excluirConta(contaId) {

    await apiFetch(
        `/usuarios/${usuarioIdSessao}/contas/${contaId}`,
        { method: "DELETE" }
    );

    await Promise.all([
        listarContas(),
        listarCompras()
    ]);

}

async function atualizarCompra(compraId, dados) {

    await apiFetch(
        `/usuarios/${usuarioIdSessao}/compras/${compraId}`,
        {
            method: "PUT",
            body: JSON.stringify(dados)
        }
    );

    // O saldo das contas muda junto com a compra.
    await Promise.all([
        listarCompras(),
        listarContas()
    ]);

}

async function excluirCompra(compraId) {

    await apiFetch(
        `/usuarios/${usuarioIdSessao}/compras/${compraId}`,
        { method: "DELETE" }
    );

    await Promise.all([
        listarCompras(),
        listarContas()
    ]);

}

function abrirModalConta(contaId) {

    const conta =
        contas.find(c => c.id === contaId);

    if (!conta) return;

    contaEmEdicao = conta.id;

    document.getElementById("campo-editar-nome-conta").value =
        conta.nome;

    document.getElementById("campo-editar-tipo-conta").value =
        conta.tipo;

    document.getElementById("editar-conta-erro").textContent = "";

    document.getElementById("modal-conta").showModal();

}

function abrirModalCompra(compraId) {

    const compra =
        compras.find(c => c.id === compraId);

    if (!compra) return;

    compraEmEdicao = compra.id;


    const selectCategoria =
        document.getElementById("campo-editar-categoria");

    selectCategoria.innerHTML = "";

    categorias.forEach(categoria => {
        selectCategoria.appendChild(
            new Option(categoria.nome, categoria.nome)
        );
    });

    selectCategoria.value = compra.categoria;


    const selectConta =
        document.getElementById("campo-editar-conta");

    selectConta.innerHTML = "";

    // A compra guarda só o nome da conta, então procura o id pelo nome.
    const contaAtual =
        contas.find(c => c.nome === compra.conta);

    if (!contaAtual) {
        selectConta.appendChild(
            new Option("(conta removida — escolha outra)", "")
        );
    }

    contas.forEach(conta => {
        selectConta.appendChild(
            new Option(conta.nome, String(conta.id))
        );
    });

    if (contaAtual) {
        selectConta.value = String(contaAtual.id);
    }


    document.getElementById("campo-editar-produto").value =
        compra.produto;

    document.getElementById("campo-editar-valor").value =
        compra.valor;

    document.getElementById("editar-compra-erro").textContent = "";

    document.getElementById("modal-compra").showModal();

}

async function confirmarExclusaoConta(contaId) {

    const conta =
        contas.find(c => c.id === contaId);

    if (!conta) return;

    const confirmado = await confirmar({
        titulo: "Excluir conta",
        mensagem:
            `Excluir a conta "${conta.nome}"? Ela deixa de aparecer no ` +
            "dashboard, mas as compras já registradas continuam no " +
            "histórico. Você pode reativá-la depois em " +
            "\"Ver contas desativadas\".",
        textoConfirmar: "Excluir"
    });

    if (!confirmado) return;

    try {
        await excluirConta(contaId);
        await recarregarContasInativasSeAbertas();
    } catch (error) {
        mostrarAviso(error.message);
    }

}

async function confirmarExclusaoCompra(compraId) {

    const compra =
        compras.find(c => c.id === compraId);

    if (!compra) return;

    const confirmado = await confirmar({
        titulo: "Excluir compra",
        mensagem:
            `Excluir a compra "${compra.produto}" ` +
            `(${formatarMoeda(compra.valor)})? ` +
            "O valor volta para o saldo da conta.",
        textoConfirmar: "Excluir"
    });

    if (!confirmado) return;

    try {
        await excluirCompra(compraId);
    } catch (error) {
        mostrarAviso(error.message);
    }

}

// ============================================================
// CONTAS DESATIVADAS (VER E REATIVAR)
// ============================================================

let contasInativas = [];

async function listarContasInativas() {

    const todas = await apiFetch(
        `/usuarios/${usuarioIdSessao}/contas?apenas_ativas=false`
    );

    contasInativas = todas.filter(conta => !conta.ativa);

    renderizarContasInativas();

}

function renderizarContasInativas() {

    const lista =
        document.getElementById("lista-contas-inativas");

    const vazio =
        document.getElementById("contas-inativas-vazio");

    if (!lista) return;

    lista.innerHTML = "";

    if (vazio) {
        vazio.hidden = contasInativas.length > 0;
    }

    contasInativas.forEach(conta => {

        const card =
            document.createElement("div");

        card.className = "conta-card inativa";

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

        <div class="acoes-item">
            <button type="button" class="btn-mini" data-acao="reativar-conta" data-id="${conta.id}" title="Reativar conta" aria-label="Reativar conta">♻️ Reativar</button>
        </div>

        `;

        lista.appendChild(card);

    });

}

async function reativarConta(contaId) {

    await apiFetch(
        `/usuarios/${usuarioIdSessao}/contas/${contaId}/reativar`,
        { method: "POST" }
    );

    await Promise.all([
        listarContas(),
        listarContasInativas(),
        listarCompras()
    ]);

}

async function recarregarContasInativasSeAbertas() {

    const area =
        document.getElementById("area-contas-inativas");

    if (area && !area.hidden) {
        await listarContasInativas();
    }

}

async function alternarContasInativas() {

    const area =
        document.getElementById("area-contas-inativas");

    const botao =
        document.getElementById("btn-contas-inativas");

    if (!area || !botao) return;

    const abrindo = area.hidden;

    if (abrindo) {

        try {
            await listarContasInativas();
        } catch (error) {
            mostrarAviso(error.message);
            return;
        }

    }

    area.hidden = !abrindo;

    botao.textContent = abrindo
        ? "Ocultar contas desativadas"
        : "Ver contas desativadas";

    botao.setAttribute("aria-expanded", String(abrindo));

}

let categoriaEmEdicao = null;

async function atualizarCategoria(categoriaId, dados) {

    await apiFetch(
        `/usuarios/${usuarioIdSessao}/categorias/${categoriaId}`,
        {
            method: "PUT",
            body: JSON.stringify(dados)
        }
    );

    // O nome da categoria aparece nas compras, então recarrega as duas listas.
    await Promise.all([
        listarCategorias(),
        listarCompras()
    ]);

}

async function excluirCategoria(categoriaId) {

    await apiFetch(
        `/usuarios/${usuarioIdSessao}/categorias/${categoriaId}`,
        { method: "DELETE" }
    );

    await listarCategorias();

}

function abrirModalCategoria(categoriaId) {

    const categoria =
        categorias.find(c => c.id === categoriaId);

    if (!categoria) return;

    categoriaEmEdicao = categoria.id;

    document.getElementById("campo-editar-nome-categoria").value =
        categoria.nome;

    document.getElementById("editar-categoria-erro").textContent = "";

    document.getElementById("modal-categoria").showModal();

}

async function confirmarExclusaoCategoria(categoriaId) {

    const categoria =
        categorias.find(c => c.id === categoriaId);

    if (!categoria) return;

    const confirmado = await confirmar({
        titulo: "Excluir categoria",
        mensagem:
            `Excluir a categoria "${categoria.nome}"? ` +
            "Isso só é permitido se nenhuma compra estiver usando ela.",
        textoConfirmar: "Excluir"
    });

    if (!confirmado) return;

    try {
        await excluirCategoria(categoriaId);
    } catch (error) {
        // Ex.: categoria em uso por compras.
        mostrarAviso(error.message);
    }

}

function configurarAcoesItens() {

    // Um único listener por lista (delegação), já que os itens
    // são recriados a cada renderização.
    const aoClicar = async event => {

        const botao =
            event.target.closest("[data-acao]");

        if (!botao) return;

        const id = Number(botao.dataset.id);

        switch (botao.dataset.acao) {

            case "editar-conta":
                abrirModalConta(id);
                break;

            case "excluir-conta":
                await confirmarExclusaoConta(id);
                break;

            case "reativar-conta":
                try {
                    await reativarConta(id);
                } catch (error) {
                    mostrarAviso(error.message);
                }
                break;

            case "editar-categoria":
                abrirModalCategoria(id);
                break;

            case "excluir-categoria":
                await confirmarExclusaoCategoria(id);
                break;

            case "editar-compra":
                abrirModalCompra(id);
                break;

            case "excluir-compra":
                await confirmarExclusaoCompra(id);
                break;

        }

    };

    document
        .getElementById("lista-contas")
        ?.addEventListener("click", aoClicar);

    document
        .getElementById("lista-compras")
        ?.addEventListener("click", aoClicar);


    document
        .getElementById("lista-categorias")
        ?.addEventListener("click", aoClicar);


    document
        .getElementById("lista-contas-inativas")
        ?.addEventListener("click", aoClicar);

    document
        .getElementById("btn-contas-inativas")
        ?.addEventListener("click", alternarContasInativas);


    // Fechar modais: botão Cancelar e clique no fundo escuro.
    document.querySelectorAll(".modal").forEach(modal => {

        modal
            .querySelectorAll("[data-fechar]")
            .forEach(botao => {
                botao.addEventListener(
                    "click",
                    () => modal.close()
                );
            });

        modal.addEventListener("click", event => {
            if (event.target === modal) {
                modal.close();
            }
        });

    });


    // Salvar conta.
    document
        .getElementById("form-editar-conta")
        .addEventListener("submit", async event => {

            event.preventDefault();

            const erro =
                document.getElementById("editar-conta-erro");

            const botao =
                event.target.querySelector("[type=submit]");

            erro.textContent = "";

            const nome =
                document
                    .getElementById("campo-editar-nome-conta")
                    .value
                    .trim();

            const tipo =
                document
                    .getElementById("campo-editar-tipo-conta")
                    .value;

            if (!nome) {
                erro.textContent = "Informe o nome da conta.";
                return;
            }

            botao.disabled = true;

            try {
                await atualizarConta(contaEmEdicao, { nome, tipo });
                document.getElementById("modal-conta").close();
            } catch (error) {
                erro.textContent = error.message;
            } finally {
                botao.disabled = false;
            }

        });


    // Salvar categoria.
    document
        .getElementById("form-editar-categoria")
        .addEventListener("submit", async event => {

            event.preventDefault();

            const erro =
                document.getElementById("editar-categoria-erro");

            const botao =
                event.target.querySelector("[type=submit]");

            erro.textContent = "";

            const nome =
                document
                    .getElementById("campo-editar-nome-categoria")
                    .value
                    .trim();

            if (!nome) {
                erro.textContent = "Informe o nome da categoria.";
                return;
            }

            botao.disabled = true;

            try {
                await atualizarCategoria(categoriaEmEdicao, { nome });
                document.getElementById("modal-categoria").close();
            } catch (error) {
                erro.textContent = error.message;
            } finally {
                botao.disabled = false;
            }

        });


    // Salvar compra.
    document
        .getElementById("form-editar-compra")
        .addEventListener("submit", async event => {

            event.preventDefault();

            const erro =
                document.getElementById("editar-compra-erro");

            const botao =
                event.target.querySelector("[type=submit]");

            erro.textContent = "";

            const produto =
                document
                    .getElementById("campo-editar-produto")
                    .value
                    .trim();

            const categoria =
                document
                    .getElementById("campo-editar-categoria")
                    .value;

            const contaValor =
                document
                    .getElementById("campo-editar-conta")
                    .value;

            const valor =
                Number(
                    document
                        .getElementById("campo-editar-valor")
                        .value
                );

            if (!produto) {
                erro.textContent = "Informe o produto.";
                return;
            }

            if (!Number.isFinite(valor) || valor < 0) {
                erro.textContent = "Informe um valor válido.";
                return;
            }

            botao.disabled = true;

            try {

                await atualizarCompra(compraEmEdicao, {
                    produto,
                    categoria,
                    contaId: contaValor ? Number(contaValor) : undefined,
                    valor
                });

                document.getElementById("modal-compra").close();

            } catch (error) {
                erro.textContent = error.message;
            } finally {
                botao.disabled = false;
            }

        });

}


document.addEventListener(
    "DOMContentLoaded",
    () => {
        if (!window.location.pathname.endsWith("login.html")) {
            inicializarDashboard();
        }
    }
);
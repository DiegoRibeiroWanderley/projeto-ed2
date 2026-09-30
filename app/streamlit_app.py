"""Interface Streamlit (Fase 3): produtos com imagem e visualização das estruturas (F6).

Uso: streamlit run app/streamlit_app.py [-- pasta_do_dataset]
(ou defina ACERVO_DATASET; padrão: raiz do projeto)

O Streamlit reexecuta este script a cada interação; por isso o catálogo
fica em st.session_state (montado uma vez por sessão) e toda operação que
altera estruturas (abrir produto) roda em callbacks de botão, nunca no
corpo do script — senão cada rerun afunilaria a splay e contaria um acesso.
"""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import streamlit as st  # noqa: E402

from app import simulacao as sim  # noqa: E402
from app import visualizacao as viz  # noqa: E402
from dados.catalogo import Catalogo  # noqa: E402

POR_PAGINA = 20
COLUNAS = 5
PAGINAS = ["Buscar", "Linha do tempo", "Marcas", "Mais populares", "Produto", "Estruturas",
           "Simulação e métricas"]

st.set_page_config(page_title="Acervo de Moda — ED2", layout="wide")
ss = st.session_state


# ------------------------------------------------------------------ estado
def pasta_dataset():
    if len(sys.argv) > 1 and sys.argv[0].endswith("streamlit_app.py"):
        return sys.argv[1]
    return os.environ.get("ACERVO_DATASET", RAIZ)


if "cat" not in ss:
    pasta = pasta_dataset()
    if not os.path.exists(os.path.join(pasta, "styles.csv")):
        st.error(f"Dataset não encontrado: não existe `styles.csv` em `{pasta}`.\n\n"
                 "Baixe o *Fashion Product Images (Small)* do Kaggle e descompacte na raiz do "
                 "projeto (ficam `styles.csv` e `images/` lado a lado), ou passe a pasta com "
                 "`streamlit run app/streamlit_app.py -- <pasta>`. Passo a passo em `instrucoes.md`.")
        st.stop()
    with st.spinner("Carregando dataset e montando estruturas..."):
        ss.cat = Catalogo.do_dataset(pasta)
    ss.ultimo = None
    ss.pagina = "Buscar"
    ss.pag_tempo = 0
    ss.pag_marca = 0
cat = ss.cat


def abrir(pid):
    """Callback: abre o produto e guarda o que for preciso para desenhar o acesso."""
    caminho = viz.caminho_splay(cat.splay, pid)
    dot_antes = viz.dot_caminho(cat.splay, caminho)
    pos_antes = cat.ranking.posicao(pid)
    ms, ma, mk = cat.splay.metricas, cat.avl.metricas, cat.skip.metricas
    c0, r0, ca0, ck0 = ms.comparacoes, ms.rotacoes, ma.comparacoes, mk.comparacoes
    produto = cat.abrir(pid)
    no_skip = viz.no_skip(cat.skip, (produto.ano, produto.id)) if produto and produto.ano else None
    ss.ultimo = {
        "id": pid,
        "produto": produto,
        "achou": produto is not None,
        "caminho": caminho,
        "dot_antes": dot_antes,
        "rotacoes": list(cat.splay.ultimas_rotacoes),
        "comparacoes": ms.comparacoes - c0,
        "n_rotacoes": ms.rotacoes - r0,
        "comparacoes_avl": ma.comparacoes - ca0,
        "prof_avl": ma.profundidades[-1] if ma.profundidades else None,
        "rank": (pos_antes if pos_antes >= 0 else None, cat.ranking.posicao(pid)),
        # M1
        "m1": cat.splay.limiar if cat.splay.m1_ligada else None,
        "afunilou": cat.splay.ultimo_afunilou,
        "contador": cat.splay.ultimo_contador,
        # skip list / M3
        "m3": cat.skip.popularidade,
        "skip_comparacoes": mk.comparacoes - ck0 if no_skip else None,
        "skip_nivel": no_skip.nivel if no_skip else None,
        "skip_acessos": no_skip.acessos if no_skip else None,
        "promocao": cat.skip.ultima_promocao if no_skip else None,
    }
    ss.pagina = "Produto"


# ------------------------------------------------------------- componentes
def imagem(p, largura):
    if p.imagem:
        st.image(p.imagem, width=largura)
    else:
        st.markdown(f"<div style='width:{largura}px;height:{int(largura * 4 / 3)}px;"
                    "background:#eee;color:#999;display:flex;align-items:center;"
                    "justify-content:center;font-size:12px'>sem imagem</div>",
                    unsafe_allow_html=True)


def grade(produtos, prefixo):
    """Cartões com imagem, nome e botão para abrir o produto."""
    if not produtos:
        st.info("Nenhum produto encontrado.")
        return
    for ini in range(0, len(produtos), COLUNAS):
        colunas = st.columns(COLUNAS)
        for col, p in zip(colunas, produtos[ini:ini + COLUNAS]):
            with col:
                imagem(p, 90)
                st.caption(f"**{p.marca}** · {p.ano or '—'}  \n{p.nome}")
                st.button("Abrir", key=f"{prefixo}-{p.id}", on_click=abrir, args=(p.id,))


def paginador(chave, total):
    paginas = max(1, -(-total // POR_PAGINA))
    ss[chave] = min(ss[chave], paginas - 1)
    a, b, c = st.columns([1, 2, 1])
    if a.button("◀ anterior", key=f"{chave}-ant", disabled=ss[chave] == 0):
        ss[chave] -= 1
        st.rerun()
    b.markdown(f"<div style='text-align:center'>página {ss[chave] + 1} de {paginas} "
               f"· {total} produtos</div>", unsafe_allow_html=True)
    if c.button("próxima ▶", key=f"{chave}-prox", disabled=ss[chave] >= paginas - 1):
        ss[chave] += 1
        st.rerun()
    return ss[chave]


def busca_skip_desenhada(chave_alvo):
    """Desenha e narra a busca por chave_alvo na skip list (sem alterar métricas).

    Uma coluna por nó que a busca tocou; os trechos pulados viram "⋯ N nós".
    """
    html, passos = viz.html_busca_skip(cat.skip, chave_alvo)
    avancos = sum(1 for p in passos if p[0] == "avança")
    achou = passos and passos[-1][0] == "achou"
    st.write(f"Busca por {chave_alvo}: {len(passos)} passos — avançou por {avancos} nós "
             f"(amarelo), desceu {sum(1 for p in passos if p[0] == 'desce')} vezes "
             f"{'e achou a chave (vermelho)' if achou else 'e parou no nível 0 (a chave não existe)'}. "
             "Os números nas células são a ordem dos passos; ✕ = nó comparado que era maior, "
             "por isso a busca desceu. As colunas cinza resumem os nós que a busca pulou.")
    st.markdown(html, unsafe_allow_html=True)
    with st.expander("Passo a passo"):
        st.markdown("\n".join(f"- {linha}" for linha in viz.narrar_busca_skip(passos, chave_alvo)))


# ------------------------------------------------------------------ páginas
def pagina_buscar():
    st.header("Buscar produto")
    st.caption("Busca por nome: tabela ordenada de (nome normalizado, id) com busca binária "
               "pelo prefixo. O produto escolhido é aberto pela splay tree (chave = id).")
    prefixo = st.text_input("Início do nome", placeholder="ex.: puma men black")
    if prefixo.strip():
        grade(cat.buscar_nome(prefixo, limite=POR_PAGINA), "nome")
    st.divider()
    col, _ = st.columns([1, 3])
    pid = col.number_input("Ou abra direto pelo id", min_value=0, step=1, value=15970)
    col.button("Abrir id", on_click=abrir, args=(int(pid),))


def pagina_linha_do_tempo():
    st.header("Linha do tempo")
    st.caption("Skip list com chave (ano, id): o filtro desce pelos níveis até o início do "
               "intervalo e depois percorre a base em ordem, página a página.")
    ini, fim = st.select_slider("Intervalo de anos", options=cat.anos,
                                value=(cat.anos[0], cat.anos[-1]))
    if ss.get("faixa") != (ini, fim):
        ss.faixa, ss.pag_tempo = (ini, fim), 0
    total = cat.total_no_intervalo(ini, fim)
    pagina = paginador("pag_tempo", total)
    grade(cat.linha_do_tempo(ini, fim, pagina, POR_PAGINA), "tempo")
    with st.expander("Como a skip list encontrou o início do intervalo"):
        busca_skip_desenhada((ini,))


def pagina_marcas():
    st.header("Marcas")
    st.caption("Tabela ordenada de marcas (busca binária por prefixo); cada marca aponta para "
               "uma lista encadeada com seus produtos.")
    prefixo = st.text_input("Prefixo da marca", placeholder="ex.: nike")
    marcas = cat.buscar_marcas(prefixo, limite=200) if prefixo.strip() else cat.listar_marcas(0, len(cat.marcas))
    if not marcas:
        st.info("Nenhuma marca com esse prefixo.")
        return
    rotulos = [f"{m} ({n})" for m, n in marcas]
    escolha = st.selectbox(f"{len(marcas)} marcas", range(len(marcas)), format_func=lambda i: rotulos[i])
    marca = marcas[escolha][0]
    if ss.get("marca_atual") != marca:
        ss.marca_atual, ss.pag_marca = marca, 0
    produtos = cat.produtos_da_marca(marca)
    pagina = paginador("pag_marca", len(produtos))
    grade(produtos[pagina * POR_PAGINA:(pagina + 1) * POR_PAGINA], "marca")


def desenho_ranking(n=12):
    itens = [(chave, p.nome, acessos) for chave, p, acessos in cat.ranking.primeiros(n)]
    ult = ss.ultimo
    destaque = ult["id"] if ult and ult["achou"] else None
    mov = ult["rank"] if ult and ult["achou"] else None
    st.graphviz_chart(viz.dot_ranking(itens, destaque, mov))


def pagina_populares():
    st.header("Mais populares")
    st.caption("Lista com transposição: o 1º acesso insere no fim e cada novo acesso troca o "
               "produto com o anterior. O ranking é aproximado — não ordena pela contagem, "
               "mostrada só para comparação.")
    top = cat.mais_populares(POR_PAGINA)
    if not top:
        st.info("Nenhum produto visualizado ainda. Abra alguns produtos nas outras páginas.")
        return
    desenho_ranking()
    grade([p for p, _ in top], "pop")


def pagina_produto():
    ult = ss.ultimo
    if ult is None:
        st.info("Nenhum produto aberto ainda.")
        return
    if not ult["achou"]:
        st.warning(f"Produto {ult['id']} não existe. A splay afunilou o último nó visitado.")
    else:
        p = ult["produto"]
        st.header(p.nome)
        a, b = st.columns([1, 3])
        with a:
            imagem(p, 200)
        with b:
            st.markdown(
                f"**Marca:** {p.marca}  \n**Ano:** {p.ano or '—'}  \n**Gênero:** {p.genero}  \n"
                f"**Categoria:** {p.categoria} › {p.subcategoria} › {p.tipo}  \n"
                f"**Cor:** {p.cor or '—'} · **Estação:** {p.estacao or '—'} · **Uso:** {p.uso or '—'}  \n"
                f"**id:** {p.id}")
            antes, depois = ult["rank"]
            txt = "entrou no fim do ranking" if antes is None else (
                "já estava no topo" if antes == depois else f"subiu da {antes + 1}ª para a {depois + 1}ª posição")
            st.markdown(f"**Ranking:** {txt} (lista com transposição)")

    st.subheader("O que a splay tree fez neste acesso")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Profundidade antes", len(ult["caminho"]) - 1)
    m2.metric("Comparações (splay)", ult["comparacoes"])
    m3.metric("Rotações", ult["n_rotacoes"])
    m4.metric("Comparações (AVL)", ult["comparacoes_avl"],
              help=f"A mesma busca na AVL chegou à profundidade {ult['prof_avl']}.")
    if ult["m1"] and ult["achou"] and not ult["afunilou"]:
        st.info(f"**M1 ligada (k = {ult['m1']}):** contador do nó = {ult['contador']}/{ult['m1']}. "
                f"Ainda não atingiu o limiar, então a busca foi uma busca comum de BST e a árvore "
                f"não mudou. Abra de novo mais {ult['m1'] - ult['contador']} vez(es) para afunilar.")
    elif ult["m1"] and ult["afunilou"]:
        st.success(f"**M1 ligada (k = {ult['m1']}):** o contador atingiu o limiar, o nó foi "
                   "afunilado e o contador voltou a 0.")
    elif ult["m1"] and not ult["achou"]:
        st.info("**M1 ligada:** busca sem sucesso não afunila.")
    st.markdown(f"**Passos do splay:** {viz.resumo_rotacoes(ult['rotacoes'])}")
    a, b = st.columns(2)
    with a:
        st.markdown("**Antes — caminho da busca** (vermelho = alvo, triângulos = subárvores não visitadas)")
        st.graphviz_chart(ult["dot_antes"])
    with b:
        if ult["afunilou"]:
            st.markdown("**Depois — topo da árvore** (o nó acessado virou a raiz)")
        else:
            st.markdown("**Depois — topo da árvore** (inalterado: não houve splay)")
        st.graphviz_chart(viz.dot_topo_arvore(cat.splay.raiz, 4, ult["caminho"], ult["id"]))

    if ult["skip_nivel"] is not None:
        st.subheader("Skip list neste acesso")
        m1_, m2_, m3_ = st.columns(3)
        m1_.metric("Comparações", ult["skip_comparacoes"])
        m2_.metric("Nível do nó", ult["skip_nivel"])
        m3_.metric("Acessos registrados", ult["skip_acessos"])
        if ult["promocao"]:
            antes, depois = ult["promocao"]
            st.success(f"**M3:** o produto foi promovido do nível {antes} para o {depois} "
                       "pela popularidade; as próximas buscas por ele param mais cedo.")
        elif ult["m3"]:
            st.caption("M3 ligada: nível atual já é ≥ 1 + ⌊log₂(1 + acessos)⌋; sem promoção.")
        else:
            st.caption("M3 desligada: o nível foi sorteado na inserção e não muda.")


def pagina_estruturas():
    st.header("Estado das estruturas")
    aba_splay, aba_skip, aba_rank, aba_tab = st.tabs(
        ["Splay tree", "Skip list", "Lista com transposição", "Tabelas ordenadas"])
    ult = ss.ultimo

    with aba_splay:
        niveis = st.slider("Níveis desenhados", 2, 6, 4)
        st.caption(f"{len(cat.splay)} nós · altura {cat.splay.altura()} · desenhados até "
                   f"{2 ** niveis - 1} nós. Em amarelo, o caminho do último acesso.")
        st.graphviz_chart(viz.dot_topo_arvore(cat.splay.raiz, niveis,
                                              ult["caminho"] if ult else (),
                                              ult["id"] if ult else None))

    with aba_skip:
        tam = cat.skip.tamanho_niveis()
        st.caption(f"{len(cat.skip)} nós · {cat.skip.nivel} níveis · promoções por M3: "
                   f"{cat.skip.promocoes} · nós por nível: "
                   + ", ".join(f"n{i}={n}" for i, n in enumerate(tam)))
        st.bar_chart({"nós": tam}, x_label="nível", y_label="nós")
        a, b = st.columns(2)
        ano = a.selectbox("Ano", cat.anos, index=cat.anos.index(2011) if 2011 in cat.anos else 0)
        pid = b.number_input("id (desempate)", min_value=0, step=1, value=1557)
        busca_skip_desenhada((ano, int(pid)))

    with aba_rank:
        if len(cat.ranking) == 0:
            st.info("Nenhum produto visualizado ainda.")
        else:
            st.caption(f"{len(cat.ranking)} produtos já visualizados; primeiros 12 desenhados.")
            desenho_ranking()

    with aba_tab:
        st.caption(f"Marcas: {len(cat.marcas)} entradas · Nomes: {len(cat.nomes)} entradas "
                   "(chave = (nome normalizado, id), pois há nomes repetidos).")
        a, b = st.columns(2)
        a.dataframe([{"marca": m, "produtos": n} for m, n in cat.listar_marcas(0, 30)],
                    hide_index=True)
        b.dataframe([{"nome": k[0], "id": k[1]} for k, _ in cat.nomes.fatia(0, 30)],
                    hide_index=True)


def parametros_simulacao():
    a, b, c = st.columns(3)
    n = a.number_input("Acessos", 1000, 100000, 20000, step=1000, key="sim_n")
    pop = b.number_input("Produtos populares", 10, 5000, 500, step=50, key="sim_pop")
    s = c.slider("Concentração (expoente Zipf)", 0.5, 2.0, 1.0, 0.1, key="sim_s")
    a, b, c = st.columns(3)
    ruido = a.slider("Visitas isoladas", 0.0, 0.9, 0.2, 0.05, key="sim_ruido",
                     help="Fração de acessos a um produto qualquer, fora dos populares.")
    mudanca = b.checkbox("Trocar os populares na metade", True, key="sim_mudanca")
    semente = c.number_input("Semente", 0, 9999, 0, key="sim_semente")
    return dict(n_acessos=int(n), n_populares=int(pop), s=s, ruido=ruido, mudanca=mudanca,
                semente=int(semente))


def aplicar_ao_catalogo(n):
    """Callback (F7): aplica os primeiros n acessos simulados ao catálogo da sessão."""
    seq = sim.gerar_sequencia(ss.produtos, **ss.sim_params)
    for p in seq[:n]:
        cat.abrir(p.id)
    ss.aplicados = n


def grafico_linhas(series, atributo, rotulo_y):
    dados = {"acesso": []}
    for s in series:
        valores = sim.media_por_bloco(getattr(s, atributo), 50)
        if not dados["acesso"]:
            passo = len(getattr(s, atributo)) / len(valores)
            dados["acesso"] = [int(i * passo) for i in range(len(valores))]
        dados[s.nome] = valores
    st.line_chart(dados, x="acesso", y=[s.nome for s in series], x_label="acessos",
                  y_label=rotulo_y)


def pagina_simulacao():
    st.header("Simulação e métricas")
    st.caption("F7: gera acessos concentrados em poucos produtos (Zipf) com visitas isoladas "
               "e aplica a mesma sequência a estruturas novas — clássicas e modificadas — "
               "montadas com a mesma ordem de inserção (I1–I4).")
    if "produtos" not in ss:
        ss.produtos = [p for _, p in cat.splay]
    params = parametros_simulacao()
    k = ss.get("m1_k", 3)
    if st.button(f"Rodar simulação (M1 com k = {k})", type="primary"):
        with st.spinner("Montando estruturas e simulando..."):
            seq = sim.gerar_sequencia(ss.produtos, **params)
            ss.sim = sim.simular(ss.produtos, seq, k=k)
            ss.sim_params = params

    r = ss.get("sim")
    if r is not None:
        st.subheader("Resumo (I1, I3)")
        st.dataframe(r.tabela(), hide_index=True)
        niv = {n: sum(v) / len(v) for n, v in r.niveis_populares.items()}
        st.markdown(
            f"- **M3:** {r.promocoes} promoções; nível médio dos 50 mais acessados: "
            + ", ".join(f"{n} **{m:.1f}**" for n, m in niv.items()) + ".\n"
            f"- **Ranking:** {r.ranking['precisao']:.0%} do top-10 real aparece no top-10 da lista "
            f"com transposição ({r.ranking['tamanho']} produtos distintos visualizados). "
            "A transposição sobe um passo por acesso, então converge devagar.")
        st.subheader("Profundidade do acesso ao longo do tempo (I2)")
        grafico_linhas(r.arvores, "profundidade", "profundidade média")
        a, b = st.columns(2)
        with a:
            st.markdown("**Rotações por acesso: splay clássica × M1**")
            grafico_linhas(r.arvores[:2], "rotacoes", "rotações")
        with b:
            st.markdown("**Comparações por busca: skip list clássica × M3**")
            grafico_linhas(r.skips, "comparacoes", "comparações")
        st.markdown("**Custo da busca sequencial no ranking**")
        grafico_linhas(r.ranking["series"], "comparacoes", "comparações")

        st.divider()
        st.subheader("Demonstração ao vivo")
        st.caption("Aplica acessos da mesma sequência ao catálogo desta sessão (com as "
                   "modificações ligadas na barra lateral). Depois veja as páginas Estruturas "
                   "e Mais populares.")
        n = st.slider("Acessos a aplicar", 10, min(5000, r.n_acessos), 500, step=10)
        st.button(f"Aplicar {n} acessos ao catálogo", on_click=aplicar_ao_catalogo, args=(n,))
        if ss.get("aplicados"):
            st.success(f"{ss.aplicados} acessos aplicados. Raiz da splay: {cat.splay.raiz.chave}.")

    st.divider()
    st.subheader("Métricas desta sessão (I1)")
    st.caption("Contadores acumulados pelo uso do catálogo desde a carga.")
    linhas = []
    for nome, e in [("Splay", cat.splay), ("AVL", cat.avl), ("Skip list", cat.skip),
                    ("Lista com transposição", cat.ranking), ("Tabela de marcas", cat.marcas),
                    ("Tabela de nomes", cat.nomes)]:
        m = e.metricas
        prof = m.profundidades
        linhas.append({"estrutura": nome, "operações": m.operacoes, "comparações": m.comparacoes,
                       "comparações/op": round(m.media_comparacoes(), 2), "rotações": m.rotacoes,
                       "profundidade média": round(sum(prof) / len(prof), 2) if prof else None})
    st.dataframe(linhas, hide_index=True)
    prof = cat.splay.metricas.profundidades
    if len(prof) >= 2:
        st.markdown("**Profundidade dos acessos na splay desta sessão (I2)**")
        st.line_chart({"acesso": list(range(1, len(prof) + 1)), "profundidade": prof},
                      x="acesso", y="profundidade")


# --------------------------------------------------------------- navegação
with st.sidebar:
    st.title("Acervo de Moda")
    st.radio("Página", PAGINAS, key="pagina")
    st.divider()
    st.markdown("**Modificações** (seção 5)")
    m1 = st.toggle("M1 · splay com limiar", key="m1",
                   help="Só afunila um nó depois de k acessos a ele.")
    k = st.slider("k (acessos para afunilar)", 2, 10, 3, key="m1_k", disabled=not m1)
    m3 = st.toggle("M3 · skip list por popularidade", key="m3",
                   help="Produtos mais acessados sobem de nível na skip list.")
    cat.configurar(k if m1 else None, m3)
    st.divider()
    st.caption(f"{len(cat)} produtos · {len(cat.marcas)} marcas · estruturas montadas em "
               f"{cat.tempo_montagem:.1f}s")
    with st.expander("Relatório da carga"):
        st.text(cat.relatorio.texto())

{
    "Buscar": pagina_buscar,
    "Linha do tempo": pagina_linha_do_tempo,
    "Marcas": pagina_marcas,
    "Mais populares": pagina_populares,
    "Produto": pagina_produto,
    "Estruturas": pagina_estruturas,
    "Simulação e métricas": pagina_simulacao,
}[ss.pagina]()

"""Desenho do estado das estruturas (F6).

Gera DOT (renderizado pelo st.graphviz_chart) e HTML. Tudo aqui é somente
leitura: percorre os nós diretamente, sem afunilar a splay nem alterar as
métricas. Desenha subconjuntos legíveis (N4): o topo da árvore, o caminho
de uma busca, uma janela da skip list, os primeiros do ranking.
"""

import html

COR_CAMINHO = "#f6c85f"
COR_ALVO = "#e8684a"
COR_NO = "#dbe7f5"
COR_BORDA = "#5b7fa6"


def _esc(texto):
    return str(texto).replace("\\", "\\\\").replace('"', '\\"')


def _cabecalho(nome, rankdir="TB"):
    return [
        f'digraph "{nome}" {{',
        f"  rankdir={rankdir}; bgcolor=transparent; nodesep=0.25; ranksep=0.35;",
        f'  node [shape=circle, style=filled, fillcolor="{COR_NO}", color="{COR_BORDA}", '
        'fontname="Helvetica", fontsize=10, width=0.55, fixedsize=true];',
        '  edge [arrowhead=none, color="#8899aa"];',
    ]


# ----------------------------------------------------------------- splay
def caminho_splay(arvore, chave):
    """Chaves visitadas da raiz até chave (ou até onde a busca pararia), sem afunilar."""
    caminho, no = [], arvore.raiz
    while no is not None:
        caminho.append(no.chave)
        if chave == no.chave:
            break
        no = no.esq if chave < no.chave else no.dir
    return caminho


def no_splay(arvore, chave):
    """O nó com a chave (ou None), sem afunilar nem contar métricas."""
    no = arvore.raiz
    while no is not None and no.chave != chave:
        no = no.esq if chave < no.chave else no.dir
    return no


def _cor(chave, caminho, alvo):
    if chave == alvo:
        return COR_ALVO
    if chave in caminho:
        return COR_CAMINHO
    return COR_NO


def dot_topo_arvore(raiz, niveis=4, caminho=(), alvo=None, nome="splay"):
    """Os primeiros `niveis` níveis da árvore (até 2^niveis - 1 nós).

    Subárvores cortadas aparecem como um triângulo "…"; filhos ausentes
    viram nós invisíveis para preservar a posição esquerda/direita.
    """
    linhas = _cabecalho(nome) + ["  ordering=out;"]
    if raiz is None:
        linhas.append('  vazio [label="(vazia)", shape=plaintext];')
        return "\n".join(linhas + ["}"])
    caminho = set(caminho)
    fila, i, extra = [(raiz, 0)], 0, 0
    while i < len(fila):
        no, prof = fila[i]
        i += 1
        linhas.append(f'  n{no.chave} [label="{no.chave}", fillcolor="{_cor(no.chave, caminho, alvo)}"];')
        for filho in (no.esq, no.dir):
            extra += 1
            if filho is None:
                linhas.append(f"  x{extra} [style=invis, label=\"\"]; n{no.chave} -> x{extra} [style=invis];")
            elif prof + 1 < niveis:
                fila.append((filho, prof + 1))
                linhas.append(f"  n{no.chave} -> n{filho.chave};")
            else:
                cor = COR_CAMINHO if filho.chave in caminho or filho.chave == alvo else "#eeeeee"
                linhas.append(f'  t{extra} [label="…", shape=triangle, width=0.4, fillcolor="{cor}"]; '
                              f"n{no.chave} -> t{extra};")
    return "\n".join(linhas + ["}"])


def dot_caminho(arvore, caminho, max_nos=24):
    """Desenha só o caminho de uma busca, com o irmão de cada nó como subárvore "…".

    Caminhos longos são truncados no meio para caber na tela.
    """
    linhas = _cabecalho("caminho")
    if not caminho:
        return "\n".join(linhas + ["}"])
    # recupera os nós do caminho descendo pela árvore atual (antes do splay)
    nos, no = [], arvore.raiz
    for chave in caminho:
        if no is None or no.chave != chave:
            break
        nos.append(no)
        if len(nos) < len(caminho):
            no = no.esq if caminho[len(nos)] < no.chave else no.dir
    linhas.append("  ordering=out;")  # filhos desenhados na ordem das arestas
    alvo = caminho[-1]
    metade = max_nos // 2
    truncar = len(nos) > max_nos

    def oculto(k):
        return truncar and metade <= k < len(nos) - metade

    def ident(k):
        return "pulo" if oculto(k) else f"n{nos[k].chave}"

    if truncar:
        linhas.append(f'  pulo [label="… {len(nos) - 2 * metade} nós …", shape=box, '
                      'style=dashed, fixedsize=false, fillcolor=white];')
        linhas.append(f"  pulo -> n{nos[len(nos) - metade].chave} [style=dashed];")
    for k, no in enumerate(nos):
        if oculto(k):
            continue
        cor = COR_ALVO if no.chave == alvo else COR_CAMINHO
        linhas.append(f'  n{no.chave} [label="{no.chave}", fillcolor="{cor}"];')
        if k + 1 == len(nos):
            continue
        seguiu_esq = nos[k + 1] is no.esq
        estilo = " [style=dashed]" if oculto(k + 1) else ""
        seguido = f"  n{no.chave} -> {ident(k + 1)}{estilo};"
        # o filho não seguido pela busca aparece como subárvore resumida
        irmao = no.dir if seguiu_esq else no.esq
        if irmao is None:
            outro = f'  v{no.chave} [style=invis, label=""]; n{no.chave} -> v{no.chave} [style=invis];'
        else:
            outro = (f'  s{no.chave} [label="{irmao.chave}\\n…", shape=triangle, width=0.55, '
                     f'fillcolor="#eeeeee", fontsize=8]; n{no.chave} -> s{no.chave} [style=dotted];')
        linhas.extend([seguido, outro] if seguiu_esq else [outro, seguido])
    return "\n".join(linhas + ["}"])


def resumo_rotacoes(rotacoes):
    """[('zig-zag', 5), ('zig-zig', 5), ...] -> 'zig-zag ×2, zig-zig ×1' (em ordem)."""
    if not rotacoes:
        return "nenhuma (o nó já estava na raiz)"
    partes, atual, n = [], rotacoes[0][0], 0
    for tipo, _ in rotacoes:
        if tipo == atual:
            n += 1
        else:
            partes.append(f"{atual} ×{n}")
            atual, n = tipo, 1
    partes.append(f"{atual} ×{n}")
    return " → ".join(partes)


# ------------------------------------------------------------- skip list
def rastro_skip(skip, chave):
    """Todos os passos da busca por chave, sem contar métricas.

    Mesma regra de SkipList.buscar (para no nível em que acha a chave).
    Cada passo é (ação, nível, de, para), com de/para = chave do nó ou None
    para a cabeça (em `de`) ou o fim da lista (em `para`):
    - "avança": para < chave, a busca anda até ele;
    - "desce": para >= chave (ou fim), a busca desce um nível a partir de `de`;
    - "achou": para == chave.
    """
    passos, no = [], skip.cabeca
    for i in range(skip.nivel - 1, -1, -1):
        while True:
            seguinte = no.prox[i]
            if seguinte is None:
                passos.append(("desce", i, no.chave, None))
                break
            if seguinte.chave < chave:
                passos.append(("avança", i, no.chave, seguinte.chave))
                no = seguinte
                continue
            if seguinte.chave == chave:
                passos.append(("achou", i, no.chave, seguinte.chave))
                return passos
            passos.append(("desce", i, no.chave, seguinte.chave))
            break
    return passos


def caminho_skip(skip, chave):
    """(nível, chave) dos nós visitados (onde a busca avançou), como em ultimo_caminho."""
    return [(i, para) for acao, i, _, para in rastro_skip(skip, chave) if acao == "avança"]


def no_skip(skip, chave):
    """O nó com a chave (ou None), sem contar métricas."""
    no = skip.cabeca
    for i in range(skip.nivel - 1, -1, -1):
        while no.prox[i] is not None and no.prox[i].chave < chave:
            no = no.prox[i]
        if no.prox[i] is not None and no.prox[i].chave == chave:
            return no.prox[i]
    return None


def _nos_da_base_ate(skip, chaves):
    """Percorre a base uma vez e devolve, para cada chave (em ordem), (nó, nós pulados antes).

    "Pulados" = nós da base entre a coluna anterior e esta, que a busca não tocou.
    """
    saida, no, pulados, k = [], skip.cabeca.prox[0], 0, 0
    while no is not None and k < len(chaves):
        if no.chave == chaves[k]:
            saida.append((no, pulados))
            pulados, k = 0, k + 1
        else:
            pulados += 1
        no = no.prox[0]
    return saida


CSS_SKIP = (
    "<style>.sk{border-collapse:collapse;font:11px Helvetica,sans-serif}"
    ".sk td{border:1px solid #ccd;padding:2px 5px;text-align:center;min-width:46px;height:18px}"
    ".sk .v{background:#dbe7f5;color:#8aa}"            # nó existe neste nível
    ".sk .p{background:#f6c85f;font-weight:bold}"       # a busca avançou até ele
    ".sk .x{background:#f4d6d0;color:#a33}"             # comparado: maior, desceu
    ".sk .a{background:#e8684a;color:white;font-weight:bold}"  # achou
    ".sk .h{background:#5b7fa6;color:white}"            # cabeça
    ".sk .hp{background:#3d5f86;color:#f6c85f;font-weight:bold}"
    ".sk .e{color:#ddd;border-color:#f0f0f4}"           # sem ponteiro neste nível
    ".sk .g{background:#fafafa;color:#999;border-style:dashed;min-width:40px}"
    ".sk th{font-weight:normal;color:#667;padding:2px 4px;white-space:nowrap}"
    ".sk .k td{height:auto}</style>")


def html_busca_skip(skip, chave):
    """Desenha a busca por chave: uma coluna por nó tocado, com os trechos pulados resumidos.

    Linhas = níveis (topo em cima). Em cada célula:
    - amarelo "n": no passo n a busca avançou até este nó neste nível;
    - rosa "✕n": no passo n este nó foi comparado, era maior que a chave, e a busca desceu;
    - vermelho "✓n": achou a chave no passo n;
    - "↓" marca de onde a busca desceu; azul-claro: o nó tem ponteiro aqui, mas não foi tocado.
    Devolve (html, passos).
    """
    from estruturas.tabela_ordenada import merge_sort

    passos = rastro_skip(skip, chave)
    marcas = {}  # (nível, chave ou "cabeça") -> (classe, texto)
    for n, (acao, i, de, para) in enumerate(passos, 1):
        origem = "cabeça" if de is None else de
        if acao == "avança":
            marcas[(i, para)] = ("p", str(n))
        elif acao == "achou":
            marcas[(i, para)] = ("a", f"✓{n}")
        else:
            classe, texto = marcas.get((i, origem), ("hp" if de is None else "p", ""))
            marcas[(i, origem)] = (classe, (texto + " ↓").strip())
            if para is not None:
                marcas[(i, para)] = ("x", f"✕{n}")

    tocadas = []
    for _, _, _, para in passos:
        if para is not None and para not in tocadas:
            tocadas.append(para)
    ordenadas = [k for k, _ in merge_sort([(k, None) for k in tocadas])]
    colunas = _nos_da_base_ate(skip, ordenadas)
    total_linhas = skip.nivel + 1

    linhas = [CSS_SKIP, '<div style="overflow-x:auto"><table class="sk">']
    for linha, i in enumerate(range(skip.nivel - 1, -1, -1)):
        classe, texto = marcas.get((i, "cabeça"), ("h", ""))
        cel = [f"<th>nível {i}</th>", f'<td class="{classe}">{texto}</td>']
        for no, pulados in colunas:
            if pulados and linha == 0:
                cel.append(f'<td class="g" rowspan="{total_linhas}">⋯<br>{pulados}<br>nós</td>')
            if no.nivel > i:
                classe, texto = marcas.get((i, no.chave), ("v", "→"))
                cel.append(f'<td class="{classe}">{texto}</td>')
            else:
                cel.append('<td class="e"></td>')
        linhas.append("<tr>" + "".join(cel) + "</tr>")
    rodape = ["<th>chave</th>", '<td class="h">cabeça</td>']
    for no, _ in colunas:
        ano, pid = no.chave
        rodape.append(f"<td><b>{ano}</b><br>{pid}</td>")
    linhas.append('<tr class="k">' + "".join(rodape) + "</tr></table></div>")
    return "".join(linhas), passos


def narrar_busca_skip(passos, chave):
    """Texto passo a passo da busca (uma linha por passo)."""
    def nome(k):
        return "a cabeça" if k is None else str(k)

    saida = []
    for n, (acao, i, de, para) in enumerate(passos, 1):
        if acao == "avança":
            saida.append(f"{n}. nível {i}: o próximo de {nome(de)} é {para} < {chave} → avança")
        elif acao == "achou":
            saida.append(f"{n}. nível {i}: o próximo de {nome(de)} é {para} = chave → **achou**")
        elif i == 0:
            fim = "não há ninguém depois" if para is None else f"o próximo é {para} > {chave}"
            saida.append(f"{n}. nível 0: depois de {nome(de)}, {fim} → a chave não está na "
                         "lista; este é o ponto de parada (onde um intervalo começaria)")
        elif para is None:
            saida.append(f"{n}. nível {i}: depois de {nome(de)} não há ninguém → desce")
        else:
            saida.append(f"{n}. nível {i}: o próximo de {nome(de)} é {para} > {chave} → desce")
    return saida


# --------------------------------------------------------------- ranking
def dot_ranking(itens, destaque=None, movimento=None):
    """Lista encadeada do ranking, da esquerda (topo) para a direita.

    itens: [(chave, rótulo, acessos)]; destaque: chave do último acesso;
    movimento: (posição antes, posição depois) do item destacado.
    """
    linhas = _cabecalho("ranking", rankdir="LR")
    linhas.append('  node [shape=box, fixedsize=false, width=0, style="filled,rounded"];')
    linhas.append('  edge [arrowhead=normal];')
    linhas.append('  ini [label="início", shape=plaintext, style=""];')
    anterior = "ini"
    for pos, (chave, rotulo, acessos) in enumerate(itens):
        cor = COR_ALVO if chave == destaque else COR_NO
        texto = f"{pos + 1}º  [{chave}]\\n{_esc(rotulo[:22])}\\n{acessos} acesso{'s' if acessos != 1 else ''}"
        linhas.append(f'  r{pos} [label="{texto}", fillcolor="{cor}"];')
        linhas.append(f"  {anterior} -> r{pos};")
        anterior = f"r{pos}"
    if movimento is not None and destaque is not None:
        antes, depois = movimento
        if antes is not None and antes != depois and antes < len(itens):
            linhas.append(f'  r{antes} -> r{depois} [style=dashed, color="{COR_ALVO}", '
                          'constraint=false, label="transposição", fontsize=9];')
    return "\n".join(linhas + ["}"])


def escapar(texto):
    return html.escape(str(texto))

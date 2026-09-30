"""Modo de simulação (F7) e métricas comparativas (I1–I3).

Gera uma sequência de acessos com poucos produtos populares (Zipf), mais
uma fração de visitas isoladas ("ruído"), e opcionalmente troca o conjunto
de populares no meio (para ver a estrutura se readaptar). A mesma sequência
é aplicada a estruturas novas, montadas com a mesma ordem de inserção:

- splay clássica × splay com M1 × AVL (comparações, profundidade, rotações)
- skip list clássica × skip list com M3 (comparações, promoções, níveis)
- lista com transposição × lista sem autoajuste (custo da busca sequencial
  e qualidade do ranking em relação à contagem real)

Independe da interface: usado pelo Streamlit e por relatorio_metricas.py.
"""

import random
import time

from estruturas.avl import AVLTree
from estruturas.lista_encadeada import ListaEncadeada
from estruturas.lista_transposicao import ListaTransposicao
from estruturas.skiplist import SkipList
from estruturas.splay import SplayTree
from estruturas.tabela_ordenada import merge_sort


# ------------------------------------------------------------- sequência
def gerar_sequencia(produtos, n_acessos=20000, n_populares=500, s=1.0, ruido=0.2,
                    mudanca=False, semente=0):
    """Lista de Produto a acessar, em ordem.

    - n_populares produtos sorteados recebem pesos Zipf 1/(posto+1)^s;
    - cada acesso, com probabilidade `ruido`, vai para um produto qualquer
      (visita isolada);
    - com `mudanca`, a segunda metade usa outro conjunto de populares.
    Só entram produtos com ano, para que todos existam também na skip list.
    """
    rng = random.Random(semente)
    candidatos = [p for p in produtos if p.ano is not None]
    acumulados, total = [], 0.0
    for r in range(n_populares):
        total += 1.0 / (r + 1) ** s
        acumulados.append(total)
    populares = rng.sample(candidatos, n_populares)
    segunda = rng.sample(candidatos, n_populares) if mudanca else populares
    seq = []
    for i in range(n_acessos):
        grupo = segunda if mudanca and i >= n_acessos // 2 else populares
        if rng.random() < ruido:
            seq.append(candidatos[rng.randrange(len(candidatos))])
        else:
            seq.append(rng.choices(grupo, cum_weights=acumulados)[0])
    return seq


# ---------------------------------------------------------------- séries
class Serie:
    """Custos por acesso de uma variante (I1, I2)."""

    def __init__(self, nome):
        self.nome = nome
        self.comparacoes = []
        self.profundidade = []
        self.rotacoes = []
        self.tempo = 0.0

    def media(self, valores):
        return sum(valores) / len(valores) if valores else 0.0

    def resumo(self):
        return {
            "variante": self.nome,
            "comparações/acesso": round(self.media(self.comparacoes), 2),
            "profundidade média": round(self.media(self.profundidade), 2) if self.profundidade else None,
            "rotações/acesso": round(self.media(self.rotacoes), 2) if self.rotacoes else None,
            "tempo (s)": round(self.tempo, 3),
        }


def media_por_bloco(valores, blocos=50):
    """Divide a série em `blocos` partes e devolve a média de cada uma (para gráficos)."""
    if not valores:
        return []
    tam = max(1, len(valores) // blocos)
    return [sum(valores[i:i + tam]) / len(valores[i:i + tam]) for i in range(0, len(valores), tam)]


def _medir_arvore(nome, arvore, seq):
    serie = Serie(nome)
    m = arvore.metricas
    m.zerar()
    inicio = time.perf_counter()
    for p in seq:
        c0, r0 = m.comparacoes, m.rotacoes
        arvore.buscar(p.id)
        serie.comparacoes.append(m.comparacoes - c0)
        serie.rotacoes.append(m.rotacoes - r0)
    serie.tempo = time.perf_counter() - inicio
    serie.profundidade = list(m.profundidades)
    return serie


def _medir_skip(nome, skip, seq):
    serie = Serie(nome)
    m = skip.metricas
    m.zerar()
    inicio = time.perf_counter()
    for p in seq:
        c0 = m.comparacoes
        skip.buscar((p.ano, p.id))
        serie.comparacoes.append(m.comparacoes - c0)
    serie.tempo = time.perf_counter() - inicio
    serie.profundidade = list(m.profundidades)  # nós visitados antes de achar
    serie.rotacoes = []
    return serie


# --------------------------------------------------------------- ranking
def contagem_real(seq, n):
    """Os n produtos mais acessados de fato: [(Produto, acessos)], por contagem decrescente."""
    ids = merge_sort([(p.id, p) for p in seq])
    contagens, i = [], 0
    while i < len(ids):
        j = i
        while j < len(ids) and ids[j][0] == ids[i][0]:
            j += 1
        contagens.append(((-(j - i), ids[i][0]), ids[i][1]))  # negativo: maior primeiro
        i = j
    return [(p, -neg) for (neg, _), p in merge_sort(contagens)[:n]]


def _medir_ranking(seq, n_top=10):
    transp = ListaTransposicao()
    fixa = ListaEncadeada()  # sem autoajuste: ordem do 1º acesso
    s_transp, s_fixa = Serie("Lista com transposição"), Serie("Lista sem autoajuste")
    inicio = time.perf_counter()
    for p in seq:
        c0 = transp.metricas.comparacoes
        transp.acessar(p.id, p)
        s_transp.comparacoes.append(transp.metricas.comparacoes - c0)
    s_transp.tempo = time.perf_counter() - inicio
    inicio = time.perf_counter()
    for p in seq:
        c0 = fixa.metricas.comparacoes
        if fixa.buscar(p.id) is None:
            fixa.inserir_fim(p.id)
        s_fixa.comparacoes.append(fixa.metricas.comparacoes - c0)
    s_fixa.tempo = time.perf_counter() - inicio
    real = contagem_real(seq, n_top)
    top_real = [p.id for p, _ in real]
    top_lista = [c for c, _, _ in transp.primeiros(n_top)]
    acertos = sum(1 for pid in top_lista if pid in top_real)
    return {
        "series": [s_transp, s_fixa],
        "top_real": real,
        "top_lista": [(c, a) for c, _, a in transp.primeiros(n_top)],
        "precisao": acertos / n_top if n_top else 0.0,
        "tamanho": len(transp),
    }


# ------------------------------------------------------------- simulação
class Resultado:
    def __init__(self, arvores, skips, ranking, niveis, niveis_populares, promocoes, n_acessos):
        self.arvores = arvores  # [Serie] splay clássica, splay M1, AVL
        self.skips = skips  # [Serie] skip clássica, skip M3
        self.ranking = ranking
        self.niveis = niveis  # nome -> nós por nível ao final
        self.niveis_populares = niveis_populares  # nome -> nível dos 50 mais acessados
        self.promocoes = promocoes
        self.n_acessos = n_acessos

    def tabela(self):
        return [s.resumo() for s in self.arvores + self.skips + self.ranking["series"]]


def simular(produtos, seq, k=3, semente=0):
    """Aplica seq a estruturas novas: clássicas e modificadas, mesma ordem de inserção."""
    ordem = list(produtos)
    random.Random(semente).shuffle(ordem)  # mesma ordem do Catalogo

    splay, splay_m1, avl = SplayTree(), SplayTree(), AVLTree()
    skip = SkipList(rng=random.Random(semente + 1))
    skip_m3 = SkipList(rng=random.Random(semente + 1), popularidade=True)  # mesmos níveis iniciais
    for p in ordem:
        splay.inserir(p.id, p)
        splay_m1.inserir(p.id, p)
        avl.inserir(p.id, p)
        if p.ano is not None:
            skip.inserir((p.ano, p.id), p)
            skip_m3.inserir((p.ano, p.id), p)
    splay_m1.limiar = k  # M1 só nas buscas (inserção clássica)

    arvores = [
        _medir_arvore("Splay clássica", splay, seq),
        _medir_arvore(f"Splay M1 (k={k})", splay_m1, seq),
        _medir_arvore("AVL", avl, seq),
    ]
    skips = [
        _medir_skip("Skip list clássica", skip, seq),
        _medir_skip("Skip list M3", skip_m3, seq),
    ]
    niveis = {"Skip list clássica": skip.tamanho_niveis(), "Skip list M3": skip_m3.tamanho_niveis()}
    top = [p for p, _ in contagem_real(seq, 50)]
    niveis_populares = {
        "Skip list clássica": [skip.nivel_de((p.ano, p.id)) for p in top],
        "Skip list M3": [skip_m3.nivel_de((p.ano, p.id)) for p in top],
    }
    return Resultado(arvores, skips, _medir_ranking(seq), niveis, niveis_populares,
                     skip_m3.promocoes, len(seq))

import json
import random
import re

import pytest

from app import animacao as anim
from estruturas.skiplist import SkipList
from estruturas.splay import SplayTree


def arvore(chaves):
    a = SplayTree()
    for c in chaves:
        a.inserir(c, c)
    return a


def lista_de_anos():
    sl = SkipList(rng=random.Random(2))
    for i in range(500):
        sl.inserir((2000 + i // 50, i), i)
    return sl


def formato(a):
    """Forma da árvore (chaves em pré-ordem), para ver se algo mudou."""
    saida, pilha = [], [a.raiz]
    while pilha:
        no = pilha.pop()
        if no is not None:
            saida.append(no.chave)
            pilha += [no.dir, no.esq]
    return saida


def ids_do_svg(svg):
    return set(re.findall(r'id="([^"]+)"', svg))


def quadros_da_pagina(pagina):
    return json.loads(re.search(r"const Q = (\[.*?\]);\n", pagina, re.S).group(1))


def conferir_ids(svg, quadros):
    """Toda marca e todo destaque apontam para um elemento que existe no desenho."""
    ids = ids_do_svg(svg)
    for q in quadros:
        for id_, _ in q["marcas"]:
            assert id_ in ids
        for id_ in q["ex"]:
            assert id_ in ids


@pytest.mark.parametrize("chave", [50, 1, 99, 37, 1000, -5, 42])
def test_splay_comparacoes_iguais_a_busca_real_e_sem_afunilar(chave):
    a = arvore(random.Random(1).sample(range(100), 100))
    antes, metricas = formato(a), a.metricas.comparacoes
    svg, quadros, _ = anim.quadros_splay(a, chave)
    assert formato(a) == antes and a.metricas.comparacoes == metricas  # só leitura
    a.buscar(chave)
    assert quadros[-1]["comp"] == a.metricas.comparacoes - metricas
    assert svg.count('class="no rev"') == len(a.ultimo_caminho)  # um nó por nó visitado
    conferir_ids(svg, quadros)
    achou = 0 <= chave < 100
    assert ("achou" in quadros[-1]["msg"]) == achou
    assert ('id="nulo"' in svg) == (not achou)
    # um quadro por nó visitado (+ o inicial, + o do filho vazio), cada um com balão
    assert len(quadros) == len(a.ultimo_caminho) + 1 + (not achou)
    assert all(q["balao"] for q in quadros[1:])


def test_splay_cursor_percorre_o_caminho():
    a = arvore(random.Random(3).sample(range(60), 60))
    _, quadros, _ = anim.quadros_splay(a, 17)
    posicoes = [q["cur"] for q in quadros]
    # o cursor desce um nível por quadro
    assert [y for _, y in posicoes[1:]] == sorted(y for _, y in posicoes[1:])
    assert len({y for _, y in posicoes[1:]}) == len(posicoes) - 1


def test_splay_arvore_vazia():
    svg, quadros, _ = anim.quadros_splay(SplayTree(), 3)
    assert "vazia" in svg and len(quadros) == 1


def test_splay_caminho_degenerado_e_limitado():
    a = SplayTree()
    for c in range(300):  # ids crescentes: a árvore vira uma lista
        a.inserir(c, c)
    svg, quadros, _ = anim.quadros_splay(a, -1, max_nos=50)
    assert svg.count('class="no rev"') == 50
    assert 'id="nulo"' not in svg  # a busca continuaria: não há filho vazio a mostrar
    assert "O desenho para aqui" in quadros[-1]["msg"]


@pytest.mark.parametrize("chave", [(2005,), (2007, 371), (2000, 0), (2009, 499), (2030,)])
def test_skip_comparacoes_iguais_a_busca_real_e_sem_metricas(chave):
    sl = lista_de_anos()
    m = sl.metricas.comparacoes
    svg, fixo, quadros, passos, _ = anim.quadros_skip(sl, chave)
    assert sl.metricas.comparacoes == m  # só leitura
    sl.buscar(chave)
    assert quadros[-1]["comp"] == sl.metricas.comparacoes - m
    assert len(quadros) == len(passos) + 1
    conferir_ids(svg, quadros)
    assert fixo.count("nível ") == sl.nivel


def test_skip_ponteiros_e_trechos_pulados():
    sl = lista_de_anos()
    svg, _, quadros, passos, _ = anim.quadros_skip(sl, (2007, 371))
    # cada caixa tem um ponteiro, menos as da torre do fim (que não aponta para nada)
    caixas = len(re.findall(r'id="b\d+_\d+"', svg))
    assert len(re.findall(r'id="p\d+_\d+"', svg)) == caixas - sl.nivel
    # torres de nós (sem a cabeça e o fim) + trechos pulados = todos os nós da lista
    torres = len(re.findall(r'id="b\d+_0"', svg)) - 2
    pulados = sum(int(x) for x in re.findall(r"⋯ (\d+) nós?<", svg))
    assert torres + pulados == len(sl)
    # o cursor termina no nó encontrado
    assert passos[-1][0] == "achou" and "achou" in quadros[-1]["balao"][0]


def test_temas_e_paginas():
    a = arvore(range(20))
    escura = anim.html_busca_splay(a, 7, nota_final="Nota.", tema="dark")
    clara = anim.html_busca_splay(a, 7, tema="light")
    assert quadros_da_pagina(escura)[-1]["msg"].endswith("Nota.")
    assert anim.TEMAS["dark"]["fundo"] in escura and anim.TEMAS["light"]["fundo"] in clara
    pagina, _ = anim.html_busca_skip_animada(lista_de_anos(), (2003, 160), tema="dark")
    assert len(quadros_da_pagina(pagina)) > 1 and "<svg" in pagina

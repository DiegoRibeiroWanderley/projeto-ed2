"""Testes das modificações M1 (splay com limiar) e M3 (skip list por popularidade)."""

import random

import pytest

from estruturas.skiplist import SkipList, nivel_por_popularidade
from estruturas.splay import SplayTree
from test_skiplist import verificar_invariantes as invariantes_skip
from test_splay import verificar_invariantes as invariantes_splay


# ------------------------------------------------------------------ M1
def cadeia(n, limiar=None):
    """Splay com n chaves inseridas em ordem: cadeia com 0 no fundo."""
    a = SplayTree(limiar=limiar)
    for c in range(n):
        a.inserir(c, c)
    return a


def test_m1_so_afunila_no_k_esimo_acesso():
    a = cadeia(50, limiar=3)
    raiz = a.raiz.chave
    for esperado in (1, 2):
        assert a.buscar(0) == 0
        assert not a.ultimo_afunilou and a.ultimo_contador == esperado
        assert a.raiz.chave == raiz and a.ultimas_rotacoes == []
    a.buscar(0)
    assert a.ultimo_afunilou and a.raiz.chave == 0
    assert a.ultimo_contador == 0  # contador zera após o splay
    invariantes_splay(a)


def test_m1_rotacoes_so_no_splay():
    a = cadeia(50, limiar=4)
    a.metricas.zerar()
    for _ in range(3):
        a.buscar(10)
    assert a.metricas.rotacoes == 0
    a.buscar(10)
    assert a.metricas.rotacoes > 0


def test_m1_busca_sem_sucesso_nao_afunila():
    a = cadeia(20, limiar=2)
    raiz = a.raiz.chave
    assert a.buscar(999) is None
    assert a.raiz.chave == raiz and not a.ultimo_afunilou


@pytest.mark.parametrize("limiar", [None, 1])
def test_m1_desligada_e_classica(limiar):
    a = cadeia(20, limiar=limiar)
    a.buscar(0)
    assert a.ultimo_afunilou and a.raiz.chave == 0
    b = cadeia(20, limiar=limiar)
    b.buscar(999)
    assert b.raiz.chave == 19  # clássica afunila o último visitado


def test_m1_insercao_continua_classica():
    a = SplayTree(limiar=5)
    for c in (5, 1, 9):
        a.inserir(c, c)
        assert a.raiz.chave == c


def test_m1_operacoes_aleatorias_mantem_invariantes():
    rng = random.Random(4)
    a, ref = SplayTree(limiar=3), set()
    for _ in range(3000):
        c = rng.randrange(300)
        op = rng.random()
        if op < 0.4:
            a.inserir(c, c)
            ref.add(c)
        elif op < 0.6:
            assert a.remover(c) == (c in ref)
            ref.discard(c)
        else:
            assert (a.buscar(c) is not None) == (c in ref)
        invariantes_splay(a)
    assert [k for k, _ in a] == sorted(ref)


def test_m1_pode_ser_trocada_em_execucao():
    a = cadeia(30, limiar=5)
    a.buscar(0)
    assert a.raiz.chave != 0
    a.limiar = None
    a.buscar(0)
    assert a.raiz.chave == 0


# ------------------------------------------------------------------ M3
def test_formula_do_nivel():
    assert [nivel_por_popularidade(a) for a in (0, 1, 2, 3, 6, 7, 15)] == [1, 2, 2, 3, 3, 4, 5]
    assert nivel_por_popularidade(10 ** 9, max_nivel=6) == 6


def lista(popularidade, n=300, seed=8):
    sl = SkipList(rng=random.Random(seed), popularidade=popularidade)
    for c in range(n):
        sl.inserir(c, c)
    return sl


def no_de(sl, chave):
    no = sl.cabeca.prox[0]
    while no.chave != chave:
        no = no.prox[0]
    return no


def test_m3_promove_nos_populares():
    sl = lista(True)
    alvo = next(c for c, _ in sl if no_de(sl, c).nivel == 1)  # começa no nível 1
    for acessos in range(1, 32):
        sl.buscar(alvo)
        assert no_de(sl, alvo).nivel == max(1, nivel_por_popularidade(acessos))
        invariantes_skip(sl)
    assert no_de(sl, alvo).nivel == 6
    assert sl.promocoes == 5


def test_m3_nunca_rebaixa_nivel_sorteado():
    sl = lista(True)
    alto = max((no_de(sl, c) for c, _ in sl), key=lambda n: n.nivel)
    nivel = alto.nivel
    sl.buscar(alto.chave)
    assert alto.nivel == nivel and sl.ultima_promocao is None


def test_m3_promocao_acima_do_topo_atualiza_nivel_da_lista():
    sl = SkipList(rng=random.Random(0), popularidade=True, max_nivel=8)
    for c in range(4):
        sl.inserir(c, c)
    for _ in range(255):
        sl.buscar(2)
    assert no_de(sl, 2).nivel == 8 and sl.nivel == 8
    assert sl.cabeca.prox[7] is no_de(sl, 2)
    invariantes_skip(sl)


def test_m3_popular_fica_mais_barato_de_achar():
    classica, modificada = lista(False, n=2000), lista(True, n=2000)
    for sl in (classica, modificada):
        for _ in range(200):
            sl.buscar(1500)
        sl.metricas.zerar()
        sl.buscar(1500)
    assert modificada.metricas.comparacoes < classica.metricas.comparacoes


def test_m3_desligada_nao_altera_niveis():
    sl = lista(False)
    antes = sl.tamanho_niveis()
    for _ in range(100):
        sl.buscar(42)
    assert sl.tamanho_niveis() == antes and sl.promocoes == 0
    assert no_de(sl, 42).acessos == 100  # conta, mas não promove


def test_m3_remocao_de_no_promovido():
    sl = lista(True)
    for _ in range(63):
        sl.buscar(77)
    assert sl.remover(77) and sl.buscar(77) is None
    invariantes_skip(sl)

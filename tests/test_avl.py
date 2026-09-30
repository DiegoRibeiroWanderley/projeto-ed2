import math
import random

from estruturas.avl import AVLTree


def verificar_invariantes(arv):
    """Ordem de BST, alturas corretas e fator de balanceamento em [-1, 1]."""

    def checar(no, lo, hi):
        if no is None:
            return -1, 0
        assert lo is None or no.chave > lo
        assert hi is None or no.chave < hi
        he, ne = checar(no.esq, lo, no.chave)
        hd, nd = checar(no.dir, no.chave, hi)
        assert abs(he - hd) <= 1
        assert no.altura == 1 + max(he, hd)
        return no.altura, ne + nd + 1

    _, n = checar(arv.raiz, None, None)
    assert n == len(arv)


def test_insercao_crescente_fica_balanceada():
    arv = AVLTree()
    n = 10000
    for c in range(n):
        arv.inserir(c, c)
    verificar_invariantes(arv)
    assert arv.altura() <= 1.44 * math.log2(n + 2)
    assert arv.metricas.rotacoes > 0


def test_operacoes_aleatorias_contra_referencia():
    rng = random.Random(7)
    arv, ref = AVLTree(), {}
    for _ in range(4000):
        c = rng.randrange(600)
        op = rng.random()
        if op < 0.5:
            assert arv.inserir(c, -c) == (c not in ref)
            ref[c] = -c
        elif op < 0.8:
            assert arv.remover(c) == (c in ref)
            ref.pop(c, None)
        else:
            assert arv.buscar(c) == ref.get(c)
        verificar_invariantes(arv)
    assert list(arv) == sorted(ref.items())


def test_atualizar_valor():
    arv = AVLTree()
    arv.inserir(1, "a")
    assert not arv.inserir(1, "b")
    assert arv.buscar(1) == "b" and len(arv) == 1


def test_profundidade_registrada():
    arv = AVLTree()
    for c in (2, 1, 3):
        arv.inserir(c, c)
    arv.metricas.zerar()
    arv.buscar(2)
    arv.buscar(3)
    assert arv.metricas.profundidades == [0, 1]

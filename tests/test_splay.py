import random

from estruturas.splay import SplayTree


def verificar_invariantes(arv):
    """Ordem de BST, ponteiros de pai coerentes e tamanho correto."""
    if arv.raiz is None:
        assert len(arv) == 0
        return
    assert arv.raiz.pai is None
    n, pilha = 0, [(arv.raiz, None, None)]
    while pilha:
        no, lo, hi = pilha.pop()
        n += 1
        assert lo is None or no.chave > lo
        assert hi is None or no.chave < hi
        for filho in (no.esq, no.dir):
            if filho is not None:
                assert filho.pai is no
        if no.esq is not None:
            pilha.append((no.esq, lo, no.chave))
        if no.dir is not None:
            pilha.append((no.dir, no.chave, hi))
    assert n == len(arv)


def test_insercao_e_busca_levam_a_raiz():
    arv = SplayTree()
    chaves = list(range(200))
    random.Random(1).shuffle(chaves)
    for c in chaves:
        assert arv.inserir(c, f"v{c}")
        assert arv.raiz.chave == c
    verificar_invariantes(arv)
    for c in chaves:
        assert arv.buscar(c) == f"v{c}"
        assert arv.raiz.chave == c
    verificar_invariantes(arv)
    assert [k for k, _ in arv] == sorted(chaves)


def test_inserir_existente_atualiza():
    arv = SplayTree()
    arv.inserir(5, "a")
    assert not arv.inserir(5, "b")
    assert len(arv) == 1
    assert arv.buscar(5) == "b"


def test_busca_sem_sucesso_afunila_ultimo_visitado():
    arv = SplayTree()
    for c in (10, 20, 30, 40):
        arv.inserir(c, c)
    assert arv.buscar(25) is None
    assert arv.raiz.chave in (20, 30)
    verificar_invariantes(arv)


def test_remocao_aleatoria_contra_referencia():
    rng = random.Random(42)
    arv, ref = SplayTree(), set()
    for _ in range(3000):
        c = rng.randrange(500)
        op = rng.random()
        if op < 0.5:
            assert arv.inserir(c, c) == (c not in ref)
            ref.add(c)
        elif op < 0.8:
            assert arv.remover(c) == (c in ref)
            ref.discard(c)
        else:
            assert (arv.buscar(c) is not None) == (c in ref)
        verificar_invariantes(arv)
    assert [k for k, _ in arv] == sorted(ref)


def test_remover_ate_esvaziar():
    arv = SplayTree()
    for c in range(50):
        arv.inserir(c, c)
    for c in range(50):
        assert arv.remover(c)
    assert arv.raiz is None and len(arv) == 0
    assert not arv.remover(1)


def test_insercao_crescente_degenera_sem_estourar_recursao():
    arv = SplayTree()
    for c in range(5000):
        arv.inserir(c, c)
    assert arv.altura() == 4999  # vira uma lista: motivo de inserir embaralhado
    assert arv.buscar(0) == 0  # percorre 5000 níveis sem recursão
    assert arv.altura() < 4999  # o splay reduziu a profundidade
    verificar_invariantes(arv)


def test_registro_de_caminho_e_rotacoes():
    arv = SplayTree()
    for c in (1, 2, 3):
        arv.inserir(c, c)  # vira a cadeia 3 -> 2 -> 1 à esquerda
    arv.metricas.zerar()
    arv.buscar(1)
    assert arv.ultimo_caminho == [3, 2, 1]
    assert arv.ultimas_rotacoes == [("zig-zig", 1)]
    assert arv.metricas.rotacoes == 2
    assert arv.metricas.profundidades == [2]


def test_contains_nao_altera_arvore():
    arv = SplayTree()
    for c in (1, 2, 3):
        arv.inserir(c, c)
    raiz = arv.raiz.chave
    assert 1 in arv and 99 not in arv
    assert arv.raiz.chave == raiz

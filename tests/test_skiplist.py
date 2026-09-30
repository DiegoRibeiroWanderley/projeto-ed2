import random

from estruturas.skiplist import SkipList


def verificar_invariantes(sl):
    """Cada nível é ordenado e é subsequência do nível abaixo."""
    anterior = None
    assert sum(1 for _ in sl) == len(sl)  # base contém todos os nós
    for i in range(sl.nivel):
        chaves, no = [], sl.cabeca.prox[i]
        while no is not None:
            assert no.nivel > i
            chaves.append(no.chave)
            no = no.prox[i]
        assert chaves == sorted(chaves) and len(set(chaves)) == len(chaves)
        if anterior is not None:
            assert set(chaves) <= set(anterior)
        anterior = chaves
    for i in range(sl.nivel, sl.max_nivel):
        assert sl.cabeca.prox[i] is None


def nova(seed=0):
    return SkipList(rng=random.Random(seed))


def test_operacoes_aleatorias_contra_referencia():
    rng = random.Random(3)
    sl, ref = nova(), {}
    for _ in range(4000):
        c = (rng.randrange(2007, 2020), rng.randrange(300))
        op = rng.random()
        if op < 0.5:
            assert sl.inserir(c, c) == (c not in ref)
            ref[c] = c
        elif op < 0.8:
            assert sl.remover(c) == (c in ref)
            ref.pop(c, None)
        else:
            assert sl.buscar(c) == ref.get(c)
    verificar_invariantes(sl)
    assert list(sl) == sorted(ref.items())
    assert len(sl) == len(ref)


def test_intervalo_por_ano_com_chave_composta():
    sl = nova()
    for ano in range(2007, 2020):
        for pid in range(10):
            sl.inserir((ano, pid), f"{ano}-{pid}")
    itens = list(sl.intervalo((2012,), (2015, float("inf"))))
    assert len(itens) == 40
    assert itens[0][0] == (2012, 0) and itens[-1][0] == (2015, 9)
    assert sl.contar_intervalo((2030,), (2040, float("inf"))) == 0


def test_paginacao():
    sl = nova()
    for pid in range(25):
        sl.inserir((2012, pid), pid)
    faixa = ((2012,), (2012, float("inf")))
    assert [v for _, v in sl.pagina(*faixa, 0, 10)] == list(range(10))
    assert [v for _, v in sl.pagina(*faixa, 2, 10)] == list(range(20, 25))
    assert sl.pagina(*faixa, 3, 10) == []


def test_niveis_diminuem_e_remocao_reduz_altura():
    sl = nova(seed=11)
    for c in range(2000):
        sl.inserir(c, c)
    tam = sl.tamanho_niveis()
    assert tam[0] == 2000
    assert all(tam[i] >= tam[i + 1] for i in range(len(tam) - 1))
    assert 5 <= sl.nivel <= 20
    for c in range(2000):
        assert sl.remover(c)
    assert len(sl) == 0 and sl.nivel == 1
    verificar_invariantes(sl)


def test_caminho_registrado():
    sl = nova()
    for c in range(100):
        sl.inserir(c, c)
    sl.buscar(77)
    cam = sl.ultimo_caminho
    assert cam and all(k < 77 for _, k in cam)  # só visita predecessores
    niveis = [n for n, _ in cam]
    assert niveis == sorted(niveis, reverse=True)  # só desce de nível
    assert [k for _, k in cam] == sorted(k for _, k in cam)  # só avança

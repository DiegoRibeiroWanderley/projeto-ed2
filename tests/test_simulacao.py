import random

import pytest

from app import simulacao as sim
from dados.carregador import Produto


def produtos(n=3000, sem_ano=10, semente=0):
    rng = random.Random(semente)
    saida = []
    for i in range(n):
        ano = None if i < sem_ano else rng.randrange(2008, 2019)
        saida.append(Produto(i + 1, "Men", "Apparel", "Topwear", "Tshirts", None, None, ano,
                             None, f"Produto {i + 1}"))
    return saida


def test_sequencia_deterministica_e_so_com_ano():
    ps = produtos()
    a = sim.gerar_sequencia(ps, 2000, 50, semente=3)
    b = sim.gerar_sequencia(ps, 2000, 50, semente=3)
    assert [p.id for p in a] == [p.id for p in b] and len(a) == 2000
    assert all(p.ano is not None for p in a)


def test_sequencia_concentrada_nos_populares():
    seq = sim.gerar_sequencia(produtos(), 5000, 50, s=1.2, ruido=0.0, semente=1)
    assert len({p.id for p in seq}) <= 50
    top = sim.contagem_real(seq, 1)[0]
    assert top[1] > 5000 / 50  # o mais popular recebe bem mais que a média


def test_mudanca_troca_os_populares():
    seq = sim.gerar_sequencia(produtos(), 4000, 30, ruido=0.0, mudanca=True, semente=2)
    primeira = {p.id for p in seq[:2000]}
    segunda = {p.id for p in seq[2000:]}
    assert len(primeira & segunda) < 10


def test_contagem_real_ordena_por_acessos():
    ps = produtos(10, sem_ano=0)
    seq = [ps[0]] * 3 + [ps[1]] * 5 + [ps[2]]
    assert [(p.id, n) for p, n in sim.contagem_real(seq, 2)] == [(2, 5), (1, 3)]


def test_media_por_bloco():
    assert sim.media_por_bloco(list(range(10)), 5) == [0.5, 2.5, 4.5, 6.5, 8.5]
    assert sim.media_por_bloco([], 5) == []


@pytest.fixture(scope="module")
def resultado():
    ps = produtos()
    seq = sim.gerar_sequencia(ps, 6000, 100, s=1.0, ruido=0.2, semente=4)
    return sim.simular(ps, seq, k=3)


def test_simulacao_mede_todas_as_variantes(resultado):
    nomes = [t["variante"] for t in resultado.tabela()]
    assert nomes == ["Splay clássica", "Splay M1 (k=3)", "AVL", "Skip list clássica",
                     "Skip list M3", "Lista com transposição", "Lista sem autoajuste"]
    for s in resultado.arvores + resultado.skips:
        assert len(s.comparacoes) == len(s.profundidade) == 6000


def test_m1_reduz_rotacoes(resultado):
    classica, m1, avl = resultado.arvores
    assert m1.media(m1.rotacoes) < classica.media(classica.rotacoes) / 2
    assert avl.media(avl.rotacoes) == 0  # buscas na AVL não rotacionam


def test_splay_ganha_da_avl_com_acessos_concentrados(resultado):
    classica, _, avl = resultado.arvores
    assert classica.media(classica.comparacoes) < avl.media(avl.comparacoes)


def test_m3_promove_populares_e_reduz_comparacoes(resultado):
    classica, m3 = resultado.skips
    assert m3.media(m3.comparacoes) < classica.media(classica.comparacoes)
    niv = resultado.niveis_populares
    assert sum(niv["Skip list M3"]) > sum(niv["Skip list clássica"])
    assert resultado.promocoes > 0


def test_ranking(resultado):
    rk = resultado.ranking
    assert 0.0 <= rk["precisao"] <= 1.0
    transp, fixa = rk["series"]
    assert transp.media(transp.comparacoes) <= fixa.media(fixa.comparacoes)

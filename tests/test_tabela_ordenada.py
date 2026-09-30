import random

from estruturas.tabela_ordenada import TabelaOrdenada, merge_sort


def test_merge_sort_estavel_contra_sorted():
    rng = random.Random(5)
    for n in (0, 1, 2, 7, 100, 1001):
        pares = [(rng.randrange(20), i) for i in range(n)]
        assert merge_sort(pares) == sorted(pares, key=lambda p: p[0])


def test_busca_binaria():
    t = TabelaOrdenada([(m, i) for i, m in enumerate(["Puma", "Nike", "ADIDAS", "Lee"])])
    assert [c for c, _ in t] == ["ADIDAS", "Lee", "Nike", "Puma"]
    assert t.buscar("Nike") == 1
    assert t.buscar("Reebok") is None
    assert t.indice("ADIDAS") == 0 and t.indice("Zzz") == -1


def test_busca_binaria_conta_log_n_comparacoes():
    t = TabelaOrdenada([(i, i) for i in range(1024)])
    t.metricas.zerar()
    t.buscar(777)
    assert t.metricas.comparacoes <= 12  # log2(1024) + 1 igualdade + folga


def test_prefixo_com_chave_composta_e_nomes_repetidos():
    nomes = [("puma men black shoes", 3), ("puma men black shoes", 1),
             ("puma women tee", 2), ("nike tee", 4), ("pumpkin", 5)]
    t = TabelaOrdenada([(c, c[1]) for c in nomes])
    assert len(t) == 5  # (nome, id) distingue os repetidos
    achados = [v for _, v in t.buscar_prefixo("puma ")]
    assert achados == [1, 3, 2]
    assert [v for _, v in t.buscar_prefixo("pum")] == [1, 3, 2, 5]
    assert t.buscar_prefixo("pum", limite=2) == [(("puma men black shoes", 1), 1),
                                                 (("puma men black shoes", 3), 3)]
    assert t.buscar_prefixo("zara") == []


def test_prefixo_com_chave_texto():
    t = TabelaOrdenada([(m, None) for m in ["Lee", "Lee Cooper", "Levis", "Lotto"]])
    assert [c for c, _ in t.buscar_prefixo("Le")] == ["Lee", "Lee Cooper", "Levis"]


def test_inserir_remover_mantem_ordem():
    rng = random.Random(9)
    t, ref = TabelaOrdenada(), {}
    for _ in range(1500):
        c = rng.randrange(300)
        if rng.random() < 0.6:
            assert t.inserir(c, c) == (c not in ref)
            ref[c] = c
        else:
            assert t.remover(c) == (c in ref)
            ref.pop(c, None)
    assert list(t) == sorted(ref.items())


def test_fatia_para_paginacao():
    t = TabelaOrdenada([(i, i) for i in range(10)])
    assert [c for c, _ in t.fatia(8, 5)] == [8, 9]
    assert t.item(0) == (0, 0)

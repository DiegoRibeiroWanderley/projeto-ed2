from estruturas.lista_encadeada import ListaEncadeada
from estruturas.lista_transposicao import ListaTransposicao


# ------------------------------------------------------- lista encadeada
def test_encadeada_insercao_busca_remocao():
    l = ListaEncadeada()
    for v in (2, 3):
        l.inserir_fim(v)
    l.inserir_inicio(1)
    assert list(l) == [1, 2, 3] and len(l) == 3
    assert l.buscar(2) == 2 and l.buscar(9) is None
    assert l.remover(3)  # remove o fim
    l.inserir_fim(4)
    assert list(l) == [1, 2, 4]
    assert l.remover(1) and l.remover(4) and l.remover(2)
    assert list(l) == [] and l.inicio is None and l.fim is None
    assert not l.remover(1)


# --------------------------------------------------- lista transposição
def ordem(l):
    return [c for c, _, _ in l]


def test_primeiro_acesso_insere_no_fim():
    l = ListaTransposicao()
    assert l.acessar("a", 1) == 0
    assert l.acessar("b", 2) == 1
    assert l.acessar("c", 3) == 2
    assert ordem(l) == ["a", "b", "c"]


def test_acesso_repetido_transpoe_com_antecessor():
    l = ListaTransposicao()
    for c in "abc":
        l.acessar(c, c)
    assert l.acessar("c") == 1
    assert ordem(l) == ["a", "c", "b"]
    assert l.acessar("c") == 0
    assert ordem(l) == ["c", "a", "b"]
    assert l.acessar("c") == 0  # já no topo: não se move
    assert l.primeiros(1) == [("c", "c", 4)]


def test_contador_acompanha_o_item_na_troca():
    l = ListaTransposicao()
    for c in "ab":
        l.acessar(c, c.upper())
    l.acessar("b")
    assert list(l) == [("b", "B", 2), ("a", "A", 1)]


def test_ranking_e_aproximado():
    # "a" tem mais acessos, mas "b" acessado por último sobe para a frente dele
    l = ListaTransposicao()
    for _ in range(5):
        l.acessar("a", "a")
    l.acessar("b", "b")
    l.acessar("b")
    assert ordem(l) == ["b", "a"]


def test_remocao_e_posicao():
    l = ListaTransposicao()
    for c in "abc":
        l.acessar(c, c)
    assert l.posicao("b") == 1 and l.posicao("z") == -1
    assert l.remover("a") and ordem(l) == ["b", "c"]
    assert l.remover("c") and ordem(l) == ["b"]
    assert not l.remover("z") and len(l) == 1

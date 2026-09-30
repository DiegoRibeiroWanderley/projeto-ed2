import os
import random
import re

import pytest

from app import visualizacao as viz
from estruturas.skiplist import SkipList
from estruturas.splay import SplayTree


def arvore(chaves):
    a = SplayTree()
    for c in chaves:
        a.inserir(c, c)
    return a


def nos_do_dot(dot):
    return set(re.findall(r"^\s*(n\d+) \[", dot, re.M))


def test_caminho_splay_nao_afunila():
    a = arvore(range(1, 8))  # cadeia 7 -> 6 -> ... -> 1
    raiz = a.raiz.chave
    m = a.metricas.comparacoes
    assert viz.caminho_splay(a, 1) == [7, 6, 5, 4, 3, 2, 1]
    assert viz.caminho_splay(a, 100) == [7]
    assert a.raiz.chave == raiz and a.metricas.comparacoes == m


def test_topo_limita_niveis_e_destaca():
    a = arvore(random.Random(1).sample(range(1000), 300))
    dot = viz.dot_topo_arvore(a.raiz, niveis=3, caminho=[a.raiz.chave], alvo=a.raiz.chave)
    assert len(nos_do_dot(dot)) <= 7
    assert viz.COR_ALVO in dot and "triangle" in dot
    assert dot.strip().endswith("}")
    assert "(vazia)" in viz.dot_topo_arvore(None)


def test_dot_caminho_trunca_caminhos_longos():
    a = arvore(range(200))  # cadeia de 200 nós
    cam = viz.caminho_splay(a, 0)
    dot = viz.dot_caminho(a, cam, max_nos=20)
    assert len(nos_do_dot(dot)) == 20
    assert "180 nós" in dot
    assert "n0 [" in dot and "n199 [" in dot


def test_dot_caminho_curto_mostra_irmaos():
    a = SplayTree()
    for c in (1, 3, 2):  # 2 na raiz, 1 à esquerda, 3 à direita
        a.inserir(c, c)
    dot = viz.dot_caminho(a, viz.caminho_splay(a, 3))
    assert "n2 [" in dot and "n3 [" in dot and "s2 [" in dot  # irmão 1 resumido
    # irmão esquerdo aparece antes do seguido, preservando a orientação
    assert dot.index("n2 -> s2") < dot.index("n2 -> n3")


def test_resumo_rotacoes():
    assert "nenhuma" in viz.resumo_rotacoes([])
    rot = [("zig-zag", 1), ("zig-zag", 1), ("zig-zig", 1), ("zig", 1)]
    assert viz.resumo_rotacoes(rot) == "zig-zag ×2 → zig-zig ×1 → zig ×1"


def lista_de_anos():
    sl = SkipList(rng=random.Random(2))
    for i in range(500):
        sl.inserir((2000 + i // 50, i), i)
    return sl


@pytest.mark.parametrize("chave", [(2005,), (2007, 371), (2000, 0), (2009, 499), (2030,)])
def test_rastro_igual_a_busca_real_e_sem_metricas(chave):
    sl = lista_de_anos()
    m = sl.metricas.comparacoes
    passos = viz.rastro_skip(sl, chave)
    assert sl.metricas.comparacoes == m  # não conta métricas
    sl.buscar(chave)
    assert viz.caminho_skip(sl, chave) == sl.ultimo_caminho  # mesmo caminho da busca real
    achou = passos[-1][0] == "achou"
    assert achou == (sl.buscar(chave) is not None)
    # cada passo compara uma vez; avanços só andam para a frente e os níveis só descem
    niveis = [p[1] for p in passos]
    assert niveis == sorted(niveis, reverse=True)


def test_html_da_busca_mostra_todos_os_nos_tocados():
    sl = lista_de_anos()
    chave = (2007, 371)
    html, passos = viz.html_busca_skip(sl, chave)
    tocadas = {p[3] for p in passos if p[3] is not None}
    for ano, pid in tocadas:
        assert f"<b>{ano}</b><br>{pid}</td>" in html  # toda chave tocada vira coluna
    assert html.count('class="p"') + html.count('class="hp"') >= sum(p[0] == "avança" for p in passos)
    assert "✓" in html and html.count("<tr") == sl.nivel + 1
    # colunas "⋯ N nós" somam exatamente os nós não tocados antes da última coluna
    pulados = sum(int(x) for x in re.findall(r"⋯<br>(\d+)<br>nós", html))
    ultima = max(tocadas)
    antes_da_ultima = sum(1 for k, _ in sl if k <= ultima)
    assert pulados + len(tocadas) == antes_da_ultima


def test_narracao_da_busca():
    sl = lista_de_anos()
    passos = viz.rastro_skip(sl, (2007, 371))
    texto = viz.narrar_busca_skip(passos, (2007, 371))
    assert len(texto) == len(passos) and "achou" in texto[-1]
    ausente = viz.narrar_busca_skip(viz.rastro_skip(sl, (2005,)), (2005,))
    assert "não está na lista" in ausente[-1]


def test_dot_ranking_com_transposicao():
    itens = [(1, 'Nike "Air"', 3), (2, "Puma", 1)]
    dot = viz.dot_ranking(itens, destaque=1, movimento=(1, 0))
    assert "transposição" in dot and '\\"Air\\"' in dot
    assert "transposição" not in viz.dot_ranking(itens, destaque=1, movimento=(0, 0))


RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.skipif(not os.path.exists(os.path.join(RAIZ, "styles.csv")),
                    reason="dataset real não baixado")
def test_app_streamlit_navega_sem_erros():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(os.path.join(RAIZ, "app", "streamlit_app.py"), default_timeout=120)
    at.run()
    assert not at.exception

    at.text_input[0].input("puma men black").run()
    assert not at.exception
    abrir = [b for b in at.button if b.label == "Abrir"]
    assert abrir
    abrir[0].click().run()
    assert not at.exception
    assert at.session_state.pagina == "Produto"
    ult = at.session_state.ultimo
    assert ult["achou"] and ult["caminho"][-1] == ult["id"]
    assert len(at.session_state.cat.ranking) == 1

    for pagina in ["Linha do tempo", "Marcas", "Mais populares", "Estruturas", "Produto"]:
        at.sidebar.radio[0].set_value(pagina).run()
        assert not at.exception, pagina
    # rerun sem clique não conta acesso novo
    at.run()
    assert len(at.session_state.cat.ranking) == 1
    assert at.session_state.cat.ranking.primeiros(1)[0][2] == 1

    # M1 e M3 ligadas pela barra lateral
    at.sidebar.toggle(key="m1").set_value(True).run()
    at.sidebar.toggle(key="m3").set_value(True).run()
    cat = at.session_state.cat
    assert cat.splay.limiar == 3 and cat.skip.popularidade
    at.sidebar.radio[0].set_value("Buscar").run()
    at.number_input[0].set_value(39386).run()
    [b for b in at.button if b.label == "Abrir id"][0].click().run()
    assert not at.exception
    ult = at.session_state.ultimo
    assert ult["m1"] == 3 and not ult["afunilou"] and ult["contador"] == 1
    assert ult["promocao"] is not None or ult["skip_nivel"] >= 2  # 1º acesso: alvo nível 2
    assert any("M1 ligada" in i.value for i in at.info)

    # simulação pequena + aplicação ao catálogo (F7)
    at.sidebar.radio[0].set_value("Simulação e métricas").run()
    at.number_input(key="sim_n").set_value(2000).run()
    [b for b in at.button if b.label.startswith("Rodar simulação")][0].click().run()
    assert not at.exception
    assert at.session_state.sim.n_acessos == 2000
    antes = at.session_state.cat.splay.metricas.operacoes
    [b for b in at.button if b.label.startswith("Aplicar")][0].click().run()
    assert not at.exception
    assert at.session_state.cat.splay.metricas.operacoes == antes + 500

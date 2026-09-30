import os

import pytest

from dados.carregador import carregar, extrair_marcas, normalizar
from dados.catalogo import Catalogo

CSV = """id,gender,masterCategory,subCategory,articleType,baseColour,season,year,usage,productDisplayName
10,Men,Apparel,Topwear,Shirts,Navy Blue,Fall,2011,Casual,Peter England Men Navy Blue Shirt
11,Men,Footwear,Shoes,Sports Shoes,Black,Summer,2012,Sports,Nike Men Black Shoes
12,Women,Footwear,Shoes,Sports Shoes,White,Summer,2015,Sports,Nike Women White Shoes
13,Unisex,Footwear,Shoes,Casual Shoes,White,Winter,2012,Casual,Newfeel Unisex White, Blue and Orange Casual Shoes
14,Men,Apparel,Topwear,Tshirts,Red,,,NA,Nike Red Tshirt
abc,Men,Apparel,Topwear,Tshirts,Red,Fall,2012,Casual,Id invalido
15,Men,Apparel
16,Women,Accessories,Watches,Watches,Silver,Winter,2016,Casual,Nike Women Silver Watch
"""


@pytest.fixture
def pasta(tmp_path):
    (tmp_path / "styles.csv").write_text(CSV, encoding="utf-8")
    img = tmp_path / "images"
    img.mkdir()
    for pid in (10, 11, 12, 13, 16, 999):  # 14 sem imagem; 999 sem registro
        (img / f"{pid}.jpg").write_bytes(b"")
    return str(tmp_path)


def test_relatorio_de_carga(pasta):
    produtos, rel = carregar(pasta)
    assert rel.linhas == 8
    assert rel.reparadas == 1
    assert rel.descartadas_colunas == 1
    assert rel.descartadas_id == 1
    assert rel.sem_ano == 1
    assert rel.sem_imagem == 1
    assert rel.imagens_sem_registro == 1
    assert [p.id for p in produtos] == [10, 11, 12, 13, 14, 16]


def test_linha_reparada_e_campos_opcionais(pasta):
    produtos, _ = carregar(pasta)
    por_id = {p.id: p for p in produtos}
    assert por_id[13].nome == "Newfeel Unisex White, Blue and Orange Casual Shoes"
    assert por_id[14].ano is None and por_id[14].estacao is None and por_id[14].uso is None
    assert por_id[14].imagem is None
    assert por_id[10].imagem.endswith("10.jpg")


def test_marcas_multipalavra_e_fallback(pasta):
    produtos, _ = carregar(pasta)
    por_id = {p.id: p.marca for p in produtos}
    assert por_id[10] == "Peter England"
    assert por_id[11] == "Nike"
    assert por_id[14] == "Nike"  # sem gênero: prefixo de marca conhecida
    assert por_id[13] == "Newfeel"


def test_marca_reduzida_a_marca_frequente():
    nomes = [f"Reebok Men Shoe {i}" for i in range(5)] + ["Reebok Reebounce Men Shoe"]
    assert extrair_marcas(nomes)[-1] == "Reebok"


def test_linha_de_produto_reduzida_a_marca_mas_lee_cooper_nao():
    nomes = ([f"Lee Men Jeans {i}" for i in range(5)]
             + [f"Lee Cooper Men Shoe {i}" for i in range(5)]
             + [f"Jockey Women Bra {i}" for i in range(5)]
             + [f"Jockey ZONE STRETCH Men Brief {i}" for i in range(6)])
    marcas = extrair_marcas(nomes)
    assert marcas[5] == "Lee Cooper"
    assert set(marcas[15:]) == {"Jockey"}


def test_marca_com_variacao_de_maiusculas():
    nomes = ["ADIDAS Men Tee"] * 3 + ["Adidas Men Tee"]
    assert set(extrair_marcas(nomes)) == {"ADIDAS"}


def test_normalizar():
    assert normalizar("  Nike   Men  ") == "nike men"


def test_catalogo_funcionalidades(pasta):
    cat = Catalogo.do_dataset(pasta)
    assert len(cat) == 6 and len(cat.skip) == 5  # produto 14 sem ano
    assert cat.anos == [2011, 2012, 2015, 2016]

    # F2 + F4
    assert cat.abrir(12).nome == "Nike Women White Shoes"
    assert cat.splay.raiz.chave == 12
    assert cat.abrir(999) is None
    cat.abrir(10)
    cat.abrir(10)
    assert [p.id for p, _ in cat.mais_populares()] == [10, 12]

    # F3
    assert [p.id for p in cat.linha_do_tempo(2012, 2015)] == [11, 13, 12]
    assert [p.id for p in cat.linha_do_tempo(2012, 2015, pagina=1, tamanho=2)] == [12]
    assert cat.total_no_intervalo(2011, 2016) == 5

    # F5
    assert cat.listar_marcas() == [("Newfeel", 1), ("Nike", 4), ("Peter England", 1)]
    assert cat.buscar_marcas("ni") == [("Nike", 4)]
    assert [p.id for p in cat.produtos_da_marca("NIKE")] == [11, 12, 14, 16]
    assert [p.id for p in cat.buscar_nome("nike w")] == [16, 12]  # "silver" < "white"


def test_referencias_compartilhadas(pasta):
    cat = Catalogo.do_dataset(pasta)
    p = cat.splay.buscar(11)
    assert cat.skip.buscar((2012, 11)) is p
    assert cat.buscar_nome("nike men black")[0] is p


RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.skipif(not os.path.exists(os.path.join(RAIZ, "styles.csv")),
                    reason="dataset real não baixado")
def test_dataset_real():
    cat = Catalogo.do_dataset(RAIZ, com_avl=False)
    r = cat.relatorio
    assert r.linhas == 44446 and r.reparadas == 22
    assert r.descartadas_colunas == 0 and r.descartadas_id == 0
    assert len(cat) == 44446 and r.sem_ano == 1
    assert r.sem_imagem == 5

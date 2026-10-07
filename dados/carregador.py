"""Leitura do styles.csv (Fashion Product Images Small) — requisitos D1 a D4.

Tratamento de dados (ver requisitos.MD, seção 3):
- linhas com mais de 10 colunas (vírgula sem aspas no nome) são reparadas
  reunindo as colunas excedentes no productDisplayName;
- linhas com menos colunas ou sem id numérico são descartadas;
- produtos sem year ficam fora da skip list (tratado no catálogo);
- season/usage vazios ou "NA" viram None;
- produtos sem imagem ficam com imagem = None (placeholder na interface).

A marca não existe no dataset e é extraída do nome (extrair_marcas).
"""

import csv
import os
import re

from estruturas.lista_encadeada import ListaEncadeada
from estruturas.tabela_ordenada import TabelaOrdenada, merge_sort

COLUNAS = ["id", "gender", "masterCategory", "subCategory", "articleType",
           "baseColour", "season", "year", "usage", "productDisplayName"]

# Palavras de gênero que, no productDisplayName, vêm logo após a marca.
_GENERO = re.compile(r"\b(Men's|Women's|Boy's|Girl's|Mens|Womens|Men|Women|"
                     r"Boys|Girls|Unisex|Kids|For Him|For Her)\b")
MIN_MARCA_FREQUENTE = 5
# Marcas que começam com outra marca frequente mas são empresas distintas;
# não são reduzidas pelo passo 4 ("Lee Cooper" não é linha da "Lee").
MARCAS_DISTINTAS = ["Lee Cooper"]


class Produto:
    """Um registro do styles.csv. As estruturas guardam referências a ele."""

    __slots__ = ("id", "genero", "categoria", "subcategoria", "tipo", "cor",
                 "estacao", "ano", "uso", "nome", "marca", "imagem")

    def __init__(self, id, genero, categoria, subcategoria, tipo, cor,
                 estacao, ano, uso, nome):
        self.id = id
        self.genero = genero
        self.categoria = categoria
        self.subcategoria = subcategoria
        self.tipo = tipo
        self.cor = cor
        self.estacao = estacao
        self.ano = ano
        self.uso = uso
        self.nome = nome
        self.marca = None
        self.imagem = None

    def __repr__(self):
        return f"Produto({self.id}, {self.nome!r}, {self.marca!r}, {self.ano})"


class RelatorioCarga:
    """Contagem de cada caso tratado na carga (requisito D4)."""

    def __init__(self):
        self.linhas = 0
        self.reparadas = 0
        self.descartadas_colunas = 0
        self.descartadas_id = 0
        self.sem_ano = 0
        self.sem_imagem = 0
        self.imagens_sem_registro = 0
        self.marcas = 0

    def texto(self):
        return "\n".join([
            f"Linhas de dados lidas:            {self.linhas}",
            f"  reparadas (vírgula no nome):    {self.reparadas}",
            f"  descartadas (colunas faltando): {self.descartadas_colunas}",
            f"  descartadas (id inválido):      {self.descartadas_id}",
            f"Produtos sem ano (fora da skip):  {self.sem_ano}",
            f"Produtos sem imagem:              {self.sem_imagem}",
            f"Imagens sem registro (ignoradas): {self.imagens_sem_registro}",
            f"Marcas distintas:                 {self.marcas}",
        ])


def normalizar(texto):
    """Minúsculas e espaços simples — usado nas chaves dos índices."""
    return " ".join(texto.lower().split())


def _opcional(valor):
    """Campo opcional: vazio ou "NA" vira None (exibido como "—")."""
    valor = valor.strip()
    return None if valor in ("", "NA") else valor


def ler_csv(caminho_csv, relatorio):
    """Lê o CSV e devolve a lista de Produto (sem marca nem imagem ainda)."""
    produtos = []
    with open(caminho_csv, encoding="utf-8", newline="") as f:
        leitor = csv.reader(f)
        next(leitor)  # cabeçalho
        for linha in leitor:
            relatorio.linhas += 1
            if len(linha) < len(COLUNAS):
                relatorio.descartadas_colunas += 1
                continue
            if len(linha) > len(COLUNAS):
                linha = linha[:9] + [",".join(linha[9:])]
                relatorio.reparadas += 1
            id_txt = linha[0].strip()
            if not id_txt.isdigit():
                relatorio.descartadas_id += 1
                continue
            ano_txt = linha[7].strip()
            ano = int(ano_txt) if ano_txt.isdigit() else None
            if ano is None:
                relatorio.sem_ano += 1
            produtos.append(Produto(
                int(id_txt), linha[1].strip(), linha[2].strip(), linha[3].strip(),
                linha[4].strip(), _opcional(linha[5]), _opcional(linha[6]), ano,
                _opcional(linha[8]), " ".join(linha[9].split()),
            ))
    return produtos


# --------------------------------------------------------------- marcas
def _contar(textos):
    """Conta ocorrências: TabelaOrdenada chave_minúscula -> (grafia, n).

    A grafia exibida é a mais frequente entre as variantes de maiúsculas
    ("ADIDAS" vs "Adidas").
    """
    ordenados = merge_sort([((normalizar(t), t), None) for t in textos])
    pares = []
    i = 0
    while i < len(ordenados):
        chave = ordenados[i][0][0]
        total, melhor, melhor_n = 0, None, 0
        while i < len(ordenados) and ordenados[i][0][0] == chave:
            grafia, n = ordenados[i][0][1], 0
            while (i < len(ordenados) and ordenados[i][0][0] == chave
                   and ordenados[i][0][1] == grafia):
                n += 1
                i += 1
            total += n
            if n > melhor_n:
                melhor, melhor_n = grafia, n
        pares.append((chave, (melhor, total)))
    return TabelaOrdenada(pares)


def _maior_prefixo_conhecido(palavras, conhecidas):
    """Maior prefixo (em palavras) que é marca conhecida."""
    for k in range(len(palavras), 0, -1):
        achado = conhecidas.buscar(normalizar(" ".join(palavras[:k])))
        if achado is not None:
            return achado[0]
    return None


def _menor_prefixo_frequente(palavras, conhecidas):
    """Menor prefixo que é marca conhecida com >= MIN_MARCA_FREQUENTE produtos.

    O menor, e não o maior, porque os casos longos são quase sempre linhas
    de produto da mesma marca ("ADIDAS Originals", "Jockey ZONE").
    """
    for k in range(1, len(palavras) + 1):
        achado = conhecidas.buscar(normalizar(" ".join(palavras[:k])))
        if achado is not None and achado[1] >= MIN_MARCA_FREQUENTE:
            return achado[0]
    return None


def extrair_marcas(nomes):
    """Marca de cada nome, na mesma ordem (heurística da seção 3).

    1. texto antes da palavra de gênero;
    2. senão, o maior prefixo que seja marca conhecida do passo 1;
    3. senão, a primeira palavra;
    4. reduz a marca à menor marca conhecida frequente que seja seu prefixo
       (exceto MARCAS_DISTINTAS).
    """
    distintas = TabelaOrdenada([(normalizar(m), (m, 0)) for m in MARCAS_DISTINTAS])
    candidatas = []
    for nome in nomes:
        m = _GENERO.search(nome)
        candidatas.append(nome[:m.start()].strip() if m and m.start() > 0 else None)
    conhecidas = _contar([c for c in candidatas if c])

    marcas = []
    for nome, cand in zip(nomes, candidatas):
        if cand is None:
            palavras = nome.split()
            cand = _maior_prefixo_conhecido(palavras, conhecidas) or (
                palavras[0] if palavras else "Desconhecida")
        canon = _maior_prefixo_conhecido(cand.split(), distintas)
        if canon is None:
            canon = _menor_prefixo_frequente(cand.split(), conhecidas)
        if canon is None:  # ao menos unifica a grafia ("Adidas" -> "ADIDAS")
            exata = conhecidas.buscar(normalizar(cand))
            canon = exata[0] if exata is not None else cand
        marcas.append(canon)
    return marcas


# -------------------------------------------------------------- imagens
def associar_imagens(produtos, pasta_imagens, relatorio):
    """Preenche produto.imagem usando busca binária nos nomes de arquivo."""
    arquivos = os.listdir(pasta_imagens) if os.path.isdir(pasta_imagens) else []
    tabela = TabelaOrdenada([(a, None) for a in arquivos])
    ids = TabelaOrdenada([(p.id, None) for p in produtos])
    for p in produtos:
        arquivo = f"{p.id}.jpg"
        if tabela.indice(arquivo) >= 0:
            p.imagem = os.path.join(pasta_imagens, arquivo)
        else:
            relatorio.sem_imagem += 1
    for a in arquivos:
        base = a[:-4] if a.endswith(".jpg") else ""
        if not base.isdigit() or ids.indice(int(base)) < 0:
            relatorio.imagens_sem_registro += 1


def carregar(pasta_dataset):
    """Lê styles.csv e images/ de pasta_dataset. Devolve (produtos, relatório)."""
    relatorio = RelatorioCarga()
    produtos = ler_csv(os.path.join(pasta_dataset, "styles.csv"), relatorio)
    for p, marca in zip(produtos, extrair_marcas([p.nome for p in produtos])):
        p.marca = marca
    associar_imagens(produtos, os.path.join(pasta_dataset, "images"), relatorio)
    return produtos, relatorio


def agrupar_por_marca(produtos):
    """TabelaOrdenada marca_normalizada -> (marca, ListaEncadeada de produtos)."""
    ordenados = merge_sort([((normalizar(p.marca), p.id), p) for p in produtos])
    pares, i = [], 0
    while i < len(ordenados):
        chave = ordenados[i][0][0]
        lista = ListaEncadeada()
        marca = ordenados[i][1].marca
        while i < len(ordenados) and ordenados[i][0][0] == chave:
            lista.inserir_fim(ordenados[i][1])
            i += 1
        pares.append((chave, (marca, lista)))
    return TabelaOrdenada(pares)

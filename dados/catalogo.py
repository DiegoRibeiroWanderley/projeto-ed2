"""Catálogo: monta todas as estruturas (F1) e oferece as funcionalidades F2–F5.

Independe da interface (N2): a CLI e, depois, o Streamlit só chamam estes
métodos. As estruturas secundárias guardam referências ao mesmo objeto
Produto guardado na splay, nunca cópias.
"""

import random
import time

from estruturas.avl import AVLTree
from estruturas.lista_transposicao import ListaTransposicao
from estruturas.skiplist import SkipList
from estruturas.splay import SplayTree
from estruturas.tabela_ordenada import TabelaOrdenada

from .carregador import agrupar_por_marca, carregar, normalizar

INFINITO = float("inf")


class Catalogo:
    """m1_limiar: k da modificação M1 na splay (None = clássica).
    m3: liga a modificação M3 (nível por popularidade) na skip list.
    Ambas podem ser trocadas depois com configurar().
    """

    def __init__(self, produtos, semente=0, com_avl=True, m1_limiar=None, m3=False):
        inicio = time.perf_counter()
        rng = random.Random(semente)
        # Inserir ids crescentes degeneraria a splay em lista (requisitos, seção 4).
        embaralhados = list(produtos)
        rng.shuffle(embaralhados)

        self.splay = SplayTree()
        self.avl = AVLTree() if com_avl else None
        self.skip = SkipList(rng=random.Random(semente + 1))
        for p in embaralhados:
            self.splay.inserir(p.id, p)
            if self.avl is not None:
                self.avl.inserir(p.id, p)
            if p.ano is not None:
                self.skip.inserir((p.ano, p.id), p)

        self.ranking = ListaTransposicao()
        self.marcas = agrupar_por_marca(produtos)
        self.nomes = TabelaOrdenada([((normalizar(p.nome), p.id), p) for p in produtos])
        self.anos = self._anos_distintos()
        self.tempo_montagem = time.perf_counter() - inicio

        for estrutura in (self.splay, self.avl, self.skip, self.marcas, self.nomes):
            if estrutura is not None:
                estrutura.metricas.zerar()  # métricas contam só o uso, não a carga
        # as modificações só valem para o uso; a carga é igual nas duas versões
        self.configurar(m1_limiar, m3)

    def configurar(self, m1_limiar=None, m3=False):
        """Liga/desliga as modificações (requisitos.MD, seção 5)."""
        self.splay.limiar = m1_limiar
        self.skip.popularidade = m3

    @classmethod
    def do_dataset(cls, pasta, **kw):
        produtos, relatorio = carregar(pasta)
        catalogo = cls(produtos, **kw)
        relatorio.marcas = len(catalogo.marcas)
        catalogo.relatorio = relatorio
        return catalogo

    def __len__(self):
        return len(self.splay)

    def _anos_distintos(self):
        anos, ultimo = [], None
        for (ano, _), _ in self.skip:
            if ano != ultimo:
                anos.append(ano)
                ultimo = ano
        return anos

    # ------------------------------------------------------ F2: abrir produto
    def abrir(self, id_produto):
        """Busca o produto na splay (que o afunila) e registra a visualização.

        A visualização também é registrada na skip list (busca por
        (ano, id)): é essa contagem que, com M3 ligada, promove os
        produtos populares a níveis mais altos.
        """
        produto = self.splay.buscar(id_produto)
        if self.avl is not None:
            self.avl.buscar(id_produto)  # mesma busca na AVL, para comparação (I3)
        if produto is not None:
            self.ranking.acessar(id_produto, produto)
            if produto.ano is not None:
                self.skip.buscar((produto.ano, produto.id))
        return produto

    # ------------------------------------------- F3: linha do tempo / filtro
    def linha_do_tempo(self, ano_ini, ano_fim, pagina=0, tamanho=20):
        """Página do intervalo [ano_ini, ano_fim] em ordem (ano, id)."""
        itens = self.skip.pagina((ano_ini,), (ano_fim, INFINITO), pagina, tamanho)
        return [p for _, p in itens]

    def total_no_intervalo(self, ano_ini, ano_fim):
        return self.skip.contar_intervalo((ano_ini,), (ano_fim, INFINITO))

    # ------------------------------------------------------- F4: ranking
    def mais_populares(self, n=10):
        """[(produto, acessos)] na ordem da lista com transposição."""
        return [(p, acessos) for _, p, acessos in self.ranking.primeiros(n)]

    # ---------------------------------------------- F5: marcas e nomes
    def listar_marcas(self, pagina=0, tamanho=30):
        """[(marca, quantidade de produtos)] em ordem alfabética."""
        return [(marca, len(lista))
                for _, (marca, lista) in self.marcas.fatia(pagina * tamanho, tamanho)]

    def buscar_marcas(self, prefixo, limite=30):
        return [(marca, len(lista))
                for _, (marca, lista) in self.marcas.buscar_prefixo(normalizar(prefixo), limite)]

    def produtos_da_marca(self, marca):
        achado = self.marcas.buscar(normalizar(marca))
        return list(achado[1]) if achado is not None else []

    def buscar_nome(self, prefixo, limite=20):
        """Produtos cujo nome começa com prefixo (busca binária + varredura)."""
        return [p for _, p in self.nomes.buscar_prefixo(normalizar(prefixo), limite)]

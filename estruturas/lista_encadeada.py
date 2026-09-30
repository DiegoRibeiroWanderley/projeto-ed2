"""Lista simplesmente encadeada com busca sequencial.

Usada para guardar os produtos de cada marca no índice de marcas.
"""

from .metricas import Metricas


class _No:
    __slots__ = ("valor", "prox")

    def __init__(self, valor, prox=None):
        self.valor = valor
        self.prox = prox


class ListaEncadeada:
    def __init__(self, metricas=None):
        self.inicio = None
        self.fim = None
        self._tamanho = 0
        self.metricas = metricas if metricas is not None else Metricas()

    def __len__(self):
        return self._tamanho

    def __iter__(self):
        no = self.inicio
        while no is not None:
            yield no.valor
            no = no.prox

    def inserir_inicio(self, valor):
        self.inicio = _No(valor, self.inicio)
        if self.fim is None:
            self.fim = self.inicio
        self._tamanho += 1

    def inserir_fim(self, valor):
        no = _No(valor)
        if self.fim is None:
            self.inicio = self.fim = no
        else:
            self.fim.prox = no
            self.fim = no
        self._tamanho += 1

    def buscar(self, valor):
        """Busca sequencial; devolve o valor encontrado ou None."""
        self.metricas.registrar_operacao()
        no = self.inicio
        while no is not None:
            self.metricas.comparar()
            if no.valor == valor:
                return no.valor
            no = no.prox
        return None

    def remover(self, valor):
        """Remove a primeira ocorrência de valor. Devolve True se removeu."""
        self.metricas.registrar_operacao()
        ant, no = None, self.inicio
        while no is not None:
            self.metricas.comparar()
            if no.valor == valor:
                if ant is None:
                    self.inicio = no.prox
                else:
                    ant.prox = no.prox
                if no is self.fim:
                    self.fim = ant
                self._tamanho -= 1
                return True
            ant, no = no, no.prox
        return False

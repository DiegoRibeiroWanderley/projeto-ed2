"""Tabela ordenada em vetor com busca binária.

Usada no índice de marcas e no índice de nomes (F5). O vetor nativo do
Python é usado apenas como armazenamento contíguo; a ordenação (merge sort)
e as buscas são implementadas aqui.

As chaves podem ser strings ou tuplas cujo primeiro elemento é string,
como (nome_normalizado, id) — a busca por prefixo olha esse primeiro
elemento.
"""

from .metricas import Metricas


def merge_sort(pares, metricas=None):
    """Ordena uma lista de (chave, valor) por chave, de forma estável.

    Versão iterativa (bottom-up): intercala blocos de tamanho 1, depois 2,
    4, 8... até cobrir o vetor, alternando entre dois vetores auxiliares.
    O(n log n), sem recursão.
    """
    n = len(pares)
    if n <= 1:
        return list(pares)
    origem = list(pares)
    destino = [None] * n
    largura = 1
    while largura < n:
        for ini in range(0, n, 2 * largura):
            meio = min(ini + largura, n)
            fim = min(ini + 2 * largura, n)
            # intercala origem[ini:meio] e origem[meio:fim] em destino[ini:fim]
            i, j, k = ini, meio, ini
            while i < meio and j < fim:
                if metricas is not None:
                    metricas.comparar()
                # "<" estrito: em empate fica o da esquerda (ordenação estável)
                if origem[j][0] < origem[i][0]:
                    destino[k] = origem[j]
                    j += 1
                else:
                    destino[k] = origem[i]
                    i += 1
                k += 1
            while i < meio:  # copia o que sobrou de um dos lados
                destino[k] = origem[i]
                i += 1
                k += 1
            while j < fim:
                destino[k] = origem[j]
                j += 1
                k += 1
        origem, destino = destino, origem  # o resultado vira a entrada da próxima passada
        largura *= 2
    return origem


def _texto(chave):
    """Parte textual da chave: a própria string ou o 1º elemento da tupla."""
    return chave[0] if isinstance(chave, tuple) else chave


class TabelaOrdenada:
    """Dois vetores paralelos, chaves (ordenadas) e valores, na mesma posição."""

    def __init__(self, pares=(), metricas=None):
        """Monta a tabela de uma vez: ordena com merge sort e descarta chaves repetidas."""
        self.metricas = metricas if metricas is not None else Metricas()
        self._chaves = []
        self._valores = []
        for chave, valor in merge_sort(list(pares)):
            if self._chaves and self._chaves[-1] == chave:
                self._valores[-1] = valor  # chave repetida: fica o último valor
            else:
                self._chaves.append(chave)
                self._valores.append(valor)

    def __len__(self):
        return len(self._chaves)

    def __iter__(self):
        for i in range(len(self._chaves)):
            yield self._chaves[i], self._valores[i]

    def item(self, i):
        """Par (chave, valor) da posição i."""
        return self._chaves[i], self._valores[i]

    def _limite_inferior(self, chave):
        """Primeiro índice i com chaves[i] >= chave (busca binária)."""
        ini, fim = 0, len(self._chaves)
        while ini < fim:
            # invariante: chaves[:ini] < chave <= chaves[fim:]
            meio = (ini + fim) // 2
            self.metricas.comparar()
            if self._chaves[meio] < chave:
                ini = meio + 1
            else:
                fim = meio
        return ini

    def indice(self, chave):
        """Índice da chave ou -1."""
        self.metricas.registrar_operacao()
        i = self._limite_inferior(chave)
        if i < len(self._chaves):
            self.metricas.comparar()
            if self._chaves[i] == chave:
                return i
        return -1

    def buscar(self, chave):
        """Valor associado à chave, ou None (busca binária)."""
        i = self.indice(chave)
        return self._valores[i] if i >= 0 else None

    def buscar_prefixo(self, prefixo, limite=None):
        """Itens cuja chave (ou 1º elemento da chave) começa com prefixo."""
        self.metricas.registrar_operacao()
        # todas as chaves com o prefixo estão juntas e começam no limite
        # inferior do próprio prefixo; (prefixo,) é menor que qualquer
        # (prefixo, id), então também serve para chaves em tupla
        amostra = self._chaves[0] if self._chaves else ""
        alvo = (prefixo,) if isinstance(amostra, tuple) else prefixo
        i = self._limite_inferior(alvo)
        saida = []
        # varre em ordem até a primeira chave sem o prefixo
        while i < len(self._chaves) and (limite is None or len(saida) < limite):
            self.metricas.comparar()
            if not _texto(self._chaves[i]).startswith(prefixo):
                break
            saida.append((self._chaves[i], self._valores[i]))
            i += 1
        return saida

    def fatia(self, inicio, quantidade):
        """Página da tabela em ordem: itens [inicio, inicio + quantidade)."""
        fim = min(inicio + quantidade, len(self._chaves))
        return [(self._chaves[i], self._valores[i]) for i in range(max(inicio, 0), fim)]

    def inserir(self, chave, valor):
        """Insere mantendo a ordem (desloca o vetor). Devolve False se só atualizou."""
        self.metricas.registrar_operacao()
        i = self._limite_inferior(chave)
        if i < len(self._chaves) and self._chaves[i] == chave:
            self._valores[i] = valor
            return False
        self._chaves.insert(i, chave)
        self._valores.insert(i, valor)
        return True

    def remover(self, chave):
        """Remove a chave, deslocando o resto do vetor. Devolve True se removeu."""
        i = self.indice(chave)
        if i < 0:
            return False
        del self._chaves[i]
        del self._valores[i]
        return True

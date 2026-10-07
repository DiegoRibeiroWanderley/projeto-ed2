"""Lista autoajustável com transposição (busca sequencial).

Usada no ranking de "mais populares" (F4). Contém apenas os itens já
acessados: o primeiro acesso insere no fim; cada acesso seguinte troca o
item com o seu antecessor. O ranking resultante é aproximado — itens muito
acessados tendem a ficar na frente, mas a lista não é ordenada por
contagem. O contador de acessos é guardado só para exibição.
"""

from .metricas import Metricas


class _No:
    __slots__ = ("chave", "valor", "acessos", "prox")

    def __init__(self, chave, valor):
        self.chave = chave
        self.valor = valor
        self.acessos = 1  # só para exibição; não decide a ordem
        self.prox = None


class ListaTransposicao:
    def __init__(self, metricas=None):
        self.inicio = None
        self._tamanho = 0
        self.metricas = metricas if metricas is not None else Metricas()

    def __len__(self):
        return self._tamanho

    def __iter__(self):
        """Percorre em ordem de ranking: (chave, valor, acessos)."""
        no = self.inicio
        while no is not None:
            yield no.chave, no.valor, no.acessos
            no = no.prox

    def primeiros(self, n):
        """Os n primeiros do ranking: [(chave, valor, acessos)]."""
        saida = []
        for item in self:
            if len(saida) == n:
                break
            saida.append(item)
        return saida

    def acessar(self, chave, valor=None):
        """Registra um acesso a chave e devolve sua nova posição (0 = topo).

        Se a chave não está na lista, é inserida no fim (valor é obrigatório
        nesse caso). Se está, é transposta com o antecessor.
        """
        self.metricas.registrar_operacao()
        ant, no, pos = None, self.inicio, 0
        while no is not None:
            self.metricas.comparar()
            if no.chave == chave:
                no.acessos += 1
                if ant is None:
                    return 0
                # Transposição: troca o conteúdo do nó com o do antecessor.
                # Trocar o conteúdo é mais simples que religar os ponteiros,
                # que exigiria guardar também o antecessor do antecessor.
                ant.chave, no.chave = no.chave, ant.chave
                ant.valor, no.valor = no.valor, ant.valor
                ant.acessos, no.acessos = no.acessos, ant.acessos
                return pos - 1
            ant, no, pos = no, no.prox, pos + 1

        # não está na lista: entra no fim (ant é o último nó)
        novo = _No(chave, valor)
        if ant is None:
            self.inicio = novo
        else:
            ant.prox = novo
        self._tamanho += 1
        return pos

    def posicao(self, chave):
        """Posição da chave (sem contar como acesso) ou -1."""
        no, pos = self.inicio, 0
        while no is not None:
            if no.chave == chave:
                return pos
            no, pos = no.prox, pos + 1
        return -1

    def remover(self, chave):
        """Remove a chave. Devolve True se removeu."""
        self.metricas.registrar_operacao()
        ant, no = None, self.inicio
        while no is not None:
            self.metricas.comparar()
            if no.chave == chave:
                if ant is None:
                    self.inicio = no.prox
                else:
                    ant.prox = no.prox
                self._tamanho -= 1
                return True
            ant, no = no, no.prox
        return False

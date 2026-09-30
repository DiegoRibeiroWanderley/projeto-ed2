"""Árvore AVL — base de comparação de desempenho com a splay (I3).

Inserção e remoção são recursivas: a altura da AVL é no máximo
~1,44·log2(n) (≈ 23 para 44 mil nós), então não há risco de estourar o
limite de recursão do Python, ao contrário da splay.
"""

from .metricas import Metricas


class NoAVL:
    __slots__ = ("chave", "valor", "esq", "dir", "altura")

    def __init__(self, chave, valor):
        self.chave = chave
        self.valor = valor
        self.esq = None
        self.dir = None
        self.altura = 0


def _alt(no):
    return no.altura if no is not None else -1


def _atualizar(no):
    no.altura = 1 + max(_alt(no.esq), _alt(no.dir))


def _fator(no):
    return _alt(no.esq) - _alt(no.dir)


class AVLTree:
    def __init__(self, metricas=None):
        self.raiz = None
        self._tamanho = 0
        self.metricas = metricas if metricas is not None else Metricas()

    def __len__(self):
        return self._tamanho

    def __contains__(self, chave):
        no = self.raiz
        while no is not None:
            if chave == no.chave:
                return True
            no = no.esq if chave < no.chave else no.dir
        return False

    # ------------------------------------------------------------ rotações
    def _rot_dir(self, y):
        x = y.esq
        y.esq = x.dir
        x.dir = y
        _atualizar(y)
        _atualizar(x)
        self.metricas.rotacionar()
        return x

    def _rot_esq(self, x):
        y = x.dir
        x.dir = y.esq
        y.esq = x
        _atualizar(x)
        _atualizar(y)
        self.metricas.rotacionar()
        return y

    def _balancear(self, no):
        _atualizar(no)
        f = _fator(no)
        if f > 1:
            if _fator(no.esq) < 0:
                no.esq = self._rot_esq(no.esq)  # caso esquerda-direita
            return self._rot_dir(no)
        if f < -1:
            if _fator(no.dir) > 0:
                no.dir = self._rot_dir(no.dir)  # caso direita-esquerda
            return self._rot_esq(no)
        return no

    # ------------------------------------------------------------ busca
    def buscar(self, chave):
        self.metricas.registrar_operacao()
        no, prof = self.raiz, 0
        while no is not None:
            self.metricas.comparar()
            if chave == no.chave:
                self.metricas.registrar_profundidade(prof)
                return no.valor
            self.metricas.comparar()
            no = no.esq if chave < no.chave else no.dir
            prof += 1
        self.metricas.registrar_profundidade(prof - 1)
        return None

    # ---------------------------------------------------------- inserção
    def inserir(self, chave, valor):
        """Insere (ou atualiza). Devolve True se inseriu."""
        self.metricas.registrar_operacao()
        self._inseriu = False
        self.raiz = self._inserir(self.raiz, chave, valor)
        if self._inseriu:
            self._tamanho += 1
        return self._inseriu

    def _inserir(self, no, chave, valor):
        if no is None:
            self._inseriu = True
            return NoAVL(chave, valor)
        self.metricas.comparar()
        if chave == no.chave:
            no.valor = valor
            return no
        self.metricas.comparar()
        if chave < no.chave:
            no.esq = self._inserir(no.esq, chave, valor)
        else:
            no.dir = self._inserir(no.dir, chave, valor)
        return self._balancear(no)

    # ----------------------------------------------------------- remoção
    def remover(self, chave):
        """Remove a chave. Devolve True se removeu."""
        self.metricas.registrar_operacao()
        self._removeu = False
        self.raiz = self._remover(self.raiz, chave)
        if self._removeu:
            self._tamanho -= 1
        return self._removeu

    def _remover(self, no, chave):
        if no is None:
            return None
        self.metricas.comparar()
        if chave == no.chave:
            self._removeu = True
            if no.esq is None:
                return no.dir
            if no.dir is None:
                return no.esq
            # dois filhos: copia o sucessor e o remove da subárvore direita
            suc = no.dir
            while suc.esq is not None:
                suc = suc.esq
            no.chave, no.valor = suc.chave, suc.valor
            no.dir = self._remover_menor(no.dir)
            return self._balancear(no)
        self.metricas.comparar()
        if chave < no.chave:
            no.esq = self._remover(no.esq, chave)
        else:
            no.dir = self._remover(no.dir, chave)
        return self._balancear(no)

    def _remover_menor(self, no):
        if no.esq is None:
            return no.dir
        no.esq = self._remover_menor(no.esq)
        return self._balancear(no)

    # ---------------------------------------------------------- percursos
    def __iter__(self):
        pilha, no = [], self.raiz
        while pilha or no is not None:
            while no is not None:
                pilha.append(no)
                no = no.esq
            no = pilha.pop()
            yield no.chave, no.valor
            no = no.dir

    def altura(self):
        return _alt(self.raiz)

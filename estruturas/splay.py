"""Árvore binária afunilada (splay tree) bottom-up, com a modificação M1.

Armazena todos os produtos com chave = id (F2). Na versão clássica, após
cada acesso o nó acessado (ou o último nó visitado, numa busca sem
sucesso) é levado à raiz por rotações zig, zig-zig e zig-zag.

M1 — splay com limiar de acesso (requisitos.MD, seção 5), ligada com
`limiar=k` (k >= 2; None ou 1 = clássica):
- cada nó tem um contador de acessos; a busca incrementa o contador do nó
  encontrado e só afunila quando ele chega a k, zerando-o em seguida;
- abaixo do limiar, a busca é uma busca comum de BST, sem rotações;
- busca sem sucesso não afunila (nenhum produto foi acessado);
- inserção e remoção continuam clássicas.
Motivo: numa loja/acervo, uma visita isolada a um produto obscuro não
deveria reorganizar a árvore inteira e empurrar para baixo os produtos
realmente populares; só os acessados com frequência sobem para a raiz.

Tudo é iterativo: uma splay pode ficar degenerada (profundidade O(n)) e o
limite de recursão do Python (~1000) não comportaria percursos recursivos.

Para a visualização (F6), cada operação guarda em `ultimo_caminho` as
chaves visitadas na descida e em `ultimas_rotacoes` os passos do splay.
"""

from .metricas import Metricas


class NoSplay:
    __slots__ = ("chave", "valor", "esq", "dir", "pai", "acessos")

    def __init__(self, chave, valor, pai=None):
        self.chave = chave
        self.valor = valor
        self.esq = None
        self.dir = None
        self.pai = pai
        self.acessos = 0  # M1: acessos desde o último splay deste nó


class SplayTree:
    def __init__(self, metricas=None, limiar=None):
        self.raiz = None
        self._tamanho = 0
        self.metricas = metricas if metricas is not None else Metricas()
        self.limiar = limiar  # M1: None/1 = splay clássica
        self.ultimo_caminho = []
        self.ultimas_rotacoes = []
        self.ultimo_afunilou = False
        self.ultimo_contador = None  # M1: contador do nó após a última busca

    @property
    def m1_ligada(self):
        return self.limiar is not None and self.limiar > 1

    def __len__(self):
        return self._tamanho

    def __contains__(self, chave):
        """Teste de pertinência SEM afunilar (não altera a árvore)."""
        no = self.raiz
        while no is not None:
            if chave == no.chave:
                return True
            no = no.esq if chave < no.chave else no.dir
        return False

    # ------------------------------------------------------------ rotações
    def _rotacionar(self, x):
        """Rotação simples que sobe x um nível (x é filho de p)."""
        p = x.pai
        g = p.pai
        if x is p.esq:
            p.esq = x.dir
            if x.dir is not None:
                x.dir.pai = p
            x.dir = p
        else:
            p.dir = x.esq
            if x.esq is not None:
                x.esq.pai = p
            x.esq = p
        p.pai = x
        x.pai = g
        if g is None:
            self.raiz = x
        elif g.esq is p:
            g.esq = x
        else:
            g.dir = x
        self.metricas.rotacionar()

    def _afunilar(self, x):
        """Leva x até a raiz (splay clássico)."""
        while x.pai is not None:
            p = x.pai
            g = p.pai
            if g is None:
                self.ultimas_rotacoes.append(("zig", x.chave))
                self._rotacionar(x)
            elif (x is p.esq) == (p is g.esq):
                self.ultimas_rotacoes.append(("zig-zig", x.chave))
                self._rotacionar(p)
                self._rotacionar(x)
            else:
                self.ultimas_rotacoes.append(("zig-zag", x.chave))
                self._rotacionar(x)
                self._rotacionar(x)

    # -------------------------------------------------------------- busca
    def _descer(self, chave):
        """Desce a partir da raiz. Devolve (nó com a chave ou None, último nó visitado)."""
        self.ultimo_caminho = []
        self.ultimas_rotacoes = []
        no, ultimo = self.raiz, None
        while no is not None:
            ultimo = no
            self.ultimo_caminho.append(no.chave)
            self.metricas.comparar()
            if chave == no.chave:
                return no, no
            self.metricas.comparar()
            no = no.esq if chave < no.chave else no.dir
        return None, ultimo

    def buscar(self, chave):
        """Devolve o valor associado à chave (ou None) e afunila (ver M1)."""
        self.metricas.registrar_operacao()
        achado, ultimo = self._descer(chave)
        self.metricas.registrar_profundidade(len(self.ultimo_caminho) - 1)
        self.ultimo_afunilou = False
        self.ultimo_contador = None
        if not self.m1_ligada:
            # clássica: afunila o nó encontrado ou o último visitado
            if ultimo is not None:
                self._afunilar(ultimo)
                self.ultimo_afunilou = True
        elif achado is not None:
            # M1 (modificação): só afunila quando o contador atinge o limiar k.
            # No algoritmo clássico o splay acontece incondicionalmente aqui.
            achado.acessos += 1
            if achado.acessos >= self.limiar:
                achado.acessos = 0
                self._afunilar(achado)
                self.ultimo_afunilou = True
            self.ultimo_contador = achado.acessos
        # M1 com busca sem sucesso: não afunila (nenhum produto foi acessado)
        return achado.valor if achado is not None else None

    def inserir(self, chave, valor):
        """Insere (ou atualiza) e afunila o nó. Devolve True se inseriu."""
        self.metricas.registrar_operacao()
        achado, ultimo = self._descer(chave)
        if achado is not None:
            achado.valor = valor
            self._afunilar(achado)
            return False
        novo = NoSplay(chave, valor, ultimo)
        if ultimo is None:
            self.raiz = novo
        elif chave < ultimo.chave:
            ultimo.esq = novo
        else:
            ultimo.dir = novo
        self._tamanho += 1
        self._afunilar(novo)
        return True

    def remover(self, chave):
        """Remove a chave. Devolve True se removeu."""
        self.metricas.registrar_operacao()
        achado, ultimo = self._descer(chave)
        if ultimo is not None:
            self._afunilar(ultimo)
        if achado is None:
            return False
        # achado está na raiz: junta as subárvores esquerda e direita.
        esq, dir_ = achado.esq, achado.dir
        if esq is None:
            self.raiz = dir_
            if dir_ is not None:
                dir_.pai = None
        else:
            esq.pai = None
            self.raiz = esq
            maior = esq
            while maior.dir is not None:
                maior = maior.dir
            self._afunilar(maior)  # maior da esquerda vira raiz, sem filho direito
            maior.dir = dir_
            if dir_ is not None:
                dir_.pai = maior
        self._tamanho -= 1
        return True

    # ---------------------------------------------------------- percursos
    def __iter__(self):
        """Percurso em ordem (iterativo): (chave, valor)."""
        pilha, no = [], self.raiz
        while pilha or no is not None:
            while no is not None:
                pilha.append(no)
                no = no.esq
            no = pilha.pop()
            yield no.chave, no.valor
            no = no.dir

    def altura(self):
        """Altura da árvore (árvore vazia = -1, só raiz = 0)."""
        if self.raiz is None:
            return -1
        maior, pilha = 0, [(self.raiz, 0)]
        while pilha:
            no, prof = pilha.pop()
            if prof > maior:
                maior = prof
            if no.esq is not None:
                pilha.append((no.esq, prof + 1))
            if no.dir is not None:
                pilha.append((no.dir, prof + 1))
        return maior

    def profundidade(self, chave):
        """Profundidade da chave sem afunilar (-1 se ausente)."""
        no, prof = self.raiz, 0
        while no is not None:
            if chave == no.chave:
                return prof
            no = no.esq if chave < no.chave else no.dir
            prof += 1
        return -1

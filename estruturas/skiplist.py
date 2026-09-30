"""Lista com saltos (skip list), com a modificação M3.

Guarda referências aos produtos com chave composta (year, id): a linha do
tempo (F3) usa o ano e o id desempata, deixando cada chave única.

O nível de cada nó é sorteado com moeda (p = 1/2), limitado a MAX_NIVEL.
O vetor `prox` de cada nó é o arranjo de ponteiros de avanço (um por
nível), a representação clássica da estrutura.

M3 — nível pela popularidade (requisitos.MD, seção 5), ligada com
`popularidade=True`:
- o nível inicial continua sorteado com moeda;
- cada busca bem-sucedida incrementa o contador do nó e calcula
  nivel_alvo = min(max_nivel, 1 + floor(log2(1 + acessos)));
- se nivel_alvo > nível atual, o nó é PROMOVIDO: é encadeado nos níveis
  novos usando os predecessores que a própria busca já encontrou, sem
  remover e reinserir; o nível nunca diminui.
Motivo: produtos populares ganham "vias expressas" e passam a ser
alcançados com menos comparações, enquanto o resto da lista mantém a
distribuição probabilística clássica.
"""

import random

from .metricas import Metricas

MAX_NIVEL = 20  # 2^20 ≈ 1 milhão; folga para ~44 mil produtos
P = 0.5


def nivel_por_popularidade(acessos, max_nivel=MAX_NIVEL):
    """M3: 1 + floor(log2(1 + acessos)), limitado a max_nivel."""
    nivel, n = 1, 1 + acessos
    while n >= 2 and nivel < max_nivel:  # floor(log2) sem ponto flutuante
        n //= 2
        nivel += 1
    return nivel


class NoSkip:
    __slots__ = ("chave", "valor", "prox", "acessos")

    def __init__(self, chave, valor, nivel):
        self.chave = chave
        self.valor = valor
        self.prox = [None] * nivel  # prox[i] = sucessor no nível i
        self.acessos = 0  # M3: buscas bem-sucedidas por este nó

    @property
    def nivel(self):
        return len(self.prox)


class SkipList:
    def __init__(self, metricas=None, rng=None, max_nivel=MAX_NIVEL, popularidade=False):
        self.max_nivel = max_nivel
        self.cabeca = NoSkip(None, None, max_nivel)
        self.nivel = 1  # quantidade de níveis em uso
        self._tamanho = 0
        self.metricas = metricas if metricas is not None else Metricas()
        self.rng = rng if rng is not None else random.Random()
        self.popularidade = popularidade  # M3: False = skip list clássica
        self.promocoes = 0  # M3: quantas promoções de nível já ocorreram
        self.ultimo_caminho = []  # (nível, chave) visitados na última busca
        self.ultima_promocao = None  # M3: (nível antes, nível depois) ou None

    def __len__(self):
        return self._tamanho

    def _sortear_nivel(self):
        nivel = 1
        while nivel < self.max_nivel and self.rng.random() < P:
            nivel += 1
        return nivel

    def _predecessores(self, chave):
        """Para cada nível, o último nó com chave < chave."""
        self.ultimo_caminho = []
        atualizar = [self.cabeca] * self.max_nivel
        no = self.cabeca
        for i in range(self.nivel - 1, -1, -1):
            while no.prox[i] is not None:
                self.metricas.comparar()
                if no.prox[i].chave < chave:
                    no = no.prox[i]
                    self.ultimo_caminho.append((i, no.chave))
                else:
                    break
            atualizar[i] = no
        return atualizar

    def buscar(self, chave):
        """Busca com parada antecipada: termina no nível em que achar a chave.

        (Inserção e remoção precisam dos predecessores em todos os níveis e
        descem até a base; a busca não.) A parada antecipada vale nas duas
        versões; é ela que faz um nó em nível alto ser achado mais cedo.
        """
        self.metricas.registrar_operacao()
        self.ultima_promocao = None
        self.ultimo_caminho = []
        atualizar = [self.cabeca] * self.max_nivel
        no = self.cabeca
        for i in range(self.nivel - 1, -1, -1):
            while no.prox[i] is not None:
                seguinte = no.prox[i]
                self.metricas.comparar()
                if seguinte.chave < chave:
                    no = seguinte
                    self.ultimo_caminho.append((i, no.chave))
                    continue
                self.metricas.comparar()
                if seguinte.chave == chave:
                    self.metricas.registrar_profundidade(len(self.ultimo_caminho))
                    seguinte.acessos += 1
                    if self.popularidade:
                        # atualizar[j] está pronto para todo j > i, e o nó
                        # só existe até o nível i: os níveis a promover são > i.
                        self._promover(seguinte, atualizar)
                    return seguinte.valor
                break
            atualizar[i] = no
        self.metricas.registrar_profundidade(len(self.ultimo_caminho))
        return None

    def _promover(self, no, atualizar):
        """M3 (modificação): sobe o nó ao nível dado pela sua popularidade.

        Na skip list clássica o nível é fixado na inserção e nunca muda.
        Aqui, os níveis novos são encadeados logo após os predecessores
        `atualizar[i]` já calculados pela busca: em cada nível i ainda sem o
        nó, atualizar[i] é o último nó com chave menor, então o nó entra
        entre ele e seu sucessor — sem remoção e reinserção.
        """
        alvo = nivel_por_popularidade(no.acessos, self.max_nivel)
        antes = no.nivel
        if alvo <= antes:
            return
        for i in range(antes, alvo):
            # níveis acima de self.nivel têm a cabeça como predecessor
            # (atualizar é inicializado com a cabeça em todos os níveis)
            no.prox.append(atualizar[i].prox[i])
            atualizar[i].prox[i] = no
        if alvo > self.nivel:
            self.nivel = alvo
        self.promocoes += 1
        self.ultima_promocao = (antes, alvo)

    def inserir(self, chave, valor):
        """Insere (ou atualiza). Devolve True se inseriu."""
        self.metricas.registrar_operacao()
        atualizar = self._predecessores(chave)
        cand = atualizar[0].prox[0]
        if cand is not None:
            self.metricas.comparar()
            if cand.chave == chave:
                cand.valor = valor
                return False
        nivel = self._sortear_nivel()
        if nivel > self.nivel:
            # níveis novos: o predecessor é a cabeça (já preenchido em atualizar)
            self.nivel = nivel
        novo = NoSkip(chave, valor, nivel)
        for i in range(nivel):
            novo.prox[i] = atualizar[i].prox[i]
            atualizar[i].prox[i] = novo
        self._tamanho += 1
        return True

    def remover(self, chave):
        self.metricas.registrar_operacao()
        atualizar = self._predecessores(chave)
        alvo = atualizar[0].prox[0]
        if alvo is None:
            return False
        self.metricas.comparar()
        if alvo.chave != chave:
            return False
        for i in range(alvo.nivel):
            atualizar[i].prox[i] = alvo.prox[i]
        while self.nivel > 1 and self.cabeca.prox[self.nivel - 1] is None:
            self.nivel -= 1
        self._tamanho -= 1
        return True

    # ------------------------------------------------- linha do tempo (F3)
    def intervalo(self, minimo, maximo):
        """Gera (chave, valor) com minimo <= chave <= maximo, em ordem.

        Para filtrar por ano com chave (year, id), use por exemplo
        minimo=(2012,) e maximo=(2015, float("inf")).
        """
        self.metricas.registrar_operacao()
        no = self._predecessores(minimo)[0].prox[0]
        while no is not None:
            self.metricas.comparar()
            if no.chave > maximo:
                break
            yield no.chave, no.valor
            no = no.prox[0]

    def pagina(self, minimo, maximo, numero, tamanho):
        """Página `numero` (0, 1, ...) do intervalo, com `tamanho` itens."""
        pular = numero * tamanho
        saida = []
        for item in self.intervalo(minimo, maximo):
            if pular > 0:
                pular -= 1
                continue
            saida.append(item)
            if len(saida) == tamanho:
                break
        return saida

    def contar_intervalo(self, minimo, maximo):
        n = 0
        for _ in self.intervalo(minimo, maximo):
            n += 1
        return n

    def __iter__(self):
        no = self.cabeca.prox[0]
        while no is not None:
            yield no.chave, no.valor
            no = no.prox[0]

    def nivel_de(self, chave):
        """Nível do nó com a chave (0 se ausente), sem contar métricas."""
        no = self.cabeca
        for i in range(self.nivel - 1, -1, -1):
            while no.prox[i] is not None and no.prox[i].chave < chave:
                no = no.prox[i]
            if no.prox[i] is not None and no.prox[i].chave == chave:
                return no.prox[i].nivel
        return 0

    def tamanho_niveis(self):
        """Quantos nós há em cada nível (0 = base)."""
        saida = []
        for i in range(self.nivel):
            n, no = 0, self.cabeca.prox[i]
            while no is not None:
                n += 1
                no = no.prox[i]
            saida.append(n)
        return saida

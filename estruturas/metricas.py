"""Instrumentação compartilhada pelas estruturas (requisitos I1 e I2)."""


class Metricas:
    """Contadores de uma estrutura.

    - comparacoes: comparações de chave (I1)
    - rotacoes: rotações em árvores (I1)
    - operacoes: quantas operações foram contadas
    - profundidades: profundidade de cada acesso, na ordem em que ocorreram (I2)
    """

    def __init__(self):
        self.zerar()

    def zerar(self):
        self.comparacoes = 0
        self.rotacoes = 0
        self.operacoes = 0
        self.profundidades = []

    def comparar(self, n=1):
        self.comparacoes += n

    def rotacionar(self, n=1):
        self.rotacoes += n

    def registrar_operacao(self):
        self.operacoes += 1

    def registrar_profundidade(self, profundidade):
        self.profundidades.append(profundidade)

    def media_comparacoes(self):
        return self.comparacoes / self.operacoes if self.operacoes else 0.0

    def resumo(self):
        return {
            "operacoes": self.operacoes,
            "comparacoes": self.comparacoes,
            "rotacoes": self.rotacoes,
            "media_comparacoes": self.media_comparacoes(),
        }

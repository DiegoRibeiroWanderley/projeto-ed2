"""Gera os gráficos e a tabela de métricas para a apresentação (I3, I4).

Uso: python -m app.relatorio_metricas [pasta_do_dataset] [pasta_saida]
Padrões: raiz do projeto e relatorio/. Grava PNGs e resumo.md.
"""

import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from app.simulacao import gerar_sequencia, media_por_bloco, simular  # noqa: E402
from dados.carregador import carregar  # noqa: E402

CORES = {"Splay clássica": "#5b7fa6", "AVL": "#8c8c8c", "Skip list clássica": "#5b7fa6",
         "Skip list M3": "#e8684a", "Lista com transposição": "#e8684a",
         "Lista sem autoajuste": "#8c8c8c"}
COR_M1 = "#e8684a"
N_ACESSOS, N_POPULARES, K = 20000, 500, 3


def cor(nome):
    return CORES.get(nome, COR_M1)


def salvar(fig, pasta, nome):
    caminho = os.path.join(pasta, nome)
    fig.tight_layout()
    fig.savefig(caminho, dpi=150)
    plt.close(fig)
    print("  ", caminho)


def grafico_series(series, atributo, titulo, rotulo_y, pasta, nome, mudanca=False):
    fig, ax = plt.subplots(figsize=(8, 4))
    for s in series:
        valores = media_por_bloco(getattr(s, atributo), 50)
        passo = N_ACESSOS / len(valores)
        ax.plot([i * passo for i in range(len(valores))], valores, label=s.nome, color=cor(s.nome),
                linewidth=2)
    if mudanca:
        ax.axvline(N_ACESSOS / 2, color="#999", linestyle="--", linewidth=1)
        ax.annotate(" troca dos populares", (N_ACESSOS / 2, 0.02), xycoords=("data", "axes fraction"),
                    color="#666", fontsize=8)
    ax.set_title(titulo)
    ax.set_xlabel("acessos")
    ax.set_ylabel(rotulo_y)
    ax.grid(alpha=0.3)
    ax.legend()
    salvar(fig, pasta, nome)


def main():
    pasta_dataset = sys.argv[1] if len(sys.argv) > 1 else "."
    saida = sys.argv[2] if len(sys.argv) > 2 else "relatorio"
    os.makedirs(saida, exist_ok=True)
    produtos, _ = carregar(pasta_dataset)
    print(f"{len(produtos)} produtos carregados; simulando {N_ACESSOS} acessos...")

    # 1. cenário principal: Zipf com ruído e troca dos populares no meio
    seq = gerar_sequencia(produtos, N_ACESSOS, N_POPULARES, s=1.0, ruido=0.2, mudanca=True)
    r = simular(produtos, seq, k=K)
    grafico_series(r.arvores, "profundidade", "Profundidade do acesso ao longo do tempo (I2)",
                   "profundidade média", saida, "1_profundidade_arvores.png", mudanca=True)
    grafico_series(r.arvores[:2], "rotacoes", "Rotações por acesso: splay clássica × M1",
                   "rotações", saida, "2_rotacoes_splay.png", mudanca=True)
    grafico_series(r.skips, "comparacoes", "Comparações por busca: skip list clássica × M3",
                   "comparações", saida, "3_comparacoes_skip.png", mudanca=True)
    grafico_series(r.ranking["series"], "comparacoes",
                   "Custo da busca sequencial no ranking", "comparações", saida,
                   "4_comparacoes_ranking.png", mudanca=True)

    # 5. nível dos produtos mais acessados na skip list ao final
    fig, ax = plt.subplots(figsize=(8, 4))
    maior = max(max(v) for v in r.niveis_populares.values())
    largura = 0.4
    for j, (nome, niveis) in enumerate(r.niveis_populares.items()):
        contagem = [sum(1 for n in niveis if n == nv) for nv in range(1, maior + 1)]
        media = sum(niveis) / len(niveis)
        ax.bar([nv + (j - 0.5) * largura for nv in range(1, maior + 1)], contagem, largura,
               label=f"{nome} (nível médio {media:.1f})", color=cor(nome))
    ax.set_xticks(range(1, maior + 1))
    ax.set_title(f"Nível dos 50 produtos mais acessados na skip list ({r.promocoes} promoções por M3)")
    ax.set_xlabel("nível do nó")
    ax.set_ylabel("produtos")
    ax.legend()
    salvar(fig, saida, "5_niveis_populares_skip.png")

    # 6. varredura do limiar k da M1 (cenário sem troca)
    seq_k = gerar_sequencia(produtos, N_ACESSOS, N_POPULARES, s=1.0, ruido=0.2, semente=1)
    ks, comp, rot = [1, 2, 3, 4, 5, 7, 10], [], []
    for k in ks:
        m1 = simular(produtos, seq_k, k=k).arvores[1]
        comp.append(m1.media(m1.comparacoes))
        rot.append(m1.media(m1.rotacoes))
        print(f"   k={k}: {comp[-1]:.1f} comparações, {rot[-1]:.2f} rotações por acesso")
    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(ks, comp, "o-", color="#5b7fa6", label="comparações/acesso")
    ax1.set_xlabel("limiar k da M1 (k = 1: splay clássica)")
    ax1.set_ylabel("comparações/acesso", color="#5b7fa6")
    ax2 = ax1.twinx()
    ax2.plot(ks, rot, "s-", color=COR_M1, label="rotações/acesso")
    ax2.set_ylabel("rotações/acesso", color=COR_M1)
    ax1.set_title("Efeito do limiar k da M1")
    ax1.grid(alpha=0.3)
    salvar(fig, saida, "6_varredura_k.png")

    # tabela-resumo
    linhas = ["# Métricas da simulação", "",
              f"{N_ACESSOS} acessos, {N_POPULARES} produtos populares (Zipf s=1), 20% de visitas "
              "isoladas, troca dos populares na metade. M1 com k = 3.", "",
              "| variante | comparações/acesso | profundidade média | rotações/acesso | tempo (s) |",
              "|---|---|---|---|---|"]
    for t in r.tabela():
        v = {c: ("—" if t[c] is None else t[c]) for c in t}
        linhas.append(f"| {v['variante']} | {v['comparações/acesso']} | {v['profundidade média']} | "
                      f"{v['rotações/acesso']} | {v['tempo (s)']} |")
    niv = {n: sum(v) / len(v) for n, v in r.niveis_populares.items()}
    linhas += ["", "Na skip list, profundidade = nós visitados antes de achar a chave. Buscas na "
               "AVL não fazem rotações (só inserção/remoção).", "",
               f"Promoções da M3: {r.promocoes}. Nível médio dos 50 mais acessados: "
               + ", ".join(f"{n} {m:.1f}" for n, m in niv.items()) + ".",
               f"Ranking (transposição): {r.ranking['precisao']:.0%} do top-10 real no top-10 da lista "
               f"({r.ranking['tamanho']} produtos distintos visualizados).", "",
               "Varredura do k da M1 (sem troca dos populares):", "",
               "| k | comparações/acesso | rotações/acesso |", "|---|---|---|"]
    linhas += [f"| {k} | {c:.2f} | {x:.2f} |" for k, c, x in zip(ks, comp, rot)]
    with open(os.path.join(saida, "resumo.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
    print("  ", os.path.join(saida, "resumo.md"))


if __name__ == "__main__":
    main()

"""Interface de linha de comando para F1–F5 (Fase 2).

Uso: python -m app.cli [pasta_do_dataset]
A pasta deve conter styles.csv e images/ (padrão: diretório atual).
"""

import sys

from dados.catalogo import Catalogo


def mostrar_produto(p):
    print(f"\n  [{p.id}] {p.nome}")
    print(f"  Marca: {p.marca} | Ano: {p.ano or '—'} | {p.genero} | {p.categoria} > "
          f"{p.subcategoria} > {p.tipo}")
    print(f"  Cor: {p.cor or '—'} | Estação: {p.estacao or '—'} | Uso: {p.uso or '—'}")
    print(f"  Imagem: {p.imagem or '(sem imagem)'}")


def listar(produtos):
    if not produtos:
        print("  (nenhum resultado)")
    for p in produtos:
        print(f"  [{p.id:>5}] {p.ano or '----'}  {p.nome}")


def ler_int(msg, padrao=None):
    txt = input(msg).strip()
    if not txt and padrao is not None:
        return padrao
    return int(txt) if txt.lstrip("-").isdigit() else None


def opcao_abrir(cat):
    pid = ler_int("  id do produto: ")
    p = cat.abrir(pid) if pid is not None else None
    if p is None:
        print("  produto não encontrado")
        return
    mostrar_produto(p)
    s = cat.splay
    print(f"  splay: caminho {len(s.ultimo_caminho)} nós, rotações {s.ultimas_rotacoes[:5]}"
          f"{' ...' if len(s.ultimas_rotacoes) > 5 else ''}; raiz agora = {s.raiz.chave}")


def opcao_linha_do_tempo(cat):
    print(f"  anos disponíveis: {cat.anos[0]}–{cat.anos[-1]}")
    ini = ler_int("  ano inicial: ", cat.anos[0])
    fim = ler_int("  ano final: ", cat.anos[-1])
    total = cat.total_no_intervalo(ini, fim)
    tamanho, pagina = 15, 0
    while True:
        print(f"\n  {ini}–{fim}: {total} produtos — página {pagina + 1}/{max(1, -(-total // tamanho))}")
        listar(cat.linha_do_tempo(ini, fim, pagina, tamanho))
        cmd = input("  [n] próxima, [p] anterior, [enter] sair: ").strip().lower()
        if cmd == "n" and (pagina + 1) * tamanho < total:
            pagina += 1
        elif cmd == "p" and pagina > 0:
            pagina -= 1
        elif cmd not in ("n", "p"):
            return


def opcao_ranking(cat):
    top = cat.mais_populares(15)
    if not top:
        print("  nenhum produto visualizado ainda")
    for i, (p, acessos) in enumerate(top, 1):
        print(f"  {i:>2}. [{p.id:>5}] {acessos:>3} acessos  {p.nome}")


def opcao_marcas(cat):
    prefixo = input("  prefixo da marca (enter = todas): ").strip()
    marcas = cat.buscar_marcas(prefixo) if prefixo else cat.listar_marcas(0, 30)
    for marca, n in marcas:
        print(f"  {marca:<35} {n:>5} produtos")
    escolha = input("  ver produtos de qual marca? (enter = voltar): ").strip()
    if escolha:
        listar(cat.produtos_da_marca(escolha)[:30])


def opcao_nome(cat):
    listar(cat.buscar_nome(input("  início do nome: ")))


MENU = [
    ("Abrir produto por id (splay)", opcao_abrir),
    ("Linha do tempo por ano (skip list)", opcao_linha_do_tempo),
    ("Mais populares (lista com transposição)", opcao_ranking),
    ("Marcas (tabela ordenada)", opcao_marcas),
    ("Buscar por nome (tabela ordenada)", opcao_nome),
]


def main():
    pasta = sys.argv[1] if len(sys.argv) > 1 else "."
    print("Carregando dataset...")
    cat = Catalogo.do_dataset(pasta)
    print(cat.relatorio.texto())
    print(f"Estruturas montadas em {cat.tempo_montagem:.1f}s ({len(cat)} produtos)")
    while True:
        print()
        for i, (texto, _) in enumerate(MENU, 1):
            print(f"{i}. {texto}")
        print("0. Sair")
        op = ler_int("> ")
        if op == 0:
            return
        if op is not None and 1 <= op <= len(MENU):
            try:
                MENU[op - 1][1](cat)
            except (EOFError, KeyboardInterrupt):
                print()


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        pass

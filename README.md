# Visualizador de Acervo Multimídia — Estrutura de Dados 2

Catálogo de ~44 mil produtos de moda em que splay tree, skip list, lista com
transposição e tabelas ordenadas (todas implementadas do zero) armazenam os
dados e oferecem as funcionalidades. Os requisitos e as decisões de projeto
estão em [`requisitos.MD`](requisitos.MD).

## Instalação

Passo a passo completo, do clone até o app rodando: [`instrucoes.md`](instrucoes.md).

Requer Python 3.10+.

```
pip install -r requirements.txt
```

## Dataset

Baixe o [Fashion Product Images (Small)](https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-small)
do Kaggle (login necessário) e descompacte na raiz do projeto, de modo que
fiquem `styles.csv` e `images/` lado a lado. O zip vem com uma cópia
idêntica em `myntradataset/`, que pode ser apagada.

Pela linha de comando (requer token da API em `~/.kaggle/kaggle.json`):

```
pip install kaggle
kaggle datasets download -d paramaggarwal/fashion-product-images-small --unzip
```

## Execução

```
streamlit run app/streamlit_app.py [-- pasta_do_dataset]   # interface (padrão: raiz do projeto)
python -m app.cli [pasta_do_dataset]                        # linha de comando
python -m app.relatorio_metricas [pasta_do_dataset]         # gráficos em relatorio/ (~1 min)
python -m pytest                                            # testes
```

Na interface, as modificações M1 e M3 são ligadas na barra lateral, e a página
"Simulação e métricas" roda a comparação clássica × modificada (F7, I1–I4).

## Organização

- `estruturas/` — uma estrutura por módulo, sem dependência da interface
- `dados/carregador.py` — leitura do CSV, tratamento de dados, extração de marca
- `dados/catalogo.py` — monta as estruturas e oferece as funcionalidades
- `app/` — interfaces (Streamlit e CLI), `visualizacao.py` (desenho das estruturas),
  `simulacao.py` (sequências Zipf e comparação) e `relatorio_metricas.py` (gráficos)
- `relatorio/` — gráficos e `resumo.md` para a apresentação (gerados por
  `python -m app.relatorio_metricas`; não versionados)
- `docs/` — texto do trabalho, roteiro da apresentação e roteiro do vídeo
- `tests/` — testes unitários e de invariantes

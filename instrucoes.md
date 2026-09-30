# Instruções: do clone até o app rodando

O repositório **não inclui o dataset**: são ~640 MB de imagens, e ele está no
`.gitignore`. Depois de clonar, é preciso instalar as dependências e baixar
o dataset do Kaggle.

## 1. Pré-requisitos

- **Python 3.10 ou mais recente.** Confira com `python --version`.
- **Conta no Kaggle**, gratuita, necessária para baixar o dataset.

## 2. Clonar e entrar na pasta

```
git clone <url-do-repositório>
cd projeto-ed2
```

Todos os comandos abaixo são executados **na raiz do projeto**, a pasta
onde está este arquivo.

## 3. Criar um ambiente virtual (recomendado)

**Windows (PowerShell):**
```
python -m venv .venv
.venv\Scripts\Activate.ps1
```
> Se aparecer um erro de "execução de scripts desabilitada", rode uma vez
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` e tente de novo.

**Linux / macOS:**
```
python3 -m venv .venv
source .venv/bin/activate
```

Com o ambiente ativo, o terminal mostra `(.venv)` no início da linha. Ative
o ambiente sempre que for trabalhar no projeto.

## 4. Instalar as dependências

```
pip install -r requirements.txt
```

Isso instala o Streamlit (interface), o matplotlib (gráficos do relatório)
e o pytest (testes). Todas as estruturas de dados são do próprio projeto,
então não há nenhuma outra biblioteca.

## 5. Baixar o dataset

Dataset: **Fashion Product Images (Small)**
https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-small

### Opção A: pelo navegador

1. Entre na sua conta do Kaggle, abra o link acima e clique em **Download**.
2. Descompacte o `.zip` **na raiz do projeto**.

### Opção B: pela linha de comando

1. No Kaggle, vá em *Settings → API → Create New Token*. Isso baixa um arquivo `kaggle.json`.
2. Coloque o `kaggle.json` em:
   - Windows: `C:\Users\<seu-usuário>\.kaggle\kaggle.json`
   - Linux/macOS: `~/.kaggle/kaggle.json`

   Não coloque esse arquivo dentro do projeto: é uma credencial sua.
3. Rode:
   ```
   pip install kaggle
   kaggle datasets download -d paramaggarwal/fashion-product-images-small --unzip
   ```

### Depois de descompactar

O zip traz o conteúdo **duplicado**: uma cópia na raiz e outra idêntica em
`myntradataset/`. Apague a pasta `myntradataset/`, porque só a cópia da
raiz é usada. A estrutura deve ficar assim:

```
projeto-ed2/
├── images/            ← 44.441 arquivos .jpg
├── styles.csv         ← ~4,3 MB
├── app/
├── dados/
├── estruturas/
├── tests/
├── requirements.txt
└── ...
```

> Se preferir guardar o dataset em outra pasta, veja a seção 8.

## 6. Conferir se está tudo certo

```
python -m pytest
```

Todos os testes devem passar, em cerca de 15 s. Dois deles usam o dataset
real:

- `test_dataset_real`: confere a leitura do `styles.csv`;
- `test_app_streamlit_navega_sem_erros`: abre o app e passa por todas as páginas.

Se aparecerem como **`skipped`**, o `styles.csv` não foi encontrado na raiz.
Volte ao passo 5.

## 7. Rodar

**Interface (principal):**
```
streamlit run app/streamlit_app.py
```
O navegador abre em http://localhost:8501. A primeira carga leva cerca de
3 s, para ler o CSV e montar as estruturas. Para encerrar, use **Ctrl+C**
no terminal.

**Linha de comando (versão simples, sem imagens):**
```
python -m app.cli
```

**Gráficos para a apresentação** (gravados em `relatorio/`, leva ~1 min):
```
python -m app.relatorio_metricas
```

## 8. Dataset em outra pasta

Se `styles.csv` e `images/` estiverem em outro lugar, informe o caminho:

```
streamlit run app/streamlit_app.py -- C:\caminho\para\o\dataset
python -m app.cli C:\caminho\para\o\dataset
python -m app.relatorio_metricas C:\caminho\para\o\dataset
```

Os dois hífens `--` no comando do Streamlit são necessários: eles separam
as opções do Streamlit das opções do app. Outra forma é definir a variável
de ambiente `ACERVO_DATASET` com o caminho.

## 9. Problemas comuns

| Sintoma | Causa provável e solução |
|---|---|
| `'streamlit' não é reconhecido como comando` | O ambiente virtual não está ativo. Ative-o (passo 3) ou use `python -m streamlit run app/streamlit_app.py`. |
| "Dataset não encontrado" no app, ou `FileNotFoundError: ... styles.csv` na linha de comando | O dataset não está na raiz do projeto. Confira o passo 5 ou passe o caminho (seção 8). |
| `ModuleNotFoundError: No module named 'estruturas'` | O comando foi rodado fora da raiz do projeto. Entre na pasta `projeto-ed2` e rode de novo. |
| Erro no app logo depois de um `git pull` (por exemplo, `AttributeError` em `visualizacao`) | O servidor manteve o código antigo em memória. Pare com **Ctrl+C** e rode `streamlit run` de novo; só recarregar o navegador não basta. |
| Produtos aparecem com "sem imagem" | A pasta `images/` está faltando ou fora da raiz. São esperados apenas 5 produtos sem imagem, que é o normal do dataset. |
| A porta 8501 já está em uso | Outro Streamlit está rodando. Feche-o ou use `streamlit run app/streamlit_app.py --server.port 8502`. |

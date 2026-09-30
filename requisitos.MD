# Requisitos do Projeto — Visualizador de Acervo Multimídia

Trabalho da disciplina **Estrutura de Dados 2**. Grupo de até 4 pessoas.

## 1. Objetivo

Criar uma aplicação para visualizar uma base de dados multimídia substancialmente grande (ex.: WikiArt), em que as estruturas de dados sejam usadas **tanto para armazenamento quanto para oferecer funcionalidades ao usuário**.

Exemplo dado pelo professor: uma loja on-line guarda produtos numa AVL (acesso rápido) e oferece um ranking de "mais vendidos" usando uma lista simples, sem ordenação, com transposição.

## 2. Regras obrigatórias (critérios de nota)

- **R1.** Só podem ser usadas estruturas vistas em aula:
  - Busca Sequencial (incluindo listas autoajustáveis: mover para frente e transposição)
  - Busca Linear em Tabela Ordenada (vetor ordenado, busca binária)
  - Lista com Saltos (Skip List)
  - Árvore Binária de Busca
  - Árvore AVL
  - Árvore Binária Afunilada (Splay Tree)
- **R2.** É obrigatório usar **Lista com Saltos ou Árvore Afunilada** (este projeto usa as duas).
- **R3.** É obrigatório usar **pelo menos uma estrutura linear e uma hierárquica**.
- **R4.** Estruturas sem modificação dos algoritmos clássicos → nota máxima 8,0.
- **R5.** Modificações nos algoritmos, adequadas à aplicação, implementadas **e explicadas** → nota máxima 10,0.

### Restrições de implementação

- Todas as estruturas devem ser **implementadas do zero** pelo grupo.
- Não usar estruturas prontas da linguagem para as funcionalidades principais (ex.: `dict`/`HashMap`, `set`, `sorted containers`, `heapq`, árvores de bibliotecas). Tabela hash, heap e grafos **não** foram vistos em aula.
- Listas/arrays nativos só como suporte básico (ex.: leitura do CSV, vetor da tabela ordenada).

## 3. Base de dados

**Decisão:** _Fashion Product Images Dataset_ (Kaggle), versão **small** (`paramaggarwal/fashion-product-images-small`): os mesmos ~44 mil produtos e o mesmo `styles.csv` da versão completa, com imagens em baixa resolução. O dataset tem poucas centenas de MB (a descrição da versão completa cita ~280 MB), enquanto a versão completa (`paramaggarwal/fashion-product-images-dataset`) tem ~25 GB. Conferir o tamanho e a resolução exatos no download.

- Metadados em `styles.csv`, colunas: `id, gender, masterCategory, subCategory, articleType, baseColour, season, year, usage, productDisplayName`.
- Imagem de cada produto em `images/{id}.jpg`.
- No restante deste documento, "obra" = **produto** e "artista" = **marca**.
- **Marca:** o dataset não tem essa coluna. A primeira palavra não serve, porque há marcas com várias palavras ("Peter England", "United Colors of Benetton"). A marca é extraída em 3 passos:
  1. Texto antes da palavra de gênero (`Men`, `Women`, `Boys`, `Girls`, `Unisex`, `Kids`, `Men's`, `Boy's`, `For Her`…): cobre ~40,9 mil produtos.
  2. Senão, o maior prefixo do nome que seja uma marca já conhecida do passo 1: ~3,4 mil.
  3. Senão, a primeira palavra: ~180.
  4. Normalização:
     - Se a marca obtida começa (ignorando maiúsculas) por uma marca conhecida com ≥ 5 produtos, é reduzida à **menor** delas. Os casos longos são quase sempre linhas de produto: "ADIDAS Originals" → "ADIDAS", "Jockey ZONE" → "Jockey", "Turtle Check" → "Turtle".
     - Exceção: marcas distintas listadas em `MARCAS_DISTINTAS` (hoje só "Lee Cooper", que não é linha da "Lee").
     - Variações de maiúsculas são unificadas na grafia mais frequente.

  Resultado: 487 marcas, das quais 56 com um único produto (resíduo aceito e documentado).

Inspeção do `styles.csv` (Fase 0, concluída):

- 44.446 linhas de dados. `id` é numérico, único e vai de 1163 a 60000.
- 22 linhas têm 11 colunas em vez de 10, porque o nome tem vírgula sem aspas.
- Vazios: `season` 21, `year` 1, `usage` 1 (`usage` também tem 316 valores `"NA"`). As demais colunas estão completas.
- `year` tem 13 valores (2007–2019) e é muito concentrado: 2011 e 2012 somam ~67% dos produtos.
- `productDisplayName` tem **13.302 nomes repetidos**, o que exige chave composta na tabela de nomes.
- 5 registros não têm imagem e 22 imagens não têm registro.
- 143 valores de `articleType` distintos.
- O zip do Kaggle vem duplicado (raiz + `myntradataset/`, conteúdos idênticos); só a cópia da raiz é usada.

Tratamento de dados (D4):

- O CSV é lido com o módulo `csv` (sem `pandas`).
- Linhas com mais de 10 colunas são **reparadas**: as colunas a partir da 10ª são reunidas com `,` para recompor o `productDisplayName`. Linhas com menos colunas são descartadas.
- Sem `id` numérico → descartado.
- Sem `year` → entra na splay e nos índices, mas **não** na skip list.
- `season`/`usage` vazios ou `"NA"` → exibidos como "—".
- Sem imagem no disco → exibe placeholder. Imagens sem registro são ignoradas.
- Tabela de nomes com chave `(nome normalizado, id)`, por causa dos nomes repetidos.
- A carga imprime a contagem de cada caso.

Requisitos da base:

- **D1.** Conter mídia (imagem, pôster, capa) para cada registro, ou link para ela.
- **D2.** Ter uma chave única por registro (ID ou título + artista).
- **D3.** Ter pelo menos um campo ordenável para a skip list (ano, data ou outro numérico). Se o dataset não tiver ano por obra, escolher outro campo ordenável.
- **D4.** Documentar o tratamento de dados ausentes (ex.: registros sem o campo-chave são descartados e a quantidade é informada).

## 4. Arquitetura das estruturas

| Estrutura               | Tipo                   | Armazena                                               | Funcionalidade oferecida                                                          |
| ----------------------- | ---------------------- | ------------------------------------------------------ | --------------------------------------------------------------------------------- |
| Árvore Afunilada        | Hierárquica            | Todos os produtos, chave = `id`                          | Busca/abertura de produto; acessados sobem para a raiz ("vistos recentemente")    |
| Lista com Saltos        | Linear                 | Referências aos produtos, chave composta `(year, id)`    | Linha do tempo por ano, filtro por intervalo, paginação                           |
| Lista com Transposição  | Linear (autoajustável) | Referências aos produtos já visualizados                 | Ranking de "mais populares"                                                       |
| Tabela Ordenada (vetor) | Linear                 | Marcas em ordem alfabética → lista encadeada de produtos | Índice de marcas com busca binária                                                |
| Tabela Ordenada (vetor) | Linear                 | Nomes normalizados (`productDisplayName`) → referência   | Busca por nome (binária + prefixo); abre o produto pela splay via `id`            |
| Árvore AVL (recomendada)| Hierárquica            | Mesmos produtos da splay                                 | Base de comparação de desempenho (I3)                                             |

As estruturas secundárias guardam **referências** ao registro do produto, não cópias.

Detalhes de projeto:

- **Splay iterativa.** O limite de recursão do Python (~1000) não comporta árvores degeneradas. A AVL pode ser recursiva, porque sua altura é no máximo ~1,44·log₂n (≈ 23 para 44 mil nós). Na carga, os produtos são inseridos em **ordem embaralhada**, porque inserir IDs crescentes numa splay gera uma árvore-lista.
- **Chave `(year, id)` na skip list.** `year` só tem ~12 valores distintos; desempatar pelo `id` deixa a chave única sem prejudicar o filtro por intervalo de ano (variante leve de M4).
- **Lista com transposição.** Contém apenas produtos já vistos: o 1º acesso insere no fim e os acessos seguintes fazem uma transposição com o anterior. O ranking é **aproximado**, porque não ordena por contagem; a interface mostra o contador ao lado para evidenciar isso.
- Listas de produtos por marca e a lista de ranking são **listas encadeadas próprias**.
- **Remoção** é implementada e testada em todas as estruturas, mesmo que a interface não a use.

## 5. Modificações algorítmicas (para nota 10)

Implementar pelo menos duas, cada uma com justificativa ligada à aplicação. **Escolhidas: M1 e M3** (M4 aparece na forma leve da chave `(year, id)`).

- **M1. Splay com limiar de acesso (ESCOLHIDA):** cada nó tem um contador de acessos. A busca desce como numa BST comum e incrementa o contador; o afunilamento só ocorre quando `contador >= k`, e então o contador volta a 0. `k` é configurável. Com M1 desligada (ou `k = 1`), a splay é a clássica. Evita que uma visita isolada reorganize a árvore.
- **M2. Semi-splay / splay com profundidade limitada:** o nó sobe apenas alguns níveis por acesso, deixando a árvore mais estável. _(não escolhida)_
- **M3. Skip list com nível pela popularidade (ESCOLHIDA):** o nível inicial é sorteado com moeda (clássico). A cada acesso, `nível_alvo = min(MAX_NIVEL, 1 + floor(log2(1 + acessos)))`. Se `nível_alvo > nível atual`, o nó é **promovido**: é encadeado nos níveis novos usando os predecessores encontrados na própria busca, sem remover e reinserir. Com M3 desligada, o nível fica o sorteado.
- **M4. Skip list com chave composta:** ordenar por ano e desempatar por outro campo. _(usada na forma `(year, id)`)_

Detalhes da implementação (Fase 4):

- **M1 vale só para as buscas.** Inserção e remoção continuam clássicas: se a carga não afunilasse, a árvore inicial seria uma BST aleatória e a comparação com a clássica ficaria injusta. Com M1 ligada, busca sem sucesso não afunila.
- **M3 conta aberturas de produto.** `Catalogo.abrir` registra a visualização também na skip list, buscando `(ano, id)`; é essa contagem que promove o nó.
- **Busca com parada antecipada na skip list.** A busca termina no nível em que encontra a chave; inserção e remoção continuam descendo até a base. Sem isso, a promoção do M3 não reduziria nada, porque a busca desceria até o nível 0 de qualquer jeito. Vale nas duas versões, para que a única diferença seja o nível dos nós.
- **Configuração.** As duas modificações ligam e desligam em execução (`Catalogo.configurar`, com controles na barra lateral do Streamlit). No código, os trechos alterados estão marcados com `M1 (modificação)` e `M3 (modificação)`.
- **Prévia (20 mil acessos Zipf sobre 2 mil produtos):**

  | Configuração | Comparações por busca | Rotações por acesso |
  | --- | --- | --- |
  | Splay clássica | 18,3 | 8,6 |
  | Splay com M1, k=2 | 18,2 | 4,3 |
  | Splay com M1, k=5 | 18,3 | 1,4 |
  | AVL | 28,6 | — |
  | Skip list clássica | 41,6 | — |
  | Skip list com M3 | 30,0 | — |

Cada modificação deve ser **configurável** (ligar/desligar), para comparar com a versão clássica na apresentação.

## 6. Requisitos funcionais

- **F1.** Carregar o dataset e montar todas as estruturas na inicialização.
- **F2.** Buscar e abrir uma obra (imagem + metadados) via splay tree.
- **F3.** Navegar pela linha do tempo e filtrar por intervalo via skip list, com paginação.
- **F4.** Exibir ranking de mais populares via lista com transposição, atualizado a cada visualização.
- **F5.** Listar marcas em ordem alfabética e buscar produtos por nome (prefixo) via tabelas ordenadas.
- **F6.** **Visualizar o estado das estruturas**: desenhar a splay tree (topo da árvore, primeiros níveis), os níveis da skip list e a ordem da lista de ranking. Destacar o caminho percorrido numa busca e as rotações ocorridas.
- **F7.** Modo de simulação: gerar uma sequência de acessos (ex.: distribuição com obras populares) para demonstrar o comportamento autoajustável.

## 7. Métricas e instrumentação

- **I1.** Contar comparações e rotações por operação em cada estrutura.
- **I2.** Registrar profundidade dos acessos na splay tree ao longo do tempo.
- **I3.** Comparar: splay clássica × splay modificada × AVL (se implementada); skip list clássica × com nível por popularidade.
- **I4.** Exibir essas métricas na interface ou gerar gráficos para a apresentação.

Implementação (Fase 5):

- `app/simulacao.py` gera a sequência de acessos (Zipf sobre N populares, fração de visitas isoladas e troca opcional dos populares na metade). A mesma sequência é aplicada a estruturas novas, montadas com a mesma ordem de inserção: splay clássica, splay M1, AVL, skip list clássica, skip list M3, lista com transposição e lista sem autoajuste.
- Na interface, a página "Simulação e métricas" mostra a tabela e os gráficos, aplica a sequência ao catálogo da sessão (F7) e exibe as métricas acumuladas do uso.
- `python -m app.relatorio_metricas` grava os gráficos e o `resumo.md` em `relatorio/`.
- Resultados (20 mil acessos, 500 populares, Zipf s=1, 20% de visitas isoladas, troca na metade):
  - **Árvores:** a splay clássica usa 21,2 comparações por acesso, contra 28,5 da AVL. A M1 com k=3 usa 20,3 comparações e faz 2,0 rotações por acesso, contra 10,1 da clássica. As visitas isoladas deixam de reorganizar a árvore.
  - **Skip list:** a M3 reduz as comparações de 42,4 para 33,2. O nível médio dos 50 produtos mais acessados sobe de 2,1 para 7,4.
  - **Ranking:** a transposição reduz pouco o custo da busca sequencial (1.547 contra 1.606 comparações) e acerta 50% do top-10 real. Ela sobe um passo por acesso, então converge devagar; é uma limitação conhecida e deve ser explicada.

## 8. Requisitos não funcionais

- **N1.** Linguagem e plataforma livres. **Decisão:** Python + Streamlit. As estruturas são montadas uma vez e ficam em `st.session_state`.
  - Bibliotecas só como suporte: `csv`, `random` (moeda da skip list e simulação Zipf), `graphviz`/SVG (desenho em F6), `matplotlib`/`altair` (gráficos em I4), `pytest` (N3). Nada disso pode substituir as estruturas próprias.
  - Organização: `estruturas/` (uma estrutura por módulo + `metricas.py`), `dados/carregador.py`, `app/` (Streamlit, visualização, simulação), `tests/`.
- **N2.** Código organizado com cada estrutura em seu próprio módulo, separada da interface.
- **N3.** Testes unitários para cada estrutura (inserção, busca, remoção, invariantes).
- **N4.** Visualizações legíveis: desenhar subconjuntos (20 a 50 nós); o conjunto completo é usado para métricas.
- **N5.** README com instruções de instalação, download do dataset e execução.

## 9. Entregáveis

- Texto curto descrevendo a aplicação e o processo de desenvolvimento (incluindo uso de LLMs).
- Apresentação focada na organização e nas estruturas de dados, preparada para perguntas.
- Vídeo da aplicação em execução.
- Código-fonte.

## 10. Plano de desenvolvimento sugerido

1. **Fase 0:** escolher dataset, inspecionar colunas, definir chaves e tratamento de nulos.
2. **Fase 1:** implementar e testar as estruturas clássicas (splay, skip list, lista com transposição, tabela ordenada).
3. **Fase 2:** carregar o dataset nas estruturas; funcionalidades F1 a F5 em linha de comando.
4. **Fase 3:** interface com imagens e visualização das estruturas (F6).
5. **Fase 4:** modificações M1 a M4, com chave liga/desliga.
6. **Fase 5:** instrumentação, simulação e comparações (F7, I1 a I4).
7. **Fase 6:** texto, slides e vídeo.

## 11. Instruções para o assistente de código

- Ler este arquivo antes de qualquer tarefa.
- Respeitar a seção 2: nunca substituir as estruturas próprias por estruturas prontas da linguagem.
- Implementar uma fase por vez e rodar os testes ao final de cada uma.
- Comentar no código onde cada modificação (M1 a M4) altera o algoritmo clássico.
- Perguntar antes de tomar as decisões marcadas como pendentes.

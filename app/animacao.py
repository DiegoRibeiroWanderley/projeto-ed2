"""Animação das buscas na splay tree e na skip list (F6).

Cada animação é uma página HTML independente (SVG + um pequeno player em
JavaScript), exibida com streamlit.components.v1.html. Os quadros são
calculados aqui, em Python, percorrendo os nós diretamente: nada é
afunilado nem promovido, e as métricas não mudam.

A busca é mostrada como um cursor que percorre a estrutura. A cada quadro
o cursor desliza até o próximo nó (transições CSS) e um balão mostra as
comparações feitas ali e o resultado. A "câmera" acompanha o cursor.

Um quadro é um dicionário:
- marcas: [[id, classe]] — acumulam: o quadro i é o estado inicial com as
  marcas dos quadros 0..i aplicadas (voltar um passo é remontar até i - 1);
- ex: ids destacados só neste quadro (o ponteiro e o nó sendo comparados);
- cur: [x, y] posição do cursor; balao: [html, x, y, lado] ou None;
- msg: texto do passo; comp: comparações acumuladas.

As comparações seguem as mesmas regras das estruturas, para bater com as
métricas mostradas na interface:
- splay: 1 comparação (==) no nó que tem a chave; 2 (== e <) nos demais;
- skip list: avançar custa 1 (<); achar ou descer por um nó maior custa 2
  (< e ==); descer porque o nível acabou não compara nada.
"""

import html
import json

from estruturas.tabela_ordenada import merge_sort

from .visualizacao import _nos_da_base_ate, narrar_busca_skip, rastro_skip

# Cores dos dois temas do Streamlit. "caminho" e "alvo" seguem os desenhos
# estáticos (amarelo = visitado, vermelho = encontrado).
TEMAS = {
    "dark": {
        "fundo": "#1a1d24", "borda": "#2f3540", "texto": "#e6e8eb", "fraco": "#8b95a3",
        "msg": "#232733", "no": "#273244", "no_borda": "#5b84b8", "aresta": "#3a4352",
        "caminho": "#f2c14e", "caminho_txt": "#1a1d24", "alvo": "#ff6b4a",
        "maior": "#a8455a", "cursor": "#4fd1c5", "balao": "#0f1218",
        "sim": "#3fb950", "nao": "#ff7b72", "botao": "#262b35", "esquema": "dark",
    },
    "light": {
        "fundo": "#ffffff", "borda": "#d9dee5", "texto": "#1f2933", "fraco": "#66717e",
        "msg": "#f3f5f8", "no": "#dbe7f5", "no_borda": "#5b7fa6", "aresta": "#c3ccd6",
        "caminho": "#f6c85f", "caminho_txt": "#1f2933", "alvo": "#e8684a",
        "maior": "#f0a39a", "cursor": "#0f9d8f", "balao": "#ffffff",
        "sim": "#1a7f37", "nao": "#cf222e", "botao": "#f5f7fa", "esquema": "light",
    },
}

# velocidade -> duração de um quadro (ms) ao animar; a segunda é a inicial
VELOCIDADES = [("0,5×", 3000), ("1×", 1500), ("2×", 750)]

# ícones dos controles, em traço fino (cor do texto, via currentColor)
_ICONES = {
    "ini": '<path d="M6 5v14M18 6l-9 6 9 6z"/>',
    "ant": '<path d="M15 6l-6 6 6 6"/>',
    "play": '<path d="M8 5.5v13l11-6.5z"/>',
    "pausa": '<path d="M8 5v14M16 5v14"/>',
    "prox": '<path d="M9 6l6 6-6 6"/>',
    "fim": '<path d="M18 5v14M6 6l9 6-9 6z"/>',
}


def _icone(nome):
    return (f'<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
            f'{_ICONES[nome]}</svg>')


def _tema(nome):
    return TEMAS.get(nome or "dark", TEMAS["dark"])


def _q(marcas, msg, comp, cur, balao=None, ex=()):
    return {"marcas": marcas, "ex": list(ex), "cur": cur, "balao": balao,
            "msg": msg, "comp": comp}


def _sim(texto="sim"):
    return f"<span class='sim'>{texto}</span>"


def _nao(texto="não"):
    return f"<span class='nao'>{texto}</span>"


def _negrito(texto):
    """Converte o **negrito** do markdown da narração em <b>, escapando o resto."""
    partes = html.escape(texto).split("**")
    return "".join(f"<b>{p}</b>" if i % 2 else p for i, p in enumerate(partes))


# ------------------------------------------------------------------ player
_CSS = """<style>
:root{--t:600ms;--atraso-cur:0ms;--atraso-balao:0ms;color-scheme:%(esquema)s}
body{margin:0;font:14px "Source Sans Pro","Source Sans 3",-apple-system,sans-serif;
  color:%(texto)s;background:transparent}
.painel{background:%(fundo)s;border:1px solid %(borda)s;border-radius:10px;padding:10px 12px}
.trilha{height:3px;background:%(borda)s;border-radius:2px;margin:10px 0 4px;cursor:pointer;
  position:relative}
.trilha::before{content:"";position:absolute;inset:-6px 0}
.feito{height:100%%;width:0;background:%(cursor)s;border-radius:2px;
  transition:width var(--t) ease-in-out}
.controles{display:flex;align-items:center;gap:2px}
.controles button{border:0;background:none;color:%(fraco)s;cursor:pointer;padding:4px 6px;
  border-radius:6px;display:flex;align-items:center;font:inherit;font-size:12px}
.controles button:hover{color:%(texto)s;background:%(msg)s}
.controles #play{color:%(cursor)s}
.controles #vel{min-width:34px;justify-content:center;font-variant-numeric:tabular-nums}
.controles .info{margin-left:auto;color:%(fraco)s;font-size:12px;white-space:nowrap;
  font-variant-numeric:tabular-nums}
.controles .info b{color:%(texto)s;font-weight:600}
.msg{min-height:22px;background:%(msg)s;border-left:4px solid %(cursor)s;padding:7px 10px;
  margin-bottom:8px;border-radius:4px;line-height:1.35}
.area{display:flex}
.palco{position:relative;overflow:auto;flex:1;max-height:%(altura)dpx;
  scrollbar-color:%(aresta)s transparent;scrollbar-width:thin}
.palco::-webkit-scrollbar{height:8px;width:8px}
.palco::-webkit-scrollbar-thumb{background:%(aresta)s;border-radius:4px}
.palco::-webkit-scrollbar-track,.palco::-webkit-scrollbar-corner{background:transparent}
.camada{position:relative;width:max-content}
.balao{position:absolute;z-index:3;background:%(balao)s;border:1.5px solid %(cursor)s;
  border-radius:8px;padding:5px 9px;white-space:nowrap;font-size:13px;line-height:1.45;
  box-shadow:0 4px 14px rgba(0,0,0,.35);pointer-events:none;opacity:0;
  transition:left var(--t) ease-in-out,top var(--t) ease-in-out}
.balao.e{transform:translate(-100%%,-50%%)}
.balao.d{transform:translate(0,-50%%)}
.balao.c{transform:translate(0,-100%%)}
.balao.mostra{animation:surge calc(var(--t) * .7) ease-out var(--atraso-balao) both}
@keyframes surge{from{opacity:0;margin-top:6px}to{opacity:1;margin-top:0}}
.sim{color:%(sim)s;font-weight:700}.nao{color:%(nao)s;font-weight:700}
.balao b{color:%(cursor)s}
svg text{fill:%(texto)s;font-family:inherit}
#cursor{transition:transform var(--t) ease-in-out var(--atraso-cur)}
.cursor{fill:none;stroke:%(cursor)s;stroke-width:3;filter:drop-shadow(0 0 5px %(cursor)s)}
.pulsa{animation:pulsa 1.1s ease-in-out infinite}
@keyframes pulsa{50%%{stroke-opacity:.35}}
.rev{opacity:0;transition:opacity var(--t)}.rev.on{opacity:1}
.seg{stroke-dasharray:1;stroke-dashoffset:1;transition:stroke-dashoffset var(--t) ease-in-out}
.seg.on{stroke-dashoffset:0}
</style>"""

_HTML = """<div class="painel">
<div class="msg" id="msg"></div>
<div class="area">%(fixo)s<div class="palco" id="palco"><div class="camada">%(svg)s
<div class="balao" id="balao"></div></div></div></div>
<div class="trilha" id="trilha" title="ir para um passo"><div class="feito" id="feito"></div></div>
<div class="controles">
<button id="ini" title="voltar ao início">%(i_ini)s</button>
<button id="ant" title="passo anterior">%(i_ant)s</button>
<button id="play" title="animar">%(i_play)s</button>
<button id="prox" title="próximo passo">%(i_prox)s</button>
<button id="fim" title="ir para o fim">%(i_fim)s</button>
<button id="vel" title="velocidade"></button>
<span class="info">passo <b id="passo">0</b>/%(total)s · <b id="comp">0</b> comparações</span>
</div></div>"""

_JS = """<script>
(function(){
const Q = %(quadros)s;
const ATRASO_CUR = %(atraso_cur)s, ATRASO_BALAO = %(atraso_balao)s, CAMERA_X = %(camera_x)s;
const VEL = %(velocidades)s, ICONE_PLAY = %(i_play_js)s, ICONE_PAUSA = %(i_pausa_js)s;
const $ = id => document.getElementById(id);
const base = {};  // classe inicial de cada elemento que algum quadro altera
for (const q of Q) for (const id of [...q.marcas.map(m => m[0]), ...q.ex]) {
  const el = $(id);
  if (el && !(id in base)) base[id] = el.getAttribute("class") || "";
}
const palco = $("palco"), balao = $("balao"), cursor = $("cursor"), play = $("play"),
      vel = $("vel");
let i = 0, timer = null, v = 1;

function duracao() { return VEL[v][1]; }
function ajustarTempo() {
  const d = duracao(), raiz = document.documentElement.style;
  raiz.setProperty("--t", Math.round(d * 0.45) + "ms");
  raiz.setProperty("--atraso-cur", Math.round(d * ATRASO_CUR) + "ms");
  raiz.setProperty("--atraso-balao", Math.round(d * ATRASO_BALAO) + "ms");
  vel.textContent = VEL[v][0];
}
function camera(x, y, suave) {
  palco.scrollTo({left: x - palco.clientWidth * CAMERA_X, top: y - palco.clientHeight / 2,
                  behavior: suave ? "smooth" : "auto"});
}
function mostrar(n, suave) {
  i = Math.max(0, Math.min(Q.length - 1, n));
  for (const id in base) $(id).setAttribute("class", base[id]);
  for (let k = 0; k <= i; k++) for (const [id, cls] of Q[k].marcas) {
    const el = $(id);
    if (el) el.setAttribute("class", cls);
  }
  const q = Q[i];
  for (const id of q.ex) { const el = $(id); if (el) el.classList.add("ex"); }
  if (q.cur && cursor) cursor.style.transform = `translate(${q.cur[0]}px, ${q.cur[1]}px)`;
  balao.classList.remove("mostra");
  if (q.balao) {
    const [conteudo, x, y, lado] = q.balao;
    balao.innerHTML = conteudo;
    balao.style.left = x + "px";
    balao.style.top = y + "px";
    balao.className = "balao " + lado;
    void balao.offsetWidth;  // reinicia a animação de entrada
    balao.classList.add("mostra");
  }
  $("msg").innerHTML = q.msg;
  $("passo").textContent = i;
  $("feito").style.width = (Q.length > 1 ? 100 * i / (Q.length - 1) : 100) + "%%";
  $("comp").textContent = q.comp;
  if (q.cur) camera(q.cur[0], q.cur[1], suave);
}
function parar() { clearInterval(timer); timer = null; play.innerHTML = ICONE_PLAY; play.title = "animar"; }
function animar() {
  if (timer) { parar(); return; }
  if (i >= Q.length - 1) mostrar(0, false);
  play.innerHTML = ICONE_PAUSA;
  play.title = "pausar";
  const passo = () => { if (i >= Q.length - 1) parar(); else mostrar(i + 1, true); };
  passo();
  timer = setInterval(passo, duracao());
}
$("ini").onclick = () => { parar(); mostrar(0, true); };
$("ant").onclick = () => { parar(); mostrar(i - 1, true); };
$("prox").onclick = () => { parar(); mostrar(i + 1, true); };
$("fim").onclick = () => { parar(); mostrar(Q.length - 1, true); };
play.onclick = animar;
vel.onclick = () => {
  v = (v + 1) %% VEL.length;
  ajustarTempo();
  if (timer) { parar(); animar(); }
};
$("trilha").onclick = ev => {  // clique na barra de progresso: vai para aquele passo
  const r = ev.currentTarget.getBoundingClientRect();
  parar();
  mostrar(Math.round((ev.clientX - r.left) / r.width * (Q.length - 1)), true);
};
ajustarTempo();
mostrar(0, false);
})();
</script>"""


def _pagina(tema, css_extra, svg, quadros, altura, atraso_cur, atraso_balao, fixo="",
            camera_x=0.5):
    """Página completa: estilos, controles, mensagem, palco e player.

    atraso_cur / atraso_balao: em que fração do quadro o cursor começa a se
    mover e o balão aparece (na splay o cursor chega e depois compara; na
    skip list compara e depois anda). camera_x: em que fração da largura do
    palco a câmera mantém o cursor.
    """
    cores = _tema(tema)
    icones = {f"i_{nome}": _icone(nome) for nome in _ICONES}
    return (_CSS % dict(cores, altura=altura) + css_extra % cores
            + _HTML % dict(icones, svg=svg, fixo=fixo, total=len(quadros) - 1)
            + _JS % {"quadros": json.dumps(quadros, ensure_ascii=False),
                     "atraso_cur": atraso_cur, "atraso_balao": atraso_balao,
                     "camera_x": camera_x, "velocidades": json.dumps(VELOCIDADES),
                     "i_play_js": json.dumps(icones["i_play"]),
                     "i_pausa_js": json.dumps(icones["i_pausa"])})


# ------------------------------------------------------------------- splay
DX, DY, RAIO = 52, 64, 21   # passo horizontal, distância entre níveis, raio do nó (px)
LATERAL = 230               # folga dos lados para os balões
PALCO_SPLAY = 470           # altura máxima do palco; caminhos maiores rolam
ALTURA_SPLAY = PALCO_SPLAY + 135  # altura do componente: palco + controles

_CSS_SPLAY = """<style>
svg text{text-anchor:middle;font-size:11px}
.no circle{fill:%(no)s;stroke:%(no_borda)s;stroke-width:1.5;
  transition:fill var(--t),stroke var(--t)}
.no.visitado circle{fill:%(caminho)s;stroke:%(caminho)s}
.no.visitado .rot{fill:%(caminho_txt)s;font-weight:600}
.no.achou circle{fill:%(alvo)s;stroke:%(alvo)s}
.no.achou .rot{fill:#fff;font-weight:700}
.seg{stroke:%(caminho)s;stroke-width:3.5;fill:none}
.trilho{stroke:%(aresta)s;stroke-width:1.5;fill:none;stroke-dasharray:3 4}
.irmao polygon{fill:none;stroke:%(aresta)s;stroke-width:1.5}
.irmao text{fill:%(fraco)s;font-size:10px}
.prof{fill:%(fraco)s;font-size:10px;text-anchor:start}
.nulo line{stroke:%(alvo)s;stroke-dasharray:4 3;stroke-width:2}
.nulo text{fill:%(alvo)s;font-weight:700}
</style>"""


def _caminho_nos(arvore, chave, max_nos):
    """Nós da raiz até a chave (ou até o último antes de um filho vazio), sem afunilar."""
    nos, no = [], arvore.raiz
    while no is not None and len(nos) < max_nos:
        nos.append(no)
        if chave == no.chave:
            break
        no = no.esq if chave < no.chave else no.dir
    return nos


def quadros_splay(arvore, chave, max_nos=200):
    """Desenho (SVG) e quadros da busca por chave na árvore, como ela está agora.

    Só o caminho é desenhado: cada nó aparece quando a busca chega nele, e o
    filho que ela não seguiu fica resumido num triângulo. Devolve
    (svg, quadros, altura em px).
    """
    nos = _caminho_nos(arvore, chave, max_nos)
    if not nos:
        return ("<svg width='300' height='40'><text x='150' y='25'>(árvore vazia)</text></svg>",
                [_q([], "A árvore está vazia.", 0, None)], 60)

    # posições: cada passo à esquerda/direita desloca DX; o irmão fica do outro lado
    xs = [0]
    for k in range(1, len(nos)):
        xs.append(xs[-1] + (-DX if nos[k] is nos[k - 1].esq else DX))
    n = len(nos)
    ultimo = nos[-1]
    achou = ultimo.chave == chave
    vazio_esq = chave < ultimo.chave  # lado do filho vazio, se a busca falhar
    # caminho cortado pelo limite de nós: a busca seguiria por um filho que existe
    cortado = not achou and (ultimo.esq if vazio_esq else ultimo.dir) is not None
    minx = min(xs) - DX
    largura = max(xs) + DX - minx + 2 * LATERAL
    altura = (n + 1) * DY + 40

    def px(k):
        return xs[k] - minx + LATERAL

    def py(k):
        return 34 + k * DY

    arestas, outros, circulos, irmaos = [], [], [], set()
    for k, no in enumerate(nos):
        if k + 1 < n:
            x, y, x2, y2 = px(k), py(k), px(k + 1), py(k + 1)
            arestas.append(f'<path id="e{k}" class="seg" pathLength="1" d="M{x},{y} L{x2},{y2}"/>')
            irmao = no.dir if nos[k + 1] is no.esq else no.esq
            xi = x + (DX if nos[k + 1] is no.esq else -DX)
            if irmao is not None:
                irmaos.add(k)
                outros.append(
                    f'<g id="s{k}" class="irmao rev"><path class="trilho" d="M{x},{y} '
                    f'L{xi},{y2 - 14}"/><polygon points="{xi},{y2 - 14} {xi - 15},{y2 + 12} '
                    f'{xi + 15},{y2 + 12}"/><text x="{xi}" y="{y2 + 25}">{irmao.chave}…</text></g>')
        circulos.append(
            f'<g id="n{k}" class="no rev"><circle cx="{px(k)}" cy="{py(k)}" r="{RAIO}"/>'
            f'<text class="rot" x="{px(k)}" y="{py(k) + 4}">{no.chave}</text>'
            f'<text class="prof" x="6" y="{py(k) + 4}">prof. {k}</text></g>')
    xv, yv = px(n - 1) + (-DX if vazio_esq else DX), py(n)
    if not achou and not cortado:  # filho vazio onde a chave estaria
        outros.append(f'<g id="nulo" class="nulo rev"><line x1="{px(n - 1)}" y1="{py(n - 1)}" '
                      f'x2="{xv}" y2="{yv - 12}"/><text x="{xv}" y="{yv + 4}">vazio</text></g>')
    cursor = (f'<g id="cursor" style="transform:translate({px(0)}px,{py(0)}px)">'
              f'<circle class="cursor pulsa" r="{RAIO + 7}"/></g>')
    svg = (f'<svg width="{largura}" height="{altura}" xmlns="http://www.w3.org/2000/svg">'
           + "".join(arestas + outros + circulos) + cursor + "</svg>")

    def balao(k, conteudo):
        # vai para o lado em que, nesta linha, não há o triângulo do irmão
        lado = "e" if k > 0 and nos[k] is nos[k - 1].esq else "d"
        x = px(k) + (-(RAIO + 14) if lado == "e" else RAIO + 14)
        return [conteudo, x, py(k), lado]

    c = html.escape(str(chave))
    quadros = [_q([["n0", "no rev on"]], f"Buscando a chave <b>{c}</b>. A busca começa na "
                  "raiz. Clique em ▶ animar ou avance passo a passo.", 0, [px(0), py(0)])]
    comp = 0
    for k, no in enumerate(nos):
        marcas = []
        if k > 0:  # chegou aqui vindo do pai: desenha a aresta e mostra o irmão
            marcas = [[f"n{k - 1}", "no rev on visitado"], [f"e{k - 1}", "seg on"]]
            if k - 1 in irmaos:
                marcas.append([f"s{k - 1}", "irmao rev on"])
        marcas.append([f"n{k}", "no rev on"])
        x = no.chave
        if x == chave:
            comp += 1
            marcas.append([f"n{k}", "no rev on achou"])
            quadros.append(_q(
                marcas, f"Profundidade {k}: {c} = {x} → <b>achou</b>, com {comp} comparações.",
                comp, [px(k), py(k)], balao(k, f"<b>{c}</b> = {x}? {_sim()}<br>achou!")))
            break
        comp += 2
        menor = chave < x
        lado = "esquerda" if menor else "direita"
        quadros.append(_q(
            marcas, f"Profundidade {k}: {c} ≠ {x} e {c} {'<' if menor else '>'} {x} "
                    f"→ desce à <b>{lado}</b>.", comp, [px(k), py(k)],
            balao(k, f"<b>{c}</b> = {x}? {_nao()}<br><b>{c}</b> &lt; {x}? "
                     f"{_sim() if menor else _nao()} → {lado}")))
    if cortado:
        quadros[-1]["msg"] += f" O desenho para aqui ({max_nos} nós); a busca continuaria descendo."
    elif not achou:
        lado = "esquerdo" if vazio_esq else "direito"
        quadros.append(_q(
            [[f"n{n - 1}", "no rev on visitado"], ["nulo", "nulo rev on"]],
            f"O filho {lado} de {ultimo.chave} está vazio: a chave <b>{c}</b> não está na árvore.",
            comp, [xv, yv],
            [f"{_nao('vazio')}: <b>{c}</b> não está na árvore",
             xv + (-24 if vazio_esq else 24), yv, "e" if vazio_esq else "d"]))
    return svg, quadros, altura


def html_busca_splay(arvore, chave, max_nos=200, nota_final=None, tema=None):
    """Página com a busca animada na splay; nota_final é acrescentada ao último quadro."""
    return pagina_splay(quadros_splay(arvore, chave, max_nos), nota_final, tema)


def pagina_splay(desenho, nota_final=None, tema=None):
    """Página a partir de um desenho já calculado por quadros_splay.

    Permite calcular os quadros antes de um acesso (com a árvore ainda
    intacta) e só montar a página depois, com uma nota sobre o splay.
    """
    svg, quadros, _ = desenho
    if nota_final:
        quadros[-1]["msg"] += " " + nota_final
    # o cursor chega primeiro e o balão com as comparações aparece depois
    return _pagina(tema, _CSS_SPLAY, svg, quadros, PALCO_SPLAY, 0, 0.45)


# --------------------------------------------------------------- skip list
CW, GW, RH, BH = 92, 60, 26, 20  # largura da coluna e do trecho pulado; altura da linha e da caixa
TORRE = 64                        # largura da caixa de cada nível
TOPO = 64                         # espaço acima da torre mais alta, para o balão

_CSS_SKIP = """<style>
svg text{text-anchor:middle;font-size:11px}
.cx{fill:%(no)s;stroke:%(no_borda)s;stroke-width:1;transition:fill var(--t),stroke var(--t)}
.cx.cab{fill:%(no_borda)s}
.cx.passo{fill:%(caminho)s;stroke:%(caminho)s}
.cx.maior{fill:%(maior)s;stroke:%(maior)s}
.cx.achou{fill:%(alvo)s;stroke:%(alvo)s}
.cx.ex{stroke:%(cursor)s;stroke-width:3}
.pt{stroke:%(aresta)s;stroke-width:1.4;fill:none;marker-end:url(#seta);
  transition:stroke var(--t),stroke-width var(--t)}
.pt.seguido{stroke:%(caminho)s;stroke-width:2.6;marker-end:url(#seta-c)}
.pt.ex{stroke:%(cursor)s;stroke-width:3;stroke-dasharray:6 4;marker-end:url(#seta-x);
  animation:flui .6s linear infinite}
@keyframes flui{to{stroke-dashoffset:-10}}
.chave .ano{font-weight:700}
.gap rect{fill:none;stroke:%(aresta)s;stroke-dasharray:4 4}
.gap text{fill:%(fraco)s}
.rotulo{fill:%(fraco)s}
.niv{fill:%(fraco)s;text-anchor:end}
.seta{fill:%(aresta)s}.seta-c{fill:%(caminho)s}.seta-x{fill:%(cursor)s}
</style>"""


def _formatar(chave):
    return html.escape(str(chave)) if chave is not None else "o fim da lista"


def quadros_skip(skip, chave):
    """Desenho e quadros da busca por chave na skip list.

    A skip list é desenhada como torres (uma caixa por nível) ligadas por
    ponteiros, só com os nós que a busca comparou; os trechos que ela pulou
    viram uma caixa "⋯ N nós". Os ponteiros são os reais: um ponteiro para
    um nó de um trecho pulado termina nesse trecho.
    Devolve (svg, rótulos dos níveis, quadros, passos, altura em px).
    """
    passos = rastro_skip(skip, chave)
    tocadas = []
    for _, _, _, para in passos:
        if para is not None and para not in tocadas:
            tocadas.append(para)
    ordenadas = [k for k, _ in merge_sort([(k, None) for k in tocadas])]
    colunas = _nos_da_base_ate(skip, ordenadas)
    niveis = skip.nivel
    restantes = len(skip) - sum(p for _, p in colunas) - len(colunas)

    # colunas em ordem: cabeça, (trecho pulado), nó, ..., (trecho pulado), fim
    itens = [("cab", None, niveis)]
    for no, pulados in colunas:
        if pulados:
            itens.append(("gap", pulados, 0))
        itens.append(("no", no, no.nivel))
    if restantes:
        itens.append(("gap", restantes, 0))
    itens.append(("fim", None, niveis))
    xs, x = [], 20
    for tipo, _, _ in itens:
        w = GW if tipo == "gap" else CW
        xs.append(x + w / 2)
        x += w
    largura = x + 20
    altura = TOPO + niveis * RH + 48

    def y(i):  # centro da caixa do nível i
        return TOPO + (niveis - 1 - i) * RH + BH / 2

    col_de = {None: 0}  # chave -> índice da coluna (None = cabeça)
    for c, (tipo, no, _) in enumerate(itens):
        if tipo == "no":
            col_de[no.chave] = c
    fim = len(itens) - 1

    def coluna_alvo(origem, alvo):
        """Coluna onde o ponteiro termina: o nó, o fim ou o trecho pulado que o contém."""
        if alvo is None:
            return fim
        if alvo.chave in col_de:
            return col_de[alvo.chave]
        for c in range(origem + 1, fim):
            if itens[c][0] == "gap" and (itens[c + 1][0] == "fim"
                                         or alvo.chave < itens[c + 1][1].chave):
                return c
        return fim

    defs = "".join(
        f'<marker id="{m}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        f'markerHeight="7" orient="auto"><path class="{m}" d="M0,0 L10,5 L0,10 z"/></marker>'
        for m in ("seta", "seta-c", "seta-x"))
    ponteiros, caixas, rotulos = [], [], []
    for c, (tipo, no, altura_torre) in enumerate(itens):
        xc = xs[c]
        if tipo == "gap":
            rotulos.append(f'<g class="gap"><rect x="{xc - GW / 2 + 6}" y="{TOPO - 6}" '
                           f'width="{GW - 12}" height="{niveis * RH + 6}" rx="6"/>'
                           f'<text x="{xc}" y="{y(0) + 30}">⋯ {no} {"nó" if no == 1 else "nós"}</text></g>')
            continue
        for i in range(altura_torre):
            classe = "cx" if tipo == "no" else "cx cab"
            caixas.append(f'<rect id="b{c}_{i}" class="{classe}" x="{xc - TORRE / 2}" '
                          f'y="{y(i) - BH / 2}" width="{TORRE}" height="{BH}" rx="4"/>')
            if tipo == "fim":
                continue
            alvo = coluna_alvo(c, no.prox[i] if tipo == "no" else skip.cabeca.prox[i])
            x2 = xs[alvo] - (GW / 2 - 8 if itens[alvo][0] == "gap" else TORRE / 2 + 2)
            ponteiros.append(f'<path id="p{c}_{i}" class="pt" d="M{xc + TORRE / 2},{y(i)} '
                             f'L{x2},{y(i)}"/>')
        if tipo == "no":
            ano, pid = no.chave
            rotulos.append(f'<text class="chave" x="{xc}" y="{y(0) + 26}"><tspan class="ano">'
                           f'{ano}</tspan> · {pid}</text>')
        else:
            nome = "cabeça" if tipo == "cab" else "fim (∅)"
            rotulos.append(f'<text class="rotulo" x="{xc}" y="{y(0) + 26}">{nome}</text>')
    cursor = (f'<g id="cursor" style="transform:translate({xs[0]}px,{y(niveis - 1)}px)">'
              f'<rect class="cursor pulsa" x="{-TORRE / 2 - 5}" y="{-BH / 2 - 5}" '
              f'width="{TORRE + 10}" height="{BH + 10}" rx="7"/></g>')
    svg = (f'<svg width="{largura}" height="{altura}" xmlns="http://www.w3.org/2000/svg">'
           f'<defs>{defs}</defs>' + "".join(ponteiros + caixas + rotulos) + cursor + "</svg>")
    # rótulos dos níveis ficam fora do palco, fixos enquanto ele rola para os lados
    fixo = (f'<svg width="58" height="{altura}">'
            + "".join(f'<text class="niv" x="52" y="{y(i) + 4}">nível {i}</text>'
                      for i in range(niveis)) + "</svg>")

    narracao = narrar_busca_skip(passos, chave)
    alvo = html.escape(str(chave))
    quadros = [_q([[f"b0_{niveis - 1}", "cx cab passo"]],
                  f"Buscando <b>{alvo}</b>. A busca começa na cabeça, no nível mais alto "
                  f"({niveis - 1}). Clique em ▶ animar ou avance passo a passo.",
                  0, [xs[0], y(niveis - 1)])]
    comp = 0
    for n, (acao, i, de, para) in enumerate(passos, 1):
        c = col_de[de]
        d = col_de[para] if para is not None else fim
        prox = _formatar(para)
        ex = [f"p{c}_{i}"] + ([f"b{d}_{i}"] if para is not None else [])
        marcas, cur = [], [xs[c], y(i)]
        if acao in ("avança", "achou"):
            achou = acao == "achou"
            comp += 2 if achou else 1
            marcas = [[f"p{c}_{i}", "pt seguido"], [f"b{d}_{i}", "cx achou" if achou else "cx passo"]]
            cur = [xs[d], y(i)]
            if achou:
                texto = (f"{prox} &lt; <b>{alvo}</b>? {_nao()}<br>"
                         f"{prox} = <b>{alvo}</b>? {_sim()} → achou!")
            else:
                texto = f"{prox} &lt; <b>{alvo}</b>? {_sim()} → avança"
        else:
            if para is not None:
                comp += 2
                marcas = [[f"b{d}_{i}", "cx maior"]]
                texto = (f"{prox} &lt; <b>{alvo}</b>? {_nao()}<br>"
                         f"{prox} = <b>{alvo}</b>? {_nao()} → ")
            else:
                texto = "o próximo é o fim da lista → "
            if i > 0:  # desce um nível na mesma torre
                marcas.append([f"b{c}_{i - 1}", "cx passo" if c else "cx cab passo"])
                cur = [xs[c], y(i - 1)]
                texto += "desce"
            else:
                texto += "não está na lista"
        # o balão fica logo acima do ponteiro comparado, saindo da torre atual
        quadros.append(_q(marcas, _negrito(narracao[n - 1]), comp, cur,
                          [texto, xs[c] + TORRE / 2 + 6, y(i) - BH / 2 - 2, "c"], ex))
    return svg, fixo, quadros, passos, altura


def html_busca_skip_animada(skip, chave, tema=None):
    """Página com a busca animada na skip list. Devolve (html, passos)."""
    svg, fixo, quadros, passos, altura = quadros_skip(skip, chave)
    # compara primeiro (o balão aparece) e depois o cursor anda ou desce
    pagina = _pagina(tema, _CSS_SKIP, svg, quadros, altura + 20, 0.35, 0, fixo, camera_x=0.3)
    return pagina, passos


def altura_skip(skip):
    """Altura do componente: palco (uma linha por nível) mais controles."""
    return TOPO + skip.nivel * RH + 48 + 150

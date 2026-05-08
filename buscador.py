import asyncio
import aiohttp
import sqlite3
import re
import json

from datetime import datetime

# =========================================================
# CONFIG
# =========================================================

DB_NAME = "canais.db"
HTML_NAME = "index.html"

TIMEOUT_LISTA = 8

# =========================================================
# FONTES PUBLICAS
# =========================================================

FONTES = [

    "https://iptv-org.github.io/iptv/index.m3u",

    "https://iptv-org.github.io/iptv/countries/br.m3u",
    "https://iptv-org.github.io/iptv/countries/us.m3u",
    "https://iptv-org.github.io/iptv/countries/uk.m3u",
    "https://iptv-org.github.io/iptv/countries/es.m3u",
    "https://iptv-org.github.io/iptv/countries/fr.m3u",
    "https://iptv-org.github.io/iptv/countries/it.m3u",
    "https://iptv-org.github.io/iptv/countries/de.m3u",

    "https://iptv-org.github.io/iptv/categories/news.m3u",
    "https://iptv-org.github.io/iptv/categories/sports.m3u",
    "https://iptv-org.github.io/iptv/categories/movies.m3u",
    "https://iptv-org.github.io/iptv/categories/kids.m3u",
    "https://iptv-org.github.io/iptv/categories/music.m3u",
    "https://iptv-org.github.io/iptv/categories/documentary.m3u",

    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/br.m3u",
    "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
    "https://raw.githubusercontent.com/HelmerLousas/m3u-br/main/br.m3u",
    "https://raw.githubusercontent.com/GuikiAnimes/Canal-Aberto-Brasil/main/CanalAbertoBrasil.m3u",
]

# =========================================================
# HEADERS
# =========================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/123 Safari/537.36"
    )
}

# =========================================================
# DATABASE
# =========================================================

def iniciar_banco():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS canais (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nome TEXT,
        categoria TEXT,
        url TEXT,
        ultima_verificacao TEXT

    )

    """)

    conn.commit()

    conn.close()

# =========================================================
# LIMPEZA
# =========================================================

def limpar_nome(nome):

    nome = nome.upper()

    nome = re.sub(
        r'\[.*?\]|\(.*?\)|\||★|►',
        '',
        nome
    )

    nome = re.sub(r'\s+', ' ', nome).strip()

    return nome

# =========================================================
# CATEGORIA
# =========================================================

def detectar_categoria(nome):

    nome = nome.upper()

    if any(x in nome for x in [
        "SPORT",
        "ESPN",
        "PREMIERE",
        "COMBATE",
        "NBA",
        "NFL"
    ]):
        return "ESPORTES"

    if any(x in nome for x in [
        "FILME",
        "MOVIE",
        "HBO",
        "TELECINE",
        "CINEMA"
    ]):
        return "FILMES"

    if any(x in nome for x in [
        "KIDS",
        "CARTOON",
        "INFANTIL"
    ]):
        return "INFANTIL"

    if any(x in nome for x in [
        "NEWS",
        "CNN",
        "FOX NEWS"
    ]):
        return "NOTICIAS"

    return "GERAL"

# =========================================================
# BAIXAR LISTAS
# =========================================================

async def baixar_lista(session, url):

    try:

        async with session.get(

            url,

            timeout=TIMEOUT_LISTA,

            headers=HEADERS

        ) as response:

            if response.status != 200:
                return ""

            return await response.text()

    except:
        return ""

# =========================================================
# EXTRAIR CANAIS
# =========================================================

def extrair_canais(conteudo):

    canais = []

    regex = (
        r'#EXTINF:.*?,(.*?)\n'
        r'(?:#.*?\n)*'
        r'((?:https?|rtmp|rtsp|udp)[^\s\n\r]+)'
    )

    matches = re.findall(

        regex,

        conteudo,

        re.IGNORECASE

    )

    for nome, url in matches:

        nome = limpar_nome(nome)

        if len(nome) < 2:
            continue

        canais.append({

            "nome": nome,

            "url": url.strip(),

            "categoria": detectar_categoria(nome)

        })

    return canais

# =========================================================
# SALVAR DB
# =========================================================

def salvar_canal(canal):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    try:

        cursor.execute("""

        INSERT INTO canais (

            nome,
            categoria,
            url,
            ultima_verificacao

        )

        VALUES (?, ?, ?, ?)

        """, (

            canal["nome"],
            canal["categoria"],
            canal["url"],

            datetime.now().strftime(
                "%d/%m/%Y %H:%M:%S"
            )

        ))

        conn.commit()

    except:
        pass

    conn.close()

# =========================================================
# HTML DINAMICO
# =========================================================

def gerar_html(canais):

    agora = datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )

    dados_json = json.dumps(canais)

    html = f"""

<!DOCTYPE html>

<html lang="pt-br">

<head>

<meta charset="UTF-8">

<title>PH-TV MASSIVE</title>

<style>

body {{
    margin:0;
    background:#050505;
    color:white;
    font-family:Arial;
}}

header {{
    position:sticky;
    top:0;
    background:#000;
    padding:20px;
    border-bottom:2px solid red;
    z-index:999;
}}

h1 {{
    margin:0;
    color:#ff0000;
}}

.stats {{
    color:#aaa;
    margin-top:5px;
}}

#search {{
    width:100%;
    padding:12px;
    margin-top:15px;
    border:none;
    background:#111;
    color:white;
    font-size:16px;
}}

.grid {{
    display:grid;
    grid-template-columns:
    repeat(auto-fill,minmax(280px,1fr));

    gap:15px;

    padding:20px;
}}

.card {{
    background:#111;
    border:1px solid #222;
    border-radius:10px;
    padding:15px;
}}

.card:hover {{
    border-color:red;
}}

.nome {{
    font-weight:bold;
    margin-bottom:10px;
}}

.categoria {{
    color:#00ff88;
    font-size:12px;
    margin-bottom:10px;
}}

.url {{
    background:#000;
    color:#00ff00;
    padding:8px;
    font-size:11px;
    border-radius:5px;
    word-break:break-all;
    height:50px;
    overflow:hidden;
}}

.btns {{
    display:flex;
    gap:8px;
    margin-top:10px;
}}

button,a {{
    flex:1;
    border:none;
    padding:10px;
    text-align:center;
    text-decoration:none;
    border-radius:5px;
    cursor:pointer;
    font-weight:bold;
}}

.copy {{
    background:#00ff00;
    color:black;
}}

.test {{
    background:red;
    color:white;
}}

.pages {{
    display:flex;
    justify-content:center;
    gap:10px;
    padding:20px;
}}

.pages button {{
    background:#111;
    color:white;
    border:1px solid #333;
    padding:10px 15px;
}}

.pages button:hover {{
    border-color:red;
}}

</style>

</head>

<body>

<header>

<h1>☢️ PH-TV MASSIVE</h1>

<div class="stats">

TOTAL:
<b>{len(canais)}</b>

|

ATUALIZADO:
{agora}

</div>

<input
type="text"
id="search"
placeholder="Buscar canais..."
onkeyup="buscar()"
/>

</header>

<div class="grid" id="grid"></div>

<div class="pages">

<button onclick="paginaAnterior()">
◀ ANTERIOR
</button>

<div id="pageInfo"></div>

<button onclick="proximaPagina()">
PRÓXIMA ▶
</button>

</div>

<script>

const canais = {dados_json}

let canaisFiltrados = [...canais]

let paginaAtual = 1

const porPagina = 80

function renderizar(){

    const grid =
    document.getElementById("grid")

    grid.innerHTML = ""

    const inicio =
    (paginaAtual - 1) * porPagina

    const fim =
    inicio + porPagina

    const pagina =
    canaisFiltrados.slice(inicio, fim)

    pagina.forEach((canal, i) => {{

        grid.innerHTML += `

        <div class="card">

            <div class="nome">
                ${{canal.nome}}
            </div>

            <div class="categoria">
                ${{canal.categoria}}
            </div>

            <div class="url" id="u${{i}}">
                ${{canal.url}}
            </div>

            <div class="btns">

                <button
                class="copy"
                onclick="copiar('${{canal.url}}')"
                >
                COPIAR
                </button>

                <a
                class="test"
                target="_blank"
                href="https://hls-js.netlify.app/demo/?src=${{canal.url}}"
                >
                TESTAR
                </a>

            </div>

        </div>

        `
    }})

    atualizarInfo()
}

function atualizarInfo(){{

    const total =
    Math.ceil(
        canaisFiltrados.length / porPagina
    )

    document.getElementById("pageInfo")
    .innerHTML =
    `Página ${{paginaAtual}} de ${{total}}`
}}

function buscar(){{

    let q =
    document
    .getElementById("search")
    .value
    .toUpperCase()

    canaisFiltrados =
    canais.filter(c =>

        c.nome.includes(q)

    )

    paginaAtual = 1

    renderizar()
}}

function proximaPagina(){{

    const total =
    Math.ceil(
        canaisFiltrados.length / porPagina
    )

    if(paginaAtual < total){{
        paginaAtual++
        renderizar()
    }}
}}

function paginaAnterior(){{

    if(paginaAtual > 1){{
        paginaAtual--
        renderizar()
    }}
}}

function copiar(texto){{

    navigator.clipboard.writeText(texto)

    alert("URL copiada!")

}}

renderizar()

</script>

</body>

</html>

"""

    with open(

        HTML_NAME,

        "w",

        encoding="utf-8"

    ) as f:

        f.write(html)

# =========================================================
# PROCESSAR
# =========================================================

async def processar():

    print("\n🚀 INICIANDO MEGA SCAN IPTV\n")

    iniciar_banco()

    connector = aiohttp.TCPConnector(

        limit=100,

        ssl=False

    )

    async with aiohttp.ClientSession(

        connector=connector

    ) as session:

        tarefas = [

            baixar_lista(session, fonte)

            for fonte in FONTES

        ]

        resultados = await asyncio.gather(

            *tarefas,

            return_exceptions=True

        )

        todos = []

        for conteudo in resultados:

            if not conteudo:
                continue

            canais = extrair_canais(conteudo)

            todos.extend(canais)

        print(f"\n📡 TOTAL ENCONTRADO: {len(todos)}")

        # SEM DEDUPLICAÇÃO
        canais_finais = todos

        # SALVAR
        for canal in canais_finais:
            salvar_canal(canal)

        # ORDENAR
        canais_finais = sorted(

            canais_finais,

            key=lambda x: x["nome"]

        )

        gerar_html(canais_finais)

        print("\n💾 HTML GERADO")

# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    asyncio.run(processar())

import asyncio
import aiohttp
import sqlite3
import re

from datetime import datetime

# ============================================
# CONFIG
# ============================================

DB_NAME = "canais.db"
HTML_NAME = "index.html"

TIMEOUT = 10

# ============================================
# FONTES PUBLICAS
# ============================================

FONTES = [

    # IPTV ORG
    "https://iptv-org.github.io/iptv/index.m3u",
    "https://iptv-org.github.io/iptv/countries/br.m3u",
    "https://iptv-org.github.io/iptv/languages/por.m3u",
    "https://iptv-org.github.io/iptv/categories/news.m3u",
    "https://iptv-org.github.io/iptv/categories/sports.m3u",
    "https://iptv-org.github.io/iptv/categories/movies.m3u",
    "https://iptv-org.github.io/iptv/categories/kids.m3u",

    # LISTAS GITHUB
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/br.m3u",
    "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
    "https://raw.githubusercontent.com/HelmerLousas/m3u-br/main/br.m3u",
    "https://raw.githubusercontent.com/GuikiAnimes/Canal-Aberto-Brasil/main/CanalAbertoBrasil.m3u",
    "https://raw.githubusercontent.com/LITUATUI/IPTV/main/BR.m3u",
    "https://raw.githubusercontent.com/Geovane-S/Listas/main/Brasil.m3u",
]

# ============================================
# HEADERS
# ============================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/123 Safari/537.36"
    )
}

# ============================================
# DATABASE
# ============================================

def iniciar_banco():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS canais (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nome TEXT,
        categoria TEXT,
        url TEXT UNIQUE,

        status TEXT,

        ultima_verificacao TEXT

    )

    """)

    conn.commit()

    conn.close()

# ============================================
# LIMPAR NOME
# ============================================

def limpar_nome(nome):

    nome = nome.upper()

    nome = re.sub(
        r'\[.*?\]|\(.*?\)|\d+P|HD|FHD|4K|UHD|SD|\||★|►',
        '',
        nome
    )

    nome = re.sub(r'\s+', ' ', nome).strip()

    return nome

# ============================================
# CATEGORIA
# ============================================

def detectar_categoria(nome):

    nome = nome.upper()

    if any(x in nome for x in [
        "SPORT",
        "ESPN",
        "COMBATE",
        "PREMIERE"
    ]):
        return "ESPORTES"

    if any(x in nome for x in [
        "FILME",
        "MOVIE",
        "HBO",
        "TELECINE"
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
        "GLOBO NEWS"
    ]):
        return "NOTICIAS"

    return "GERAL"

# ============================================
# BAIXAR LISTA
# ============================================

async def baixar_lista(session, url):

    try:

        async with session.get(

            url,

            timeout=TIMEOUT,

            headers=HEADERS

        ) as response:

            if response.status != 200:
                return ""

            return await response.text()

    except:
        return ""

# ============================================
# EXTRAIR CANAIS
# ============================================

def extrair_canais(conteudo):

    canais = []

    regex = (
        r'#EXTINF:.*?,(.*?)\n'
        r'(?:#.*?\n)*'
        r'((?:https?|rtmp|rtsp)[^\s\n\r]+)'
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

# ============================================
# VALIDAR STREAM
# ============================================

async def validar_stream(session, url):

    try:

        async with session.get(

            url,

            timeout=8,

            headers=HEADERS,

            allow_redirects=True

        ) as response:

            if response.status != 200:
                return False

            content_type = response.headers.get(

                "Content-Type",

                ""

            ).lower()

            if (

                "mpegurl" in content_type
                or "video" in content_type
                or ".m3u8" in url
                or ".ts" in url

            ):
                return True

            return True

    except:
        return False

# ============================================
# SALVAR DB
# ============================================

def salvar_canal(canal, status):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    try:

        cursor.execute("""

        INSERT OR REPLACE INTO canais

        (

            nome,
            categoria,
            url,
            status,
            ultima_verificacao

        )

        VALUES (?, ?, ?, ?, ?)

        """, (

            canal["nome"],

            canal["categoria"],

            canal["url"],

            status,

            datetime.now().strftime(
                "%d/%m/%Y %H:%M:%S"
            )

        ))

        conn.commit()

    except:
        pass

    conn.close()

# ============================================
# GERAR HTML
# ============================================

def gerar_html(canais):

    agora = datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )

    html = f"""

<!DOCTYPE html>

<html lang="pt-br">

<head>

<meta charset="UTF-8">

<title>PH-TV ULTIMATE</title>

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
    repeat(auto-fill,minmax(300px,1fr));

    gap:15px;

    padding:20px;

}}

.card {{

    background:#111;

    border:1px solid #222;

    border-radius:10px;

    padding:15px;

    transition:0.2s;

}}

.card:hover {{

    transform:scale(1.02);

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

input {{

    width:100%;

    background:#000;

    color:#00ff00;

    border:1px solid #333;

    padding:8px;

    font-size:11px;

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

.hidden {{

    display:none;

}}

</style>

</head>

<body>

<header>

<h1>☢️ PH-TV ULTIMATE</h1>

<div class="stats">

ONLINE:
<b>{len(canais)}</b>

|

ATUALIZADO:
{agora}

</div>

<input

type="text"

id="search"

placeholder="Buscar canais..."

onkeyup="filtrar()"

/>

</header>

<div class="grid">

"""

    for i, canal in enumerate(canais):

        html += f"""

<div class="card"

data-name="{canal['nome']}">

<div class="nome">

{canal['nome']}

</div>

<div class="categoria">

{canal['categoria']}

</div>

<input

type="text"

value="{canal['url']}"

id="u{i}"

readonly

/>

<div class="btns">

<button

class="copy"

onclick="copiar('u{i}')"

>

COPIAR

</button>

<a

class="test"

target="_blank"

href="https://hls-js.netlify.app/demo/?src={canal['url']}"

>

TESTAR

</a>

</div>

</div>

"""

    html += """

</div>

<script>

function filtrar(){

    let q = document
    .getElementById("search")
    .value
    .toUpperCase()

    let cards =
    document.getElementsByClassName("card")

    for(let i=0;i<cards.length;i++){

        let n = cards[i]
        .getAttribute("data-name")

        cards[i]
        .classList
        .toggle(
            "hidden",
            !n.includes(q)
        )
    }
}

function copiar(id){

    let el =
    document.getElementById(id)

    el.select()

    document.execCommand("copy")

    alert("URL copiada!")

}

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

# ============================================
# PROCESSAR
# ============================================

async def processar():

    print("\n🚀 INICIANDO SCAN IPTV\n")

    iniciar_banco()

    connector = aiohttp.TCPConnector(

        limit=300

    )

    async with aiohttp.ClientSession(

        connector=connector

    ) as session:

        tarefas = [

            baixar_lista(session, fonte)

            for fonte in FONTES

        ]

        resultados = await asyncio.gather(*tarefas)

        todos = []

        for conteudo in resultados:

            if not conteudo:
                continue

            canais = extrair_canais(conteudo)

            todos.extend(canais)

        # REMOVER DUPLICADOS

        vistos = set()

        unicos = []

        for canal in todos:

            url = canal["url"] \
                .strip() \
                .lower()

            if url not in vistos:

                vistos.add(url)

                unicos.append(canal)

        print(f"\n📡 TOTAL EXTRAIDO: {len(unicos)}")

        # VALIDAR

        validos = []

        for i, canal in enumerate(unicos):

            print(

                f"🔎 [{i+1}/{len(unicos)}] "
                f"{canal['nome'][:50]}"

            )

            ok = await validar_stream(

                session,

                canal["url"]

            )

            status = (
                "ONLINE"
                if ok
                else "OFFLINE"
            )

            salvar_canal(

                canal,

                status

            )

            if ok:
                validos.append(canal)

        print(f"\n✅ ONLINE: {len(validos)}")

        gerar_html(validos)

        print("\n💾 HTML GERADO")

# ============================================
# START
# ============================================

if __name__ == "__main__":

    asyncio.run(processar())

import asyncio
import aiohttp
import sqlite3
import re

from datetime import datetime

# =========================================================
# CONFIG
# =========================================================

DB_NAME = "canais.db"
HTML_NAME = "index.html"

TIMEOUT_LISTA = 8

# =========================================================
# FONTES PUBLICAS MASSIVAS
# =========================================================

FONTES = [

    # IPTV ORG GLOBAL
    "https://iptv-org.github.io/iptv/index.m3u",

    # PAISES
    "https://iptv-org.github.io/iptv/countries/br.m3u",
    "https://iptv-org.github.io/iptv/countries/us.m3u",
    "https://iptv-org.github.io/iptv/countries/uk.m3u",
    "https://iptv-org.github.io/iptv/countries/es.m3u",
    "https://iptv-org.github.io/iptv/countries/fr.m3u",
    "https://iptv-org.github.io/iptv/countries/it.m3u",
    "https://iptv-org.github.io/iptv/countries/de.m3u",
    "https://iptv-org.github.io/iptv/countries/pt.m3u",
    "https://iptv-org.github.io/iptv/countries/ar.m3u",
    "https://iptv-org.github.io/iptv/countries/mx.m3u",

    # CATEGORIAS
    "https://iptv-org.github.io/iptv/categories/news.m3u",
    "https://iptv-org.github.io/iptv/categories/sports.m3u",
    "https://iptv-org.github.io/iptv/categories/movies.m3u",
    "https://iptv-org.github.io/iptv/categories/kids.m3u",
    "https://iptv-org.github.io/iptv/categories/music.m3u",
    "https://iptv-org.github.io/iptv/categories/documentary.m3u",
    "https://iptv-org.github.io/iptv/categories/entertainment.m3u",

    # GITHUB PUBLICOS
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/br.m3u",
    "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
    "https://raw.githubusercontent.com/HelmerLousas/m3u-br/main/br.m3u",
    "https://raw.githubusercontent.com/GuikiAnimes/Canal-Aberto-Brasil/main/CanalAbertoBrasil.m3u",
    "https://raw.githubusercontent.com/LITUATUI/IPTV/main/BR.m3u",
    "https://raw.githubusercontent.com/Geovane-S/Listas/main/Brasil.m3u",

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
# LIMPAR NOME
# =========================================================

def limpar_nome(nome):

    nome = nome.upper()

    # LIMPEZA LEVE
    nome = re.sub(
        r'\[.*?\]|\(.*?\)|\||★|►',
        '',
        nome
    )

    nome = re.sub(r'\s+', ' ', nome).strip()

    return nome

# =========================================================
# CATEGORIAS
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
        "INFANTIL",
        "DISNEY"
    ]):
        return "INFANTIL"

    if any(x in nome for x in [
        "NEWS",
        "CNN",
        "FOX NEWS",
        "GLOBO NEWS"
    ]):
        return "NOTICIAS"

    if any(x in nome for x in [
        "MUSIC",
        "MTV"
    ]):
        return "MUSICA"

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
# SALVAR BANCO
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
# GERAR HTML
# =========================================================

def gerar_html(canais):

    agora = datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )

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

<h1>☢️ PH-TV MASSIVE</h1>

<div class="stats">

TOTAL DE STREAMS:
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

        let n =
        cards[i]
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

        # GERAR HTML
        gerar_html(canais_finais)

        print("\n💾 HTML GERADO COM SUCESSO")

# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    asyncio.run(processar())

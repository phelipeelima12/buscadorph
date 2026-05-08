import asyncio
import aiohttp
import re
import sqlite3
from datetime import datetime

# ============================================
# CONFIG
# ============================================

DB_NAME = "canais.db"
HTML_NAME = "index.html"
TIMEOUT = 12

# ============================================
# FONTES PUBLICAS / FREE TO AIR
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

    # Github Públicos
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/br.m3u",
    "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
    "https://raw.githubusercontent.com/HelmerLousas/m3u-br/main/br.m3u",
    "https://raw.githubusercontent.com/GuikiAnimes/Canal-Aberto-Brasil/main/CanalAbertoBrasil.m3u",
    "https://raw.githubusercontent.com/LITUATUI/IPTV/main/BR.m3u",
    "https://raw.githubusercontent.com/Geovane-S/Listas/main/Brasil.m3u",
]

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
# LIMPEZA
# ============================================

def limpar_nome(nome):

    nome = nome.upper()

    nome = re.sub(
        r'\[.*?\]|\(.*?\)|\d+P|HD|FHD|UHD|4K|SD|\||★|►',
        '',
        nome
    )

    nome = re.sub(r'\s+', ' ', nome).strip()

    return nome

# ============================================
# CATEGORIAS
# ============================================

def detectar_categoria(nome):

    nome = nome.upper()

    if any(x in nome for x in ["SPORT", "ESPN", "PREMIERE", "COMBATE"]):
        return "ESPORTES"

    if any(x in nome for x in ["KIDS", "INFANTIL", "CARTOON", "DISCOVERY KIDS"]):
        return "INFANTIL"

    if any(x in nome for x in ["MOVIE", "FILME", "CINEMA", "HBO", "TELECINE"]):
        return "FILMES"

    if any(x in nome for x in ["NEWS", "CNN", "GLOBO NEWS", "BANDNEWS"]):
        return "NOTICIAS"

    return "GERAL"

# ============================================
# FETCH
# ============================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    )
}

# ============================================
# BAIXAR LISTAS
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
# VALIDAR STREAM
# ============================================

async def validar_stream(session, url):

    try:

        async with session.get(
            url,
            timeout=8,
            headers=HEADERS
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
# EXTRAIR STREAMS
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
# SALVAR BANCO
# ============================================

def salvar_canal(canal, status):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:

        cursor.execute("""
        INSERT OR REPLACE INTO canais
        (nome, categoria, url, status, ultima_verificacao)
        VALUES (?, ?, ?, ?, ?)
        """, (
            canal["nome"],
            canal["categoria"],
            canal["url"],
            status,
            datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        ))

        conn.commit()

    except:
        pass

    conn.close()

# ============================================
# PROCESSAR TUDO
# ============================================

async def processar():

    print("\n🚀 INICIANDO MEGA SCAN IPTV\n")

    iniciar_banco()

    connector = aiohttp.TCPConnector(limit=100)

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

        # ============================================
        # REMOVER DUPLICADOS
        # ============================================

        vistos = set()
        canais_unicos = []

        for canal in todos:

            url = canal["url"].strip().lower()

            if url not in vistos:
                vistos.add(url)
                canais_unicos.append(canal)

        print(f"📡 ENCONTRADOS: {len(canais_unicos)} canais")

        # ============================================
        # VALIDAR
        # ============================================

        validos = []

        for i, canal in enumerate(canais_unicos):

            print(
                f"🔎 VALIDANDO "
                f"[{i+1}/{len(canais_unicos)}] "
                f"{canal['nome'][:40]}"
            )

            ok = await validar_stream(
                session,
                canal["url"]
            )

            status = "ONLINE" if ok else "OFFLINE"

            salvar_canal(canal, status)

            if ok:
                validos.append(canal)

        print(f"\n✅ ONLINE: {len(validos)}")

        gerar_html(validos)

# ============================================
# GERAR HTML
# ============================================

def gerar_html(canais):

    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

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
    font-family:Arial;
    color:white;
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
CANAIS ONLINE:
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

<div class="grid" id="grid">
"""

    for i, canal in enumerate(canais):

        html += f"""
<div class="card" data-name="{canal['nome']}">

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

    let q =
    document
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

    print(f"\n💾 HTML GERADO: {HTML_NAME}")

# ============================================
# START
# ============================================

if __name__ == "__main__":

    asyncio.run(processar())

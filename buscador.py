import requests
from datetime import datetime
import re

def buscar_links():
    # FONTES APELATIVAS: Algumas dessas listas têm mais de 10 mil canais misturados
    fontes = [
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/br.m3u",
        "https://raw.githubusercontent.com/GuikiAnimes/Canal-Aberto-Brasil/main/CanalAbertoBrasil.m3u",
        "https://raw.githubusercontent.com/LITUATUI/IPTV/main/BR.m3u",
        "https://raw.githubusercontent.com/HelmerLousas/m3u-br/main/br.m3u",
        "https://raw.githubusercontent.com/paimp/lista-iptv/master/lista.m3u",
        "https://raw.githubusercontent.com/Telesv/Documentarios/main/documentarios.m3u",
        "https://raw.githubusercontent.com/AssignZ/Iptv-Gratis-Brasil/main/Lista%20Atualizada.m3u",
        "https://raw.githubusercontent.com/Deivid-Souto/IPTV-Brasil/main/canais.m3u",
        "https://raw.githubusercontent.com/estebandiazp/Lista-IPTV-Brasil/master/Brasil.m3u",
        # FONTE GLOBAIS COM MUITO CONTEÚDO (DUMPS):
        "https://raw.githubusercontent.com/iptv-org/iptv/master/index.m3u",
        "https://raw.githubusercontent.com/m3u8playlist/Free-IPTV-Links-Daily/master/brazil.m3u"
    ]
    
    canais_encontrados = []
    print("🚀 MODO BERSERKER ATIVADO: Minerando tudo...")

    for url in fontes:
        try:
            print(f"📡 Varrendo fonte: {url}")
            # Timeout maior para listas gigantes de 20MB+
            response = requests.get(url, timeout=45, headers={'User-Agent': 'Mozilla/5.0'})
            if not response.ok: continue

            conteudo = response.text
            # Regex de captura profunda: Pega o nome e a URL, mesmo com lixo entre eles
            matches = re.findall(r'#EXTINF:.*?,(.*?)\n(?:#.*?\n)*(http[^\s\n\r]+)', conteudo)
            
            for nome, link in matches:
                n_upper = nome.strip().upper()
                # Se for de lista global, só pegamos se tiver BR ou for canal conhecido
                if any(x in n_upper for x in ["BR", "BRASIL", "PORTUGUESE", "PT-BR"]) or url != fontes[9]:
                    n_limpo = re.sub(r'\[.*?\]|\(.*?\)|\d+P|HD|SD|FHD|\|', '', n_upper).strip()
                    if n_limpo and len(link) > 10:
                        canais_encontrados.append({"nome": n_limpo, "url": link.strip()})
        except Exception as e:
            print(f"⚠️ Falha na fonte {url}: {e}")

    # Deduplicação agressiva pela URL base
    vistos = set()
    lista_final = []
    for c in canais_encontrados:
        u_base = c['url'].split('?')[0].lower().strip()
        if u_base not in vistos:
            vistos.add(u_base)
            lista_final.append(c)
    
    return sorted(lista_final, key=lambda x: x['nome'])

def gerar_painel(canais):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    html_template = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>PH-TV ULTIMATE FINDER</title>
        <style>
            body {{ background: #000; color: #00ff41; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 0; }}
            .header {{ position: sticky; top: 0; background: #000; padding: 20px; border-bottom: 2px solid #f00; text-align: center; z-index: 1000; }}
            #searchBar {{ width: 80%; padding: 12px; background: #111; border: 1px solid #f00; color: #fff; border-radius: 25px; outline: none; margin-top: 10px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; padding: 20px; }}
            .card {{ background: #0a0a0a; border: 1px solid #333; padding: 15px; border-radius: 10px; transition: 0.3s; }}
            .card:hover {{ border-color: #f00; box-shadow: 0 0 15px #f00; }}
            strong {{ display: block; color: #fff; margin-bottom: 10px; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
            input {{ width: 100%; background: #000; color: #0f0; border: 1px solid #222; padding: 8px; font-size: 10px; margin-bottom: 10px; border-radius: 5px; }}
            .btns {{ display: flex; gap: 5px; }}
            button, a {{ flex: 1; padding: 10px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 10px; text-decoration: none; text-align: center; }}
            .btn-copy {{ background: #00ff41; color: #000; }}
            .btn-test {{ background: #f00; color: #fff; }}
            .hidden {{ display: none !important; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>PH-TV ULTIMATE: MODO APELAÇÃO 🚀</h1>
            <div style="font-size: 12px; color: #888;">CANAIS ENCONTRADOS: <strong>{len(canais)}</strong> | ATUALIZADO: {agora}</div>
            <input type="text" id="searchBar" placeholder="PESQUISAR CANAL..." onkeyup="filter()">
        </div>
        <div class="grid" id="mainGrid">
    """
    for i, c in enumerate(canais):
        sid = f"u{i}"
        html_template += f"""
            <div class="card" data-name="{c['nome']}">
                <strong>{c['nome']}</strong>
                <input type="text" value="{c['url']}" id="{sid}" readonly>
                <div class="btns">
                    <button class="btn-copy" onclick="copyText('{sid}')">COPIAR</button>
                    <a class="btn-test" href="https://hls-js.netlify.app/demo/?src={c['url']}" target="_blank">TESTAR</a>
                </div>
            </div>
        """
    html_template += """
        </div>
        <script>
            function filter() {
                let q = document.getElementById('searchBar').value.toUpperCase();
                let cards = document.getElementsByClassName('card');
                for (let i = 0; i < cards.length; i++) {
                    let name = cards[i].getAttribute('data-name');
                    cards[i].classList.toggle('hidden', !name.includes(q));
                }
            }
            function copyText(id) {
                let el = document.getElementById(id);
                el.select();
                document.execCommand("copy");
                alert("IP Copiado!");
            }
        </script>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    canais = buscar_links()
    gerar_painel(canais)

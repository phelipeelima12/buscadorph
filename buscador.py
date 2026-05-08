import requests
from datetime import datetime
import re

def buscar_links():
    # FONTES DE ALTO IMPACTO (Algumas contêm milhares de canais mistos)
    fontes = [
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/br.m3u",
        "https://raw.githubusercontent.com/GuikiAnimes/Canal-Aberto-Brasil/main/CanalAbertoBrasil.m3u",
        "https://raw.githubusercontent.com/LITUATUI/IPTV/main/BR.m3u",
        "https://raw.githubusercontent.com/HelmerLousas/m3u-br/main/br.m3u",
        "https://raw.githubusercontent.com/paimp/lista-iptv/master/lista.m3u",
        "https://raw.githubusercontent.com/Deivid-Souto/IPTV-Brasil/main/canais.m3u",
        "https://raw.githubusercontent.com/AssignZ/Iptv-Gratis-Brasil/main/Lista%20Atualizada.m3u",
        "https://raw.githubusercontent.com/Geovane-S/Listas/main/Brasil.m3u",
        "https://raw.githubusercontent.com/m3u8playlist/Free-IPTV-Links-Daily/master/brazil.m3u",
        "https://raw.githubusercontent.com/K-S-H-I-Z-A/IPTV/master/brazil.m3u",
        "https://raw.githubusercontent.com/clube-iptv/lista/master/clube.m3u" # Lista densa
    ]
    
    canais_encontrados = []
    print("🚀 MODO NUCLEAR: Minerando canais abertos e fechados...")

    for url in fontes:
        try:
            print(f"📡 Escaneando fonte: {url}")
            # Headers de navegador real para evitar bloqueio de servidor de canais premium
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
            }
            response = requests.get(url, timeout=35, headers=headers)
            if not response.ok: continue

            conteudo = response.text
            # REGEX BRUTAL: Pega o nome após a vírgula e a URL que pode estar várias linhas abaixo
            # Ignora tags como group-title, tvg-id, etc.
            matches = re.findall(r'#EXTINF:.*?,(.*?)\n(?:#.*?\n)*(http[^\s\n\r]+)', conteudo)
            
            for nome, link in matches:
                n_upper = nome.strip().upper()
                # Limpeza de nomes para facilitar a busca (remove HD, 4K, [PT], etc)
                n_limpo = re.sub(r'\[.*?\]|\(.*?\)|\d+P|HD|SD|FHD|4K|\||★|►', '', n_upper).strip()
                
                if n_limpo and len(link) > 10:
                    canais_encontrados.append({"nome": n_limpo, "url": link.strip()})
        except Exception as e:
            print(f"⚠️ Falha na fonte {url}: {e}")

    # DEDUPLICAÇÃO E FILTRO DE QUALIDADE
    vistos_url = set()
    lista_final = []
    
    for c in canais_encontrados:
        # Normalizamos a URL (removemos parâmetros de token após o ?)
        url_base = c['url'].split('?')[0].lower().strip()
        if url_base not in vistos_url:
            vistos_url.add(url_base)
            lista_final.append(c)
    
    # Ordena alfabeticamente
    return sorted(lista_final, key=lambda x: x['nome'])

def gerar_painel(canais):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    html_template = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>PH-TV NUCLEAR FINDER</title>
        <style>
            body {{ background: #000; color: #0f0; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 0; }}
            .header {{ 
                position: sticky; top: 0; background: rgba(0,0,0,0.95); 
                padding: 15px; z-index: 1000; border-bottom: 2px solid #f00;
                text-align: center; box-shadow: 0 0 20px #f005;
            }}
            #searchBar {{ 
                width: 85%; max-width: 700px; padding: 12px; border-radius: 5px; 
                border: 1px solid #f00; background: #111; color: #fff; font-size: 16px;
                outline: none; margin-top: 10px;
            }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; padding: 20px; }}
            .card {{ background: #0a0a0a; border: 1px solid #333; padding: 15px; border-radius: 8px; transition: 0.2s; }}
            .card:hover {{ border-color: #f00; box-shadow: 0 0 15px #f005; transform: scale(1.02); }}
            .card strong {{ display: block; color: #fff; margin-bottom: 10px; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
            input {{ width: 100%; background: #000; color: #0f0; border: 1px solid #222; padding: 8px; font-size: 10px; margin-bottom: 10px; border-radius: 4px; }}
            .btns {{ display: flex; gap: 5px; }}
            button, a {{ flex: 1; padding: 10px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 11px; text-decoration: none; text-align: center; }}
            .btn-copy {{ background: #0f0; color: #000; }}
            .btn-test {{ background: #f00; color: #fff; }}
            .hidden {{ display: none !important; }}
            .stats {{ color: #888; font-size: 12px; margin-top: 5px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>☢️ PH-TV NUCLEAR FINDER</h1>
            <div class="stats">TOTAL DE SINAIS: <strong>{len(canais)}</strong> | ATUALIZADO: {agora}</div>
            <input type="text" id="searchBar" placeholder="Pesquise canais, filmes ou esportes..." onkeyup="filter()">
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
                alert("URL Copiada!");
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

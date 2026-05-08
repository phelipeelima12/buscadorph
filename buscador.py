import requests
from datetime import datetime
import re

def buscar_links():
    # Mistura de fontes oficiais e repositórios de "vazamentos" (mais canais)
    fontes = [
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/br.m3u",
        "https://raw.githubusercontent.com/GuikiAnimes/Canal-Aberto-Brasil/main/CanalAbertoBrasil.m3u",
        "https://raw.githubusercontent.com/LITUATUI/IPTV/main/BR.m3u",
        "https://raw.githubusercontent.com/HelmerLousas/m3u-br/main/br.m3u",
        "https://raw.githubusercontent.com/paimp/lista-iptv/master/lista.m3u",
        "https://raw.githubusercontent.com/Telesv/Documentarios/main/documentarios.m3u",
        "https://raw.githubusercontent.com/Dudu_IPTV/Lista_IPTV/main/lista_br.m3u",
        "https://raw.githubusercontent.com/maikofreitas/TV_ABERTA/main/tv_aberta.m3u",
        "https://raw.githubusercontent.com/AssignZ/Iptv-Gratis-Brasil/main/Lista%20Atualizada.m3u",
        "https://raw.githubusercontent.com/Joao-P-Marques/iptv-br/master/br.m3u"
    ]
    
    canais_encontrados = []
    print("🚀 Inciando Mineração de Alta Performance...")

    for url in fontes:
        try:
            print(f"📡 Varrendo: {url}")
            # Simulando navegador para evitar bloqueios
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, timeout=30, headers=headers)
            
            if response.ok:
                conteudo = response.text
                # Regex agressivo para capturar Nome e URL
                matches = re.findall(r'#EXTINF:.*?,(.*?)\n(?:#.*?\n)*(http[^\s\n\r]+)', conteudo)
                
                for nome, link in matches:
                    n_limpo = re.sub(r'\[.*?\]|\(.*?\)|\d+P|HD|SD|FHD|\||★|►', '', nome).strip().upper()
                    if n_limpo and len(link) > 10:
                        canais_encontrados.append({"nome": n_limpo, "url": link.strip()})
        except Exception as e:
            print(f"⚠️ Erro na fonte: {e}")

    # Deduplicação inteligente
    vistos = set()
    lista_final = []
    for c in canais_encontrados:
        u_norm = c['url'].split('?')[0].lower().strip()
        if u_norm not in vistos:
            vistos.add(u_norm)
            lista_final.append(c)
    
    return sorted(lista_final, key=lambda x: x['nome'])

def gerar_painel(canais):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    html_template = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PH-TV ULTIMATE FINDER</title>
        <style>
            :root {{ --neon: #00ff41; --bg: #050505; --card: #111; --text: #fff; }}
            body {{ background: var(--bg); color: var(--text); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; }}
            
            .header {{ 
                position: sticky; top: 0; background: rgba(5,5,5,0.9); 
                padding: 20px; z-index: 1000; border-bottom: 2px solid var(--neon);
                backdrop-filter: blur(10px); text-align: center;
            }}
            
            h1 {{ margin: 0; font-size: 24px; letter-spacing: 3px; color: var(--neon); text-shadow: 0 0 10px var(--neon); }}
            
            #searchBar {{ 
                width: 90%; max-width: 800px; padding: 15px; border-radius: 30px; 
                border: 1px solid #333; background: #000; color: var(--neon); 
                font-size: 16px; outline: none; margin-top: 15px; transition: 0.3s;
            }}
            #searchBar:focus {{ border-color: var(--neon); box-shadow: 0 0 15px rgba(0,255,65,0.2); }}

            .stats {{ font-size: 12px; color: #888; margin-top: 8px; }}

            .grid {{ 
                display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); 
                gap: 20px; padding: 25px; 
            }}

            .card {{ 
                background: var(--card); border: 1px solid #222; padding: 15px; 
                border-radius: 15px; position: relative; transition: 0.3s;
                display: flex; flex-direction: column;
            }}
            .card:hover {{ border-color: var(--neon); transform: translateY(-5px); }}
            
            .card strong {{ color: #fff; font-size: 16px; margin-bottom: 10px; display: block; }}
            
            .url-box {{ 
                background: #000; color: #0f8; border: 1px solid #333; 
                padding: 8px; font-size: 10px; border-radius: 5px; 
                margin-bottom: 12px; font-family: monospace; overflow: hidden;
            }}

            .actions {{ display: flex; gap: 8px; }}
            
            button, .btn-play {{ 
                flex: 1; padding: 10px; border: none; border-radius: 5px; 
                cursor: pointer; font-weight: bold; font-size: 12px; 
                text-decoration: none; text-align: center; transition: 0.2s;
            }}
            
            .btn-copy {{ background: var(--neon); color: #000; }}
            .btn-copy:hover {{ background: #fff; }}
            
            .btn-play {{ background: #007bff; color: #fff; }}
            .btn-play:hover {{ background: #0056b3; }}

            .status-dot {{ 
                display: inline-block; width: 10px; height: 10px; 
                border-radius: 50%; background: #555; margin-right: 5px; 
            }}

            .hidden {{ display: none !important; }}
        </style>
    </head>
    <body>

        <div class="header">
            <h1>🔍 PH-TV ULTIMATE FINDER</h1>
            <div class="stats">
                CANAIS LOCALIZADOS: <strong style="color:var(--neon);">{len(canais)}</strong> | 
                ATUALIZADO: {agora}
            </div>
            <input type="text" id="searchBar" placeholder="Pesquisar canal, filme ou esporte..." onkeyup="filter()">
        </div>

        <div class="grid" id="mainGrid">
    """
    
    for i, c in enumerate(canais):
        sid = f"url-{i}"
        html_template += f"""
            <div class="card" data-name="{c['nome']}">
                <strong><span class="status-dot"></span>{c['nome']}</strong>
                <div class="url-box" id="{sid}">{c['url']}</div>
                <div class="actions">
                    <button class="btn-copy" onclick="copyText('{sid}')">COPIAR</button>
                    <a href="https://hls-js.netlify.app/demo/?src={c['url']}" target="_blank" class="btn-play">TESTAR PLAY</a>
                </div>
            </div>
        """
        
    html_template += """
        </div>

        <script>
            function filter() {
                let query = document.getElementById('searchBar').value.toUpperCase();
                let cards = document.getElementsByClassName('card');
                for (let i = 0; i < cards.length; i++) {
                    let name = cards[i].getAttribute('data-name');
                    cards[i].classList.toggle('hidden', !name.includes(query));
                }
            }

            function copyText(id) {
                let text = document.getElementById(id).innerText;
                navigator.clipboard.writeText(text).then(() => {
                    alert("URL Copiada! Jogue no seu Player.");
                });
            }
            
            // Função para tentar verificar status via Client-side (Opcional/Experimental)
            console.log("PH-TV System Ready...");
        </script>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    canais = buscar_links()
    gerar_painel(canais)
    print(f"🚀 Painel gerado com {len(canais)} canais!")

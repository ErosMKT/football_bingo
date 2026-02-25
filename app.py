import streamlit as st
import json
import random
import string
import time
import os
import plotly.graph_objects as go
import importlib
import motor_logica
from streamlit_autorefresh import st_autorefresh
importlib.reload(motor_logica)
from motor_logica import MotorJogo
import glob
import streamlit.components.v1 as components

# Ensure data/rooms exists
os.makedirs("data/rooms", exist_ok=True)

# Configuração da Página
st.set_page_config(page_title="Football Bingo", layout="wide", initial_sidebar_state="collapsed")

# Injeção de CSS Dark/Neon
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,400;0,700;0,900;1,900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif !important;
        background-color: #0d0e15 !important;
        color: #ffffff !important;
    }
    
    h1, h2, h3 {
        color: #f1f2f6 !important;
        text-transform: uppercase;
        font-weight: 900 !important;
        letter-spacing: 1px;
    }
    
    /* Letra Gigante Glowing */
    .glowing-letter {
        font-size: 130px;
        font-weight: 900;
        font-style: italic;
        color: #fff;
        text-shadow: 0 0 10px #00d2ff, 0 0 20px #00d2ff, 0 0 40px #00d2ff;
        text-align: center;
        margin-top: -30px;
        margin-bottom: 20px;
        line-height: 1;
    }
    
    .letter-label {
        font-size: 30px;
        font-weight: 900;
        font-style: italic;
        color: #f1f2f6;
        text-align: center;
        text-transform: uppercase;
    }
    
    /* Inputs Dark Mode */
    .stTextInput > div > div > input {
        background-color: #1a1b26 !important;
        color: #ffffff !important;
        border: 1px solid #00d2ff !important;
        border-radius: 8px !important;
        padding: 12px !important;
        font-size: 16px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3) !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #00ffff !important;
        box-shadow: 0 0 8px #00d2ff !important;
    }
    
    /* Botões Neon */
    .stButton > button {
        background-color: transparent !important;
        color: #ffffff !important;
        border: 2px solid #00d2ff !important;
        border-radius: 10px !important;
        padding: 10px 24px !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 0 10px rgba(0, 210, 255, 0.2) inset, 0 0 10px rgba(0, 210, 255, 0.2) !important;
    }
    .stButton > button:hover {
        background-color: rgba(0, 210, 255, 0.1) !important;
        box-shadow: 0 0 15px rgba(0, 210, 255, 0.5) inset, 0 0 15px rgba(0, 210, 255, 0.5) !important;
        border-color: #00ffff !important;
        color: #fff !important;
    }
    
    /* Containers / Divisórias */
    hr {
        border-color: #333 !important;
    }
    
    /* Métricas */
    [data-testid="stMetricValue"] {
        font-size: 32px !important;
        font-weight: 900 !important;
        color: #00e676 !important; /* Verde Neon */
        text-shadow: 0 0 10px rgba(0, 230, 118, 0.4);
    }
    [data-testid="stMetricLabel"] {
        color: #a0a0b0 !important;
        font-size: 14px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Custom Redesign for Timer Display */
    .timer-display {
        font-size: 45px;
        font-weight: 900;
        color: #ffffff;
        text-align: right;
        margin-top: 20px;
    }
    .timer-label {
        font-size: 12px;
        color: #00d2ff;
        text-transform: uppercase;
        font-weight: bold;
        letter-spacing: 2px;
        text-align: right;
    }
    
    /* Layout Responsivo para o Header do Jogo */
    .game-header-container {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        margin-bottom: 20px;
    }
    .game-header-left {
        flex: 2;
    }
    .letter-display-wrapper {
        display: flex;
        align-items: center;
        margin-left: 10px;
    }
    .pos-display {
        font-size: 50px;
        font-weight: 900;
        color: #fff;
        text-shadow: 0 0 10px #00d2ff, 0 0 20px #00d2ff, 0 0 40px #00d2ff;
        margin-left: 40px;
        text-transform: uppercase;
    }
    .game-header-right {
        flex: 1;
        text-align: right;
    }
    
    /* Adaptações para Smartphone (Mobile) */
    @media (max-width: 768px) {
        /* Reduzir letras gigantes */
        .glowing-letter { font-size: 70px; margin-top: -10px; }
        .pos-display { font-size: 30px; margin-left: 15px; }
        .letter-label { font-size: 18px; }
        .timer-display { font-size: 32px; margin-top: 5px; }
        
        /* Empilhar o painel ao invés de linha no Mobile */
        .game-header-container {
            flex-direction: column;
            align-items: flex-start;
            gap: 15px;
        }
        .game-header-right {
            text-align: left;
            width: 100%;
        }
        .timer-label, .timer-display {
            text-align: left;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Carregar Todas as Táticas
@st.cache_data
def load_taticas_all():
    with open("data/taticas.json", "r") as f:
        return json.load(f)

taticas = load_taticas_all()

# Inicializar Sessão
if "jogo_iniciado" not in st.session_state:
    st.session_state.jogo_iniciado = False
if "tatica_nome" not in st.session_state:
    st.session_state.tatica_nome = "4-3-3"
if "db_path" not in st.session_state:
    st.session_state.db_path = "data/jogadores.csv"
if "show_ranking" not in st.session_state:
    st.session_state.show_ranking = False

# Previne renderização do motor antes de escolher DB
if st.session_state.jogo_iniciado:
    @st.cache_resource
    def load_motor_with_path(path):
        return MotorJogo(data_path=path)
        
    motor = load_motor_with_path(st.session_state.db_path)
    tatica_base = taticas[st.session_state.tatica_nome]

    if "pontuacao" not in st.session_state:
        st.session_state.pontuacao = 0
    if "pulos_usados" not in st.session_state:
        st.session_state.pulos_usados = 0
    if "categorias_usadas" not in st.session_state:
        st.session_state.categorias_usadas = {"LENDA": 0, "FOLCLORICO/HISTORICO": 0, "JOGADOR BASE": 0}
    if "posicoes_preenchidas" not in st.session_state:
        st.session_state.posicoes_preenchidas = {}
    if "start_time" not in st.session_state:
        st.session_state.start_time = time.time()
    if "end_time" not in st.session_state:
        st.session_state.end_time = None
        
    if "tracking_faltando" not in st.session_state:
        st.session_state.tracking_faltando = {}
    if "tracking_terminaram" not in st.session_state:
        st.session_state.tracking_terminaram = set()
        
    if "posicao_selecionada" not in st.session_state:
        posicoes_livres = [p['id'] for p in tatica_base]
        st.session_state.posicao_selecionada = random.choice(posicoes_livres) if posicoes_livres else None

    # Pega o nome da posição selecionada para sortear letra válida (se possível)
    def get_pos_str(pos_id):
        for p in tatica_base:
            if p['id'] == pos_id:
                return p['posicao']
        return ""

    if "letra_atual" not in st.session_state:
        st.session_state.letra_atual = motor.sortear_letra_valida(get_pos_str(st.session_state.posicao_selecionada))

# --- FUNÇÃO PARA DESENHAR O CAMPO ---
def desenhar_campo(tatica):
    fig = go.Figure()

    # Desenhar gramado listrado (estilo Dark Neon)
    cores_grama = ["#10121a", "#151822"] # Tons dark/cyberpunk
    cor_linha = "rgba(180, 190, 200, 0.4)"   # Cool gray lines
    
    # Adicionar faixas verticais para simular o corte da grama
    for i in range(10):
        x0 = i * 10
        x1 = (i + 1) * 10
        cor = cores_grama[i % 2]
        fig.add_shape(type="rect", x0=x0, y0=0, x1=x1, y1=100, fillcolor=cor, line=dict(width=0), layer="below")
        
    # Bordas marginais do campo
    fig.add_shape(type="rect", x0=2, y0=2, x1=98, y1=98, line=dict(color=cor_linha, width=2), fillcolor="rgba(0,0,0,0)")
    
    # Linha central
    fig.add_shape(type="line", x0=50, y0=2, x1=50, y1=98, line=dict(color=cor_linha, width=2))
    
    # Círculo central
    fig.add_shape(type="circle", x0=40, y0=40, x1=60, y1=60, line=dict(color=cor_linha, width=2))
    fig.add_shape(type="circle", x0=49.5, y0=49.5, x1=50.5, y1=50.5, fillcolor=cor_linha, line=dict(color=cor_linha, width=1)) 
    
    # Áreas de Pênalti
    # Esquerda
    fig.add_shape(type="rect", x0=2, y0=25, x1=18, y1=75, line=dict(color=cor_linha, width=2), fillcolor="rgba(0,0,0,0)")
    fig.add_shape(type="rect", x0=2, y0=38, x1=8, y1=62, line=dict(color=cor_linha, width=2), fillcolor="rgba(0,0,0,0)")
    fig.add_shape(type="circle", x0=13.5, y0=49.5, x1=14.5, y1=50.5, fillcolor=cor_linha, line=dict(color=cor_linha, width=1)) 
    
    # Direita
    fig.add_shape(type="rect", x0=82, y0=25, x1=98, y1=75, line=dict(color=cor_linha, width=2), fillcolor="rgba(0,0,0,0)")
    fig.add_shape(type="rect", x0=92, y0=38, x1=98, y1=62, line=dict(color=cor_linha, width=2), fillcolor="rgba(0,0,0,0)")
    fig.add_shape(type="circle", x0=85.5, y0=49.5, x1=86.5, y1=50.5, fillcolor=cor_linha, line=dict(color=cor_linha, width=1)) 
    
    # Adicionando os Jogadores
    for p in tatica:
        pid = p['id']
        
        # Transformação das coordenadas (de vertical de cima-baixo para horizontal esquerda-direita)
        plot_x = 100 - p['y']
        plot_y = p['x']
        
        cor_ponto = "#1a1b26"
        cor_borda = "rgba(255, 255, 255, 0.2)"
        largura_borda = 2
        texto_dentro = str(pid)
        texto_fonte_cor = "#bbbbbb"
        
        nome_exibicao = ""
        
        posicoes_preenchidas = st.session_state.get("posicoes_preenchidas", {})
        
        if pid in posicoes_preenchidas:
            info = posicoes_preenchidas[pid]
            cat = info['categoria']
            
            # Estilo diferente quando acertado
            if cat == "LENDA":
                cor_ponto = "#ffd700" # Dourado 
                texto_fonte_cor = "#000"
                cor_borda = "rgba(255, 215, 0, 0.8)"
            elif cat == "FOLCLORICO/HISTORICO":
                cor_ponto = "#c0c0c0" # Prata
                texto_fonte_cor = "#000"
                cor_borda = "rgba(192, 192, 192, 0.8)"
            else:
                cor_ponto = "#00e676" # Verde neon
                texto_fonte_cor = "#000"
                cor_borda = "rgba(0, 230, 118, 0.8)"
                
            nome_exibicao = info['nome']
            
        # Destaque para a posição selecionada no momento (pisca/chama atenção)
        posicao_selecionada = st.session_state.get("posicao_selecionada", None)
        if pid == posicao_selecionada:
             cor_borda = "#00d2ff" # Cyan/Blue brilhante
             largura_borda = 4
             texto_fonte_cor = "#fff"
             
        # Marker (Círculo)
        fig.add_trace(go.Scatter(
            x=[plot_x],
            y=[plot_y],
            mode="markers+text",
            marker=dict(size=40, color=cor_ponto, line=dict(width=largura_borda, color=cor_borda)),
            text=[texto_dentro],
            textposition="middle center",
            textfont=dict(color=texto_fonte_cor, size=18, family="Arial Black"),
            name=str(pid),
            hoverinfo="none",
            hoverlabel=dict(bgcolor="white", font_size=16)
        ))
        
        # Etiqueta de Texto Abaixo do Jogador
        texto_etiqueta = f"<b>{nome_exibicao}</b>" if nome_exibicao else p['posicao']
        
        fig.add_annotation(
            x=plot_x,
            y=plot_y - 7.5, # Desce um pouquinho para ficar fora do círculo
            text=texto_etiqueta,
            showarrow=False,
            font=dict(color="white", size=14, family="Arial Black" if nome_exibicao else "Arial")
        )

    fig.update_layout(
        width=None, # Allow Streamlit to manage width via use_container_width
        height=450, # Reduced height from 550 to 450 to fit on screen
        margin=dict(l=0, r=0, t=0, b=0), # Remove margins
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 100]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 100]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False
    )
    
    return fig

st.title("⚽ Football Bingo-Stop")

# --- FUNÇÕES P/ LEADERBOARD ---
def carregar_leaderboard():
    caminho_hist = "data/historico.json"
    if not os.path.exists(caminho_hist):
        return []
    try:
        with open(caminho_hist, "r") as f:
            dados = json.load(f)
            # Ordena por menor tempo primeiro, e em caso de empate, maior pontuação
            return sorted(dados, key=lambda x: (x.get("tempo_segundos", float('inf')), -x.get("pontuacao", 0)))
    except:
        return []

def salvar_no_leaderboard(nome, tempo_str, tempo_segundos, pontuacao, tatica, modo="Time Attack"):
    caminho_hist = "data/historico.json"
    historico = carregar_leaderboard()
    novo_registro = {
        "nome": nome,
        "tempo_str": tempo_str,
        "tempo_segundos": tempo_segundos,
        "pontuacao": pontuacao,
        "tatica": tatica,
        "modo": modo,
        "data": time.strftime("%d/%m/%Y")
    }
    historico.append(novo_registro)
    with open(caminho_hist, "w") as f:
        json.dump(historico, f, indent=4)


if not st.session_state.jogo_iniciado:
    room_param = st.query_params.get("room")
    
    # ------------------ LOBBY MULTIPLAYER ------------------
    if room_param:
        st.subheader(f"🎮 Lobby da Sala: {room_param}")
        
        if st.session_state.get("is_host"):
            st.success("👑 **Você é o Anfitrião (Host) desta partida!**")
            st.write("Convide seus amigos enviando o link abaixo:")
            
            # Streamlit components.v1.html runs in an iframe (about:srcdoc).
            # To get the parent URL, we use JS: window.parent.location.href
            import streamlit.components.v1 as components
            components.html(
                f"""
                <div style="font-family: sans-serif; padding: 10px; border: 1px solid #444; border-radius: 5px; background: #1e1e1e; color: white;">
                    <input type="text" id="link-input" readonly style="width: 70%; padding: 8px; border-radius: 4px; border: 1px solid #555; background: #2d2d2d; color: white;">
                    <button onclick="copyLink()" style="padding: 8px 15px; margin-left: 5px; border-radius: 4px; border: none; background: #ff4b4b; color: white; cursor: pointer; font-weight: bold;">Copiar Link</button>
                    <p id="msg" style="margin: 8px 0 0 0; font-size: 13px; color: #4CAF50; display: none;">✔️ Link copiado para a área de transferência!</p>
                </div>
                <script>
                    // Pega a URL da janela pai (Streamlit root)
                    var parentUrl = window.parent.location.href; 
                    document.getElementById('link-input').value = parentUrl;
                    
                    function copyLink() {{
                        var copyText = document.getElementById("link-input");
                        // Seleciona o texto
                        copyText.select();
                        copyText.setSelectionRange(0, 99999); // Para mobile
                        // Copia via comando de documento (mais seguro em iframes)
                        document.execCommand("copy");
                        
                        document.getElementById('msg').style.display = 'block';
                        setTimeout(function(){{ document.getElementById('msg').style.display = 'none'; }}, 3000);
                    }}
                </script>
                """,
                height=110
            )

        meta_file = f"data/rooms/{room_param}_meta.json"
        if not os.path.exists(meta_file):
            st.error("Sala não encontrada ou expirada.")
            if st.button("Voltar ao Menu Principal"):
                st.query_params.clear()
                st.rerun()
        else:
            if "player_name" not in st.session_state:
                st.write("Junte-se aos seus amigos para a Batalha Tática!")
                with st.form("join_form"):
                    nome_jogador = st.text_input("Seu Nickname:")
                    btn_entrar = st.form_submit_button("Entrar na Sala")
                    if btn_entrar and nome_jogador:
                        st.session_state.player_name = nome_jogador
                        st.session_state.is_multiplayer = True
                        st.session_state.room_id = room_param
                        # Cria o arquivo do player zerado
                        player_file = f"data/rooms/{room_param}_player_{nome_jogador}.json"
                        with open(player_file, "w") as f:
                            json.dump({
                                "nome": nome_jogador,
                                "pontuacao": 0,
                                "posicoes_faltando": 11,
                                "terminou": False,
                                "tempo_final": None
                            }, f)
                        st.rerun()
            else:
                # O jogador está no lobby esperando
                st_autorefresh(interval=2000, key="lobby_refresh")
                
                with open(meta_file, "r") as f:
                    meta = json.load(f)
                    
                if meta.get("status") == "jogando":
                    st.session_state.jogo_iniciado = True
                    st.session_state.start_time = meta["start_time"]
                    st.session_state.end_time = None
                    st.session_state.tatica_nome = meta["tatica"]
                    st.session_state.db_path = meta["db_path"]
                    st.session_state.modo_multi = meta.get("modo", "BR")
                    st.session_state.morte_subita = meta.get("morte_subita", False)
                    st.rerun()
                
                st.write("### Jogadores na Sala:")
                player_files = glob.glob(f"data/rooms/{room_param}_player_*.json")
                for pf in player_files:
                    try:
                        with open(pf, "r") as f:
                            pdata = json.load(f)
                            st.markdown(f"- **{pdata['nome']}**")
                    except:
                        pass
                
                if st.session_state.get("is_host"):
                    st.divider()
                    if st.button("▶️ INICIAR PARTIDA DO LOBBY", use_container_width=True, type="primary"):
                        meta["status"] = "jogando"
                        meta["start_time"] = time.time()
                        meta["tatica"] = random.choice(list(taticas.keys()))
                        with open(meta_file, "w") as f:
                            json.dump(meta, f)
                        st.rerun()
                else:
                    st.info("Aguardando o anfitrião iniciar a partida...")
                    
                if st.button("Sair da Sala"):
                    st.query_params.clear()
                    try:
                        os.remove(f"data/rooms/{room_param}_player_{st.session_state.player_name}.json")
                    except:
                        pass
                    if "player_name" in st.session_state: del st.session_state.player_name
                    if "is_multiplayer" in st.session_state: del st.session_state.is_multiplayer
                    if "room_id" in st.session_state: del st.session_state.room_id
                    if "is_host" in st.session_state: del st.session_state.is_host
                    st.rerun()
                    
    # ------------------ CRIAR NOVO JOGO ------------------
    elif not st.session_state.show_ranking:
        col_campo, col_controles = st.columns([3, 1])
        
        # Carrega a tática apenas para exibição visual no Menu (usando 4-3-3 como padrão)
        with open("data/taticas.json", "r") as f:
            taticas_menu = json.load(f)
        tatica_base_menu = taticas_menu.get(st.session_state.tatica_nome, taticas_menu["4-3-3"])
        
        with col_campo:
            fig_campo = desenhar_campo(tatica_base_menu)
            # config={'staticPlot': True} desabilita pan/zoom em celulares
            st.plotly_chart(fig_campo, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
            
        with col_controles:
            st.markdown("### Configuração da Partida")
            st.write("Antes de entrar em campo, defina as configurações da sua partida:")
            
            modo_jogo = st.radio("Selecione o Modo:", ["🏁 Time Attack (Single Player)", "⏱️ Corrida Contra o Relógio (Single Player)", "⚔️ Battle Royale (Multiplayer)", "🤺 X1 (Mano a Mano)"])
            
            # Escanear CSVs garantindo o sync manual da pasta Google Drive, se possível
            import glob
            import shutil
            origem_drive = r"G:\My Drive\Antigravity\football_bingo\data"
            
            if os.path.exists(origem_drive):
                for f in glob.glob(os.path.join(origem_drive, "*.csv")):
                    nome_arq = os.path.basename(f)
                    dest_local = os.path.join("data", nome_arq)
                    try:
                        shutil.copy2(f, dest_local)
                    except Exception as e:
                        pass
                        
            arquivos_csv = glob.glob("data/*.csv")
            
            opcoes_db = {}
            if not arquivos_csv:
                # Fallback se não tiver nada
                opcoes_db["jogadores (Padrão)"] = "data/jogadores.csv"
            else:
                for arq in arquivos_csv:
                    # Extrai nome limpo (Ex: data/jogadores_br.csv -> jogadores_br)
                    nome_limpo = os.path.basename(arq).replace(".csv", "")
                    opcoes_db[nome_limpo] = arq
                    
            db_selecionada = st.selectbox(
                "Base de Dados:",
                list(opcoes_db.keys())
            )
            st.session_state.db_path = opcoes_db[db_selecionada]
                
            st.info("A Formação Tática será escolhida aleatoriamente pelo jogo para aumentar o desafio!")
                
            st.divider()
            
            # Request Player Name for Single Player modes before starting
            if "Single Player" in modo_jogo:
                nome_jogador = st.text_input("✍️ Seu Nome (para o Ranking Final):", value=st.session_state.get("player_name", ""))
            
            if modo_jogo == "🏁 Time Attack (Single Player)":
                if st.button("▶️ INICIAR TIME ATTACK", use_container_width=True, type="primary"):
                    if not nome_jogador:
                        st.error("Digite o seu nome antes de iniciar!")
                    else:
                        st.session_state.player_name = nome_jogador
                        st.session_state.tatica_nome = random.choice(list(taticas.keys()))
                        st.session_state.is_multiplayer = False
                        st.session_state.jogo_iniciado = True
                        st.session_state.start_time = time.time()
                        st.session_state.end_time = None
                        st.session_state.modo_atual_single = "Time Attack"
                        st.session_state.recorde_salvo = False # Reseta a flag
                        st.rerun()
            elif modo_jogo == "⏱️ Corrida Contra o Relógio (Single Player)":
                st.info("⚠️ Você tem 60s (1 min) por jogador. Se o tempo zerar ou você pular, sofrerá punições rígidas: Advertência -> Falta -> Amarelo -> Vermelho (Fim de Jogo)!")
                if st.button("▶️ INICIAR CORRIDA", use_container_width=True, type="primary"):
                    if not nome_jogador:
                        st.error("Digite o seu nome antes de iniciar!")
                    else:
                        st.session_state.player_name = nome_jogador
                        st.session_state.tatica_nome = random.choice(list(taticas.keys()))
                        st.session_state.is_multiplayer = False
                        st.session_state.jogo_iniciado = True
                        st.session_state.start_time = time.time() # Tempo local da posição
                        st.session_state.tempo_global = time.time() # Tempo total da partida
                        st.session_state.end_time = None
                        st.session_state.penalidades = 0 # 0, 1, 2, 3 (Red)
                        st.session_state.modo_atual_single = "Corrida Relogio"
                        st.session_state.recorde_salvo = False # Reseta a flag
                        st.rerun()
            elif modo_jogo == "⚔️ Battle Royale (Multiplayer)":
                st.info("💡 Battle Royale é ideal para 3 a 10 jogadores simultâneos!")
                morte_subita = st.checkbox("Habilitar Morte Súbita (Encerra a partida p/ todos quando 75% finalizarem)", value=True)
                if st.button("⚔️ CRIAR SALA BATTLE ROYALE", use_container_width=True, type="primary"):
                    novo_room = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
                    meta_file = f"data/rooms/{novo_room}_meta.json"
                    with open(meta_file, "w") as f:
                        json.dump({
                            "status": "aguardando",
                            "start_time": None,
                            "tatica": None,
                            "db_path": st.session_state.db_path,
                            "modo": "BR",
                            "morte_subita": morte_subita
                        }, f)
                    
                    st.query_params.update({"room": novo_room})
                    st.session_state.is_host = True
                    st.rerun()
            elif modo_jogo == "🤺 X1 (Mano a Mano)":
                if st.button("🤺 CRIAR SALA X1", use_container_width=True, type="primary"):
                    novo_room = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
                    meta_file = f"data/rooms/{novo_room}_meta.json"
                    with open(meta_file, "w") as f:
                        json.dump({
                            "status": "aguardando",
                            "start_time": None,
                            "tatica": None,
                            "db_path": st.session_state.db_path,
                            "modo": "X1"
                        }, f)
                    
                    st.query_params.update({"room": novo_room})
                    st.session_state.is_host = True
                    st.rerun()
                
        with col_controles:
            st.markdown("### 🏆 Hall da Fama")
            st.info("Veja os recordes globais de velocidade e pontuação dos Modos Single Player!")
            if st.button("🏅 VER RANKINGS GLOBAIS", use_container_width=True):
                st.session_state.show_ranking = True
                st.rerun()

# --------------- TELA DEDICADA DE RANKINGS ---------------
if st.session_state.show_ranking and not st.session_state.jogo_iniciado:
    st.markdown("<h2 style='text-align: center; color: #00d2ff;'>🏆 RANKINGS GLOBAIS 🏆</h2>", unsafe_allow_html=True)
    st.divider()
        
    tab_ta, tab_cr = st.tabs(["🏁 TIME ATTACK", "⏱️ CORRIDA CONTRA O RELÓGIO"])
    
    leaderboard = carregar_leaderboard()
    
    # Estilo CSS para a tabela
    tabela_css = """
    <style>
    .ranking-table { width: 100%; border-collapse: collapse; margin-bottom: 20px;}
    .ranking-table th, .ranking-table td { padding: 12px; text-align: left; border-bottom: 1px solid #333; }
    .ranking-table th { background-color: #1a1b26; color: #00d2ff; text-transform: uppercase; letter-spacing: 1px;}
    .ranking-table tr:hover { background-color: #222; }
    .medal-gold { color: gold; font-size: 20px; }
    .medal-silver { color: silver; font-size: 20px; }
    .medal-bronze { color: #cd7f32; font-size: 20px; }
    </style>
    """
    st.markdown(tabela_css, unsafe_allow_html=True)
    
    def render_table(dados, is_time_attack=True):
        if not dados:
            st.warning("Ainda não há recordes registrados neste modo. Seja o primeiro!")
            return
            
        html = '<table class="ranking-table"><tr><th>Pos</th><th>Nome</th><th>Score</th><th>Tempo</th><th>Tática</th><th>Data</th></tr>'
        for i, reg in enumerate(dados[:10]):
            icone = f"{i+1}º"
            if i == 0: icone = "<span class='medal-gold'>🥇</span>"
            elif i == 1: icone = "<span class='medal-silver'>🥈</span>"
            elif i == 2: icone = "<span class='medal-bronze'>🥉</span>"
            
            html += f"""<tr>
                <td><b>{icone}</b></td>
                <td style='color:#fff; font-weight:bold;'>{reg.get('nome', '---')}</td>
                <td style='color:#00e676; font-weight:bold;'>{reg.get('pontuacao', '0')} PTS</td>
                <td style='color:#bbb;'>{reg.get('tempo_str', '---')}</td>
                <td style='color:#bbb;'>{reg.get('tatica', '---')}</td>
                <td style='color:#777; font-size: 12px;'>{reg.get('data', '---')}</td>
            </tr>"""
        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)
        
    with tab_ta:
        # Time Attack prioriza menor tempo, em caso de empate, maior pontuação
        dados_ta = [r for r in leaderboard if not r.get("modo") or r.get("modo") == "Time Attack"]
        dados_ta_sorted = sorted(dados_ta, key=lambda x: (x.get("tempo_segundos", float('inf')), -x.get("pontuacao", 0)))
        render_table(dados_ta_sorted, True)
        
    with tab_cr:
        # Corrida Contra o Relógio prioriza maior Pontuação
        dados_cr = [r for r in leaderboard if r.get("modo") == "Corrida Relogio"]
        dados_cr_sorted = sorted(dados_cr, key=lambda x: (-x.get("pontuacao", 0), x.get("tempo_segundos", float('inf'))))
        render_table(dados_cr_sorted, False)

    st.divider()
    col_voltar, _, _ = st.columns([1, 1, 1])
    with col_voltar:
        if st.button("🔙 VOLTAR AO MENU PRINCIPAL", use_container_width=True, type="secondary"):
            st.session_state.show_ranking = False
            st.rerun()

elif st.session_state.jogo_iniciado:
    # Layout do Jogo: Esquerda (Controles & Info) / Direita (Campo Tático)
    col1, col2 = st.columns([1.5, 2.5])
    
    with col1:
        # Pega a posição alvo
        posicoes_disponiveis = [p['id'] for p in tatica_base if p['id'] not in st.session_state.posicoes_preenchidas]
        escolha = st.session_state.posicao_selecionada
        pos_str = get_pos_str(escolha) if escolha else ""
        
        # --- Lógica do Cronômetro ---
        modo_atual = st.session_state.get("modo_atual_single", "Time Attack")
        if st.session_state.get("is_multiplayer"):
            modo_atual = st.session_state.get("modo_multi", "BR")
            
        tempo_str = "00:00"
        tempo_decorrido = 0
            
        if st.session_state.end_time is None:
            st_autorefresh(interval=1000, key="timer_refresh")
            
            if modo_atual == "Corrida Relogio":
                tempo_decorrido = time.time() - st.session_state.start_time
                tempo_restante = max(0, 60 - int(tempo_decorrido))
                mins, secs = divmod(tempo_restante, 60)
                tempo_str = f"⏱️ {mins:02d}:{secs:02d}"
                
                # Handling Timeout penalty
                if tempo_restante <= 0:
                    current_penalties = 0
                    if "penalidades" in st.session_state:
                         current_penalties = st.session_state.penalidades
                    st.session_state.penalidades = current_penalties + 1
                    
                    if st.session_state.penalidades >= 4:
                        st.session_state.posicao_selecionada = None
                        st.session_state.end_time = time.time() # Game Over
                        st.session_state.game_over_derrota = True
                        st.toast("🟥 CARTÃO VERMELHO! O seu tempo esgotou e você foi EXPULSO!", icon="🟥")
                    else:
                        st.toast(f"⚠️ TEMPO ESGOTADO! Penalidade {st.session_state.penalidades}/4 aplicada.", icon="⏱️")
                        prox_posicoes = [p['id'] for p in tatica_base if p['id'] not in st.session_state.posicoes_preenchidas and p['id'] != escolha]
                        if prox_posicoes:
                            prox_pos = random.choice(prox_posicoes)
                            st.session_state.posicao_selecionada = prox_pos
                            st.session_state.letra_atual = motor.sortear_letra_valida(get_pos_str(prox_pos))
                            st.session_state.start_time = time.time() # Reset 60s timer
                        else:
                            st.session_state.posicao_selecionada = None
                            st.session_state.end_time = time.time()
                    st.rerun()
            else:
                tempo_decorrido = time.time() - st.session_state.start_time
                mins, secs = divmod(int(tempo_decorrido), 60)
                tempo_str = f"{mins:02d}:{secs:02d}"
        else:
            if modo_atual == "Corrida Relogio":
                tempo_decorrido = st.session_state.end_time - st.session_state.get("tempo_global", st.session_state.start_time)
            else:
                tempo_decorrido = st.session_state.end_time - st.session_state.start_time
            mins, secs = divmod(int(tempo_decorrido), 60)
            tempo_str = f"{mins:02d}:{secs:02d}"
        
        # Alerta de Raridade
        raridade_ui = ""
        letra_u = st.session_state.letra_atual.upper() if st.session_state.letra_atual else ""
        if pos_str and not motor.mapa_letras.empty and pos_str in motor.mapa_letras.index and letra_u in motor.mapa_letras.columns:
            qtd = motor.mapa_letras.loc[pos_str, letra_u]
            if qtd == 1:
                raridade_ui = "<span style='color:gold; font-size:14px; margin-left:10px;'>🦄💎 UNICORN (Única opção)</span>"
            elif 2 <= qtd <= 3:
                raridade_ui = "<span style='color:#00d2ff; font-size:14px; margin-left:10px;'>💎 RARE (2-3 opções)</span>"
                
        # --- Interface Header (Letra, Posição & Relógio) ---
        if escolha:
            letra = st.session_state.letra_atual
            num_pos = f"(Nº {escolha})"
            pos_display = f"{pos_str} <span style='font-size: 20px; color: #aaa; text-shadow: none; font-weight: normal; vertical-align: middle;'>{num_pos}</span>"
            
            html_code = f"""
<div class="game-header-container">
    <div class="game-header-left">
        <div class="letter-label" style="margin-bottom: 10px;">TARGET LETTER & POSITION {raridade_ui}</div>
        <div class="letter-display-wrapper">
            <div class="glowing-letter" style="text-align: left; margin-bottom: 0px;">{letra}</div>
            <div class="pos-display">
                {pos_display}
            </div>
        </div>
    </div>
    <div class="game-header-right">
        <div class="timer-label">TIME REMAINING</div>
        <div class="timer-display">{tempo_str}</div>
    </div>
</div>
"""
            st.markdown(html_code, unsafe_allow_html=True)
            # Layout simplificado para Fim de Jogo (sem letra/posição quebram o HTML)
            st.markdown(f"""
<div class="game-header-container" style="justify-content: flex-end;">
    <div class="game-header-right">
        <div class="timer-label">TOTAL TIME</div>
        <div class="timer-display" style="color: #aaa;">{tempo_str}</div>
    </div>
</div>
""", unsafe_allow_html=True)

        # --- Métricas Menores (Pontos / Pulos / Penalidades) ---
        if modo_atual == "Corrida Relogio" or modo_atual == "Corrida Relogio Hardcore":
            c_m1, c_m2, c_m3 = st.columns(3)
            c_m1.metric("SCORE", f"{st.session_state.pontuacao} PTS")
            
            pns = st.session_state.get("penalidades", 0)
            status_pena = "🟩 Limpo"
            if pns == 1: status_pena = "⚠️ Adv."
            elif pns == 2: status_pena = "🛑 Falta"
            elif pns == 3: status_pena = "🟨 Amarelo"
            elif pns >= 4: status_pena = "🟥 Vermelho"
            
            c_m2.metric("PENALTIES", status_pena)
        else:
            c_m1, c_m2, c_m3 = st.columns(3)
            c_m1.metric("SCORE", f"{st.session_state.pontuacao} PTS")
            c_m2.metric("SKIPS", f"{st.session_state.pulos_usados}/3")
        
        # ------- MULTIPLAYER SYNC E PLACAR DA SALA -------
        if st.session_state.get("is_multiplayer"):
            room = st.session_state.get("room_id")
            nome = st.session_state.get("player_name")
            if room and nome:
                falta = sum(1 for p in tatica_base if p['id'] not in st.session_state.posicoes_preenchidas)
                
                # Salva estado atual
                state_file = f"data/rooms/{room}_player_{nome}.json"
                try:
                    with open(state_file, "w") as f:
                        json.dump({
                            "nome": nome,
                            "pontuacao": st.session_state.pontuacao,
                            "posicoes_faltando": falta,
                            "terminou": falta == 0,
                            "tempo_final": st.session_state.end_time,
                            "categorias_usadas": st.session_state.get("categorias_usadas", {})
                        }, f)
                except:
                    pass
                
                # Lê o estado da sala para mostrar o placar
                player_files = glob.glob(f"data/rooms/{room}_player_*.json")
                sala_dados = []
                for pf in player_files:
                    try:
                        with open(pf, "r") as f:
                            sala_dados.append(json.load(f))
                    except:
                        pass
                
                # --- LÓGICA DE ALERTAS E MORTE SÚBITA ---
                terminados_count = 0
                for r_d in sala_dados:
                    p_name = r_d['nome']
                    p_falta = r_d.get('posicoes_faltando', 11)
                    p_terminou = r_d.get('terminou', False)
                    
                    if p_name != nome:
                        # Alertas X1
                        if st.session_state.get("modo_multi") == "X1":
                            anterior_falta = st.session_state.tracking_faltando.get(p_name, 11)
                            if p_falta < anterior_falta:
                                st.toast(f"🚨 {p_name} escalou um jogador! Faltam {p_falta} posições para ele.", icon="⚠️")
                            st.session_state.tracking_faltando[p_name] = p_falta
                            
                        # Alertas BR
                        if p_terminou and p_name not in st.session_state.tracking_terminaram:
                            st.toast(f"🔥 {p_name} FINALIZOU A CARTELA!", icon="🏆")
                            st.session_state.tracking_terminaram.add(p_name)
                    
                    if p_terminou:
                        terminados_count += 1
                
                # Verifica a morte súbita apenas se quem está jogando não terminou
                qtd_jogadores = len(sala_dados)
                if st.session_state.get("morte_subita", False) and st.session_state.get("modo_multi") == "BR" and qtd_jogadores > 1 and falta > 0:
                    if terminados_count >= (qtd_jogadores * 0.75):
                        # Forçar o game over local do jogador que não terminou a tempo
                        st.session_state.posicao_selecionada = None
                        st.session_state.end_time = time.time()
                        st.warning("💀 MORTE SÚBITA! O jogo encerrou para você!")
                        time.sleep(2)
                        st.rerun()
                
                # Renderizar Leaderboard ao vivo em um expander estilizado
                with st.expander("🏆 PLACAR AO VIVO DA SALA", expanded=False):
                    sala_dados.sort(key=lambda x: (x.get('posicoes_faltando', 11), -x.get('pontuacao', 0)))
                    for r in sala_dados:
                        txt_falta = f"Faltam {r['posicoes_faltando']}" if not r.get('terminou') else "🏁 TERMINOU"
                        st.markdown(f"<span style='color:#a0a0b0'><b>{r['nome']}</b></span> &nbsp; <span style='color:#00e676'>{r.get('pontuacao', 0)} pts</span> &nbsp; | &nbsp; <i>{txt_falta}</i>", unsafe_allow_html=True)

        
        # Seleção de Posição & Input
        if st.session_state.end_time is None and posicoes_disponiveis:
            
            # --- Auto Focus Script ---
            # Injéta um mini-script JS invisível para focar no Input toda vez que a página recarregar ou uma tecla for digitada no documento
            components.html(
                """
                <script>
                function setFocus() {
                    var inputs = window.parent.document.querySelectorAll('input[type="text"]');
                    if (inputs.length > 0) {
                        inputs[0].focus();
                    }
                }
                // Foco inicial
                setFocus();
                
                // Adiciona um listener no documento pai para redirecionar o foco ao digitar qualquer tecla (se não estiver num campo input)
                window.parent.document.addEventListener('keydown', function(e) {
                    // Não intercepta se o usuário já estiver num input
                    if (e.target.tagName.toLowerCase() !== 'input' && e.target.tagName.toLowerCase() !== 'textarea') {
                        // Evitar interceptar teclas de controle puras (como F5, Ctrl+C etc) p/ redirecionar só quando for letra, número etc
                        if (e.key.length === 1) { 
                            var inputs = window.parent.document.querySelectorAll('input[type="text"]');
                            if (inputs.length > 0) {
                                inputs[0].focus();
                            }
                        }
                    }
                });
                </script>
                """,
                height=0,
                width=0,
            )
    
            with st.form("guess_form", clear_on_submit=True):
                palpite = st.text_input("Player Name:", key="palpite_input", placeholder="e.g. Someone starting with E", label_visibility="collapsed")
                submit_button = st.form_submit_button("STOP! (SUBMIT)")
                    
            st.write("")
            
            # Botões de Pulo/Penalidade
            st.markdown("<div style='font-size: 11px; color: #888; margin-bottom: 5px; text-transform: uppercase;'>ACTIONS</div>", unsafe_allow_html=True)
            
            if modo_atual == "Corrida Relogio":
                if st.button("SKIP / NEXT (+1 Penalidade)", type="secondary"):
                    # Fix linter by explicitly managing the integer
                    current_penalties = 0
                    if "penalidades" in st.session_state:
                        current_penalties = st.session_state.penalidades
                    
                    st.session_state.penalidades = current_penalties + 1
                    
                    if st.session_state.penalidades >= 4:
                        st.session_state.posicao_selecionada = None
                        st.session_state.end_time = time.time() # Game Over
                        st.session_state.game_over_derrota = True
                        st.toast("🟥 CARTÃO VERMELHO! Você saltou demais e foi EXPULSO!", icon="🟥")
                    else:
                        st.session_state.letra_atual = motor.sortear_letra_valida(pos_str)
                        st.session_state.start_time = time.time() # Reset 60s timer
                    st.rerun()
            else:
                if st.session_state.pulos_usados < 3:
                    col_skip1, col_skip2 = st.columns(2)
                    with col_skip1:
                        if st.button("SKIP LETTER"):
                            deducao, novos_pulos, msg = motor.processar_pulo(st.session_state.pulos_usados)
                            st.session_state.pontuacao += deducao
                            st.session_state.pulos_usados = novos_pulos
                            st.session_state.letra_atual = motor.sortear_letra_valida(pos_str)
                            st.rerun()
                    with col_skip2:
                        if st.button("CHANGE POSITION", key="btn_pos"):
                            deducao, novos_pulos, msg = motor.processar_pulo(st.session_state.pulos_usados)
                            st.session_state.pontuacao += deducao
                            st.session_state.pulos_usados = novos_pulos
                            
                            outras_posicoes = [p for p in posicoes_disponiveis if p != escolha]
                            if outras_posicoes:
                                st.session_state.posicao_selecionada = random.choice(outras_posicoes)
                                st.rerun()
                            else:
                                st.error("No other positions left!")
                else:
                    st.error("🚨 Skips exhausted! Penalties apply.")
                    col_skip1, col_skip2 = st.columns(2)
                    with col_skip1:
                        if st.button("NEW LETTER (-10 PTS)"):
                            st.session_state.pontuacao -= 10
                            st.session_state.pulos_usados += 1
                            st.session_state.letra_atual = motor.sortear_letra_valida(pos_str)
                            st.rerun()
                    with col_skip2:
                        if st.button("GIVE UP POSITION"):
                            st.session_state.pulos_usados += 1
                            st.session_state.posicoes_preenchidas[escolha] = {"nome": "UNFILLED", "categoria": "JOGADOR BASE"}
                            prox_posicoes = [p['id'] for p in tatica_base if p['id'] not in st.session_state.posicoes_preenchidas]
                            if prox_posicoes:
                                prox_pos = random.choice(prox_posicoes)
                                st.session_state.posicao_selecionada = prox_pos
                                st.session_state.letra_atual = motor.sortear_letra_valida(get_pos_str(prox_pos))
                            else:
                                st.session_state.posicao_selecionada = None
                                st.session_state.end_time = time.time()
                            st.rerun()
            
            # Refresh DB just in case
            if st.button("🔄 REFRESH DB"):
                st.cache_resource.clear()
                st.session_state.letra_atual = load_motor_with_path(st.session_state.db_path).sortear_letra_valida(get_pos_str(st.session_state.posicao_selecionada))
                st.rerun()
                
            if submit_button:
                if palpite:
                    # Resgata estado real da sala se for multiplayer para uso de categorias globally
                    is_multi = st.session_state.get("is_multiplayer", False)
                    modo_atual = st.session_state.get("modo_multi", "Time Attack") if is_multi else "Time Attack"
                    
                    categorias_para_validacao = st.session_state.categorias_usadas.copy()
                    
                    if is_multi and st.session_state.get("room_id"):
                        room = st.session_state.get("room_id")
                        player_files = glob.glob(f"data/rooms/{room}_player_*.json")
                        categorias_globais = {"LENDA": 0, "FOLCLORICO/HISTORICO": 0, "JOGADOR BASE": 0}
                        for pf in player_files:
                            try:
                                with open(pf, "r") as f:
                                    dados = json.load(f)
                                    cat_p = dados.get("categorias_usadas", {})
                                    for k, v in cat_p.items():
                                        categorias_globais[k] = categorias_globais.get(k, 0) + v
                            except: pass
                        categorias_para_validacao = categorias_globais
                        
                    status, msg, pontos, row = motor.validar_palpite(palpite, st.session_state.letra_atual, pos_str, categorias_para_validacao, modo_jogo=modo_atual)
                    if status == "ACERTO":
                        bonus_velocidade = 0
                        msg_bonus = ""
                        
                        if modo_atual == "Corrida Relogio":
                            tempo_resposta = time.time() - st.session_state.start_time
                            if tempo_resposta <= 10:
                                bonus_velocidade = 50
                                msg_bonus = " ⚡ Speed Bonus (+50)!"
                            elif tempo_resposta <= 20:
                                bonus_velocidade = 20
                                msg_bonus = " 🏃 Fast Bonus (+20)!"
                            elif tempo_resposta <= 30:
                                bonus_velocidade = 10
                                msg_bonus = " ⏱️ Quick Bonus (+10)!"
                                
                        pontos_totais = pontos + bonus_velocidade
                        
                        st.success(f"{msg} (+{pontos_totais} pts){msg_bonus}")
                        
                        # Atualiza histórico de categorias
                        cat = row['categoria']
                        st.session_state.categorias_usadas[cat] = st.session_state.categorias_usadas.get(cat, 0) + 1
                        
                        st.session_state.pontuacao += pontos_totais
                        st.session_state.posicoes_preenchidas[escolha] = {
                            "nome": row['nome'],
                            "categoria": row['categoria']
                        }
                        
                        prox_posicoes = [p['id'] for p in tatica_base if p['id'] not in st.session_state.posicoes_preenchidas]
                        if prox_posicoes:
                            prox_pos = random.choice(prox_posicoes)
                            st.session_state.posicao_selecionada = prox_pos
                            st.session_state.letra_atual = motor.sortear_letra_valida(get_pos_str(prox_pos))
                            if modo_atual == "Corrida Relogio":
                                st.session_state.start_time = time.time() # Reseta timer dos 60s
                        else:
                            st.session_state.posicao_selecionada = None
                            st.session_state.end_time = time.time() # Para o cronômetro
                        
                        st.rerun()
                    elif status == "ERRO_POSICAO":
                        st.error(msg)
                    else:
                        st.warning(msg)
                else:
                    st.warning("Digite um nome!")
                    
        else:
            if st.session_state.get("game_over_derrota"):
                import random
                msgs_derrota = [
                    "Fica pra próxima campeão!! 🏆 (Só que não)",
                    "Não foi dessa vez! O professor não gostou da sua escalação. 📉",
                    "Tenta de novo, porque dessa vez não rolou... 🤦‍♂️",
                    "Foi de 12:59... o famoso 'vai dar uma hora!' Mas não deu. 🕰️",
                    "Foi de arrasta pra cima... Vai arregar ou tentar de novo? ☠️",
                    "Levou cartão vermelho! Fim de papo pro terror do apito! 🟥",
                    "Seu time foi desclassificado por W.O. mental! 🧠📉"
                ]
                st.error(f"🟥 {random.choice(msgs_derrota)}")
            else:
                st.success("🎉 FINAL DE JOGO! TÁTICA COMPLETADA COM SUCESSO! 🏆")
                
            tempo_final_segundos = st.session_state.end_time - (st.session_state.get("tempo_global") if modo_atual == "Corrida Relogio" else st.session_state.start_time)
            mins, secs = divmod(int(tempo_final_segundos), 60)
            tempo_final_str = f"{mins:02d}:{secs:02d}"
            
            st.markdown(f"**Tempo Total da Partida:** {tempo_final_str}")
            
            # --- RESUMO DA ESCALAÇÃO ---
            preenchidos = len(st.session_state.posicoes_preenchidas)
            st.markdown(f"**📋 Escalação Final ({preenchidos}/11) | Score: {st.session_state.pontuacao} pts**")
            
            cols_squad = st.columns(2)
            for i, pos in enumerate(tatica_base):
                pid = pos['id']
                label = pos['posicao']
                col_idx = i % 2
                if pid in st.session_state.posicoes_preenchidas:
                    jog = st.session_state.posicoes_preenchidas[pid]
                    cols_squad[col_idx].markdown(f"**{label}**: {jog['nome']}")
                else:
                    cols_squad[col_idx].markdown(f"**{label}**: ❌")
            
            st.markdown("---")
            ponto_final = st.session_state.pontuacao
            
            # --- LÓGICA DE PÓDIO MULTIPLAYER ---
            if st.session_state.get("is_multiplayer"):
                room = st.session_state.get("room_id")
                nome = st.session_state.get("player_name")
                
                # Atualizar JSON como terminado
                try:
                    with open(f"data/rooms/{room}_player_{nome}.json", "w") as f:
                        json.dump({
                            "nome": nome,
                            "pontuacao": st.session_state.pontuacao,
                            "posicoes_faltando": 0,
                            "terminou": True,
                            "tempo_final": st.session_state.end_time
                        }, f)
                except: pass
                
                player_files = glob.glob(f"data/rooms/{room}_player_*.json")
                terminados = []
                for pf in player_files:
                    try:
                        with open(pf, "r") as f:
                            data = json.load(f)
                            if data.get("terminou"):
                                terminados.append(data)
                    except: pass
                
                # Ordenar por tempo real
                terminados.sort(key=lambda x: x.get("tempo_final", 9999999999))
                
                meu_rank = -1
                for i, r in enumerate(terminados):
                    if r["nome"] == nome:
                        meu_rank = i
                        break
                
                modo_atual = st.session_state.get("modo_multi", "BR")
                
                if modo_atual == "X1":
                    if meu_rank == 0:
                        bonus_podio = 50
                        rank_str = "🥇 1º Lugar (+50 pts)"
                    else:
                        rank_str = f"🏅 {meu_rank+1}º Lugar (Sem Bônus no X1)"
                        bonus_podio = 0
                else: # BR
                    if meu_rank == 0:
                        bonus_podio = 50
                        rank_str = "🥇 1º Lugar (+50 pts)"
                    elif meu_rank == 1:
                        bonus_podio = 30
                        rank_str = "🥈 2º Lugar (+30 pts)"
                    elif meu_rank == 2:
                        bonus_podio = 15
                        rank_str = "🥉 3º Lugar (+15 pts)"
                    else:
                        rank_str = f"🏅 {meu_rank+1}º Lugar (Sem Bônus)"
                        bonus_podio = 0
                
                st.markdown(f"### Ranking Final: {rank_str}")
                ponto_final += bonus_podio
                st.metric("Pontuação Final (c/ Bônus)", ponto_final)

            else:
                st.metric("Pontuação Final", ponto_final)
                
            # Auto-salvar no leaderboard se Single Player
            if not st.session_state.get("is_multiplayer"):
                if st.session_state.get("game_over_derrota"):
                    st.warning("Estatísticas não salvas no placar por Desclassificação (Limites de Cartão Vermelho atingidos).")
                else:
                    if not st.session_state.get("recorde_salvo"):
                        nome_jogador = st.session_state.get("player_name", "Desconhecido")
                        # Adiciona a variavel do modo para filtrar no ranking
                        salvar_no_leaderboard(
                            nome_jogador,
                            tempo_final_str,
                            tempo_final_segundos,
                            ponto_final,
                            st.session_state.tatica_nome,
                            modo=st.session_state.get("modo_atual_single", "Time Attack")
                        )
                        st.session_state.recorde_salvo = True
                    st.success(f"🏅 Estatísticas salvas no placar para {st.session_state.get('player_name', '')}!")
            
            if st.button("Voltar ao Menu Principal"):
                if st.session_state.get("is_multiplayer"):
                    st.query_params.clear()
                    limpar_sessao()
                else:
                    limpar_sessao()
                st.rerun()

    with col2:
        st.subheader(f"Tática em Campo ({st.session_state.tatica_nome})")
        figura_campo = desenhar_campo(taticas[st.session_state.tatica_nome])
        # Use_container_width makes it responsive to the column size, ideal for mobile
        st.plotly_chart(figura_campo, use_container_width=True, config={'displayModeBar': False})

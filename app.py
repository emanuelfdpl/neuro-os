import streamlit as st
import sqlite3
import pandas as pd
import time
import random
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA E ESTILO ---
st.set_page_config(
    page_title="Neuro-OS | Protocolo 1M",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS para dar um visual "High Tech" e reduzir ruído visual
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #00ff00 , #00cc00);
    }
    .big-font {
        font-size:30px !important;
        font-weight: bold;
    }
    .mana-bar {
        color: #00b4d8;
    }
    .xp-bar {
        color: #ffaa00;
    }
    div[data-testid="stMetricValue"] {
        font-size: 24px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. GERENCIAMENTO DE ESTADO E BANCO DE DADOS ---

def init_db():
    """Inicializa o banco de dados SQLite localmente."""
    # Garante que a pasta de dados existe (Crucial para persistência no Docker/Coolify)
    if not os.path.exists('data'):
        os.makedirs('data')
        
    conn = sqlite3.connect('data/neuro_os_data.db', check_same_thread=False)
    c = conn.cursor()
    
    # Tabela de Tarefas
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY, task TEXT, difficulty TEXT, status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Tabela do Jogador (Perfil)
    c.execute('''CREATE TABLE IF NOT EXISTS player
                 (id INTEGER PRIMARY KEY, xp INTEGER, level INTEGER, mana INTEGER, streak INTEGER)''')
    
    # Criar jogador inicial se não existir
    c.execute("SELECT count(*) FROM player")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO player (xp, level, mana, streak) VALUES (0, 1, 100, 0)")
        conn.commit()
    
    return conn

conn = init_db()

# --- 3. FUNÇÕES DO SISTEMA (LÓGICA DO JOGO) ---

def get_player():
    df = pd.read_sql("SELECT * FROM player", conn)
    return df.iloc[0]

def update_player(xp_add=0, mana_add=0):
    current = get_player()
    new_xp = current['xp'] + xp_add
    new_mana = max(0, min(100, current['mana'] + mana_add)) # Clamp entre 0 e 100
    
    # Lógica de Level Up (Simples: Nível = 1 + XP/1000)
    new_level = 1 + (new_xp // 1000)
    
    cursor = conn.cursor()
    cursor.execute("UPDATE player SET xp = ?, level = ?, mana = ? WHERE id = 1", 
                   (new_xp, new_level, new_mana))
    conn.commit()
    
    if new_level > current['level']:
        st.balloons()
        st.toast(f"🏆 LEVEL UP! Agora você é Nível {new_level}!", icon="🔥")

def add_quest(task_name, difficulty):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (task, difficulty, status) VALUES (?, ?, 'pending')", 
                   (task_name, difficulty))
    conn.commit()

def complete_quest(task_id, difficulty):
    # Tabela de recompensas
    rewards = {
        'Fácil': {'xp': 50, 'mana': -5},
        'Médio': {'xp': 100, 'mana': -15},
        'Difícil': {'xp': 300, 'mana': -30},
        'Boss': {'xp': 1000, 'mana': -60}
    }
    
    rew = rewards[difficulty]
    
    # Verifica se tem mana suficiente
    player = get_player()
    if player['mana'] + rew['mana'] < 0:
        st.error("⚠️ MANA INSUFICIENTE! Você precisa descansar antes de enfrentar essa tarefa.")
        return

    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status = 'completed' WHERE id = ?", (task_id,))
    conn.commit()
    
    update_player(xp_add=rew['xp'], mana_add=rew['mana'])
    st.toast(f"Quest Completada! +{rew['xp']} XP | {rew['mana']} Mana", icon="✅")
    time.sleep(0.5)
    st.rerun()

def recover_mana():
    """Simula uma atividade de regulação sensorial"""
    with st.spinner("Regulando sistema sensorial..."):
        time.sleep(1.5) # Pausa dramática para respirar
    update_player(mana_add=20)
    st.toast("Mana recuperada! +20 Energia", icon="🔋")
    st.rerun()

# --- 4. INTERFACE DO USUÁRIO (FRONTEND) ---

# Sidebar: HUD (Heads-Up Display)
player = get_player()

with st.sidebar:
    st.title(f"🧠 Piloto: Nível {player['level']}")
    
    # Barra de XP
    xp_curr = player['xp'] % 1000
    st.write(f"**XP:** {player['xp']} / Próximo Nível: {1000 - xp_curr}")
    st.progress(xp_curr / 1000, text="Progresso do Nível")
    
    st.divider()
    
    # Barra de Mana (Energia Executiva)
    st.write(f"**⚡ Mana (Energia Executiva): {player['mana']}%**")
    st.progress(player['mana'] / 100, text="Bateria Social/Mental")
    
    if player['mana'] < 30:
        st.warning("⚠️ ALERTA: Nível de sobrecarga próximo. Priorize tarefas de baixo custo ou descanse.")
    
    st.divider()
    
    st.markdown("### 🔋 Recarga")
    st.write("Use isso se estiver sentindo sobrecarga sensorial.")
    if st.button("🧘 Meditar / Stim / Pausa (Recuperar Mana)"):
        recover_mana()

# Área Principal
col_title, col_shadow = st.columns([3, 1])
with col_title:
    st.title("Neuro-OS: Protocolo 1 Milhão")
    st.caption("Sistema de Suporte Externo para Funções Executivas")

with col_shadow:
    # O "Shadow Boss" (Placeholder visual)
    st.info("🤖 **Shadow Boss diz:**\n'Mantenha o foco. O objetivo é a liberdade.'")

# Navegação por Tabs
tab_quests, tab_roulette, tab_add = st.tabs(["📜 Quadro de Quests", "🎲 Roleta de Dopamina", "📥 Nova Quest"])

# --- TAB 1: QUADRO DE QUESTS ---
with tab_quests:
    # Filtros e Visualização
    df_tasks = pd.read_sql("SELECT * FROM tasks WHERE status = 'pending' ORDER BY id DESC", conn)
    
    if df_tasks.empty:
        st.success("🎉 Nenhuma pendência! Seu sistema está limpo. Crie novas metas ou descanse.")
    else:
        for index, row in df_tasks.iterrows():
            # Card da Tarefa
            with st.container():
                c1, c2, c3, c4 = st.columns([0.6, 0.15, 0.1, 0.15])
                
                # Definir cor baseada na dificuldade
                color_map = {'Fácil': '🟢', 'Médio': '🟡', 'Difícil': '🔴', 'Boss': '🟣'}
                icon = color_map.get(row['difficulty'], '⚪')
                
                with c1:
                    st.markdown(f"### {icon} {row['task']}")
                with c2:
                    st.caption(f"Rank: {row['difficulty']}")
                with c4:
                    if st.button("⚔️ Concluir", key=f"btn_c_{row['id']}", use_container_width=True):
                        complete_quest(row['id'], row['difficulty'])
                st.divider()

# --- TAB 2: ROLETA DE DOPAMINA (Antídoto para Paralisia) ---
with tab_roulette:
    st.header("🎲 O Oráculo do Caos")
    st.markdown("""
    **Instruções:**
    Use isso quando estiver travado, sem saber por onde começar. 
    O sistema escolherá **UMA** tarefa para você. Seu único trabalho é obedecer o algoritmo por 20 minutos.
    """)
    
    if st.button("🔮 SORTEAR MISSÃO AGORA", type="primary", use_container_width=True):
        pending = pd.read_sql("SELECT * FROM tasks WHERE status = 'pending'", conn)
        
        if not pending.empty:
            # Animação de suspense
            with st.spinner("O algoritmo está analisando as probabilidades..."):
                time.sleep(2)
            
            chosen = pending.sample().iloc[0]
            
            st.markdown("---")
            st.success("🎯 **MISSÃO SELECIONADA:**")
            st.markdown(f"# {chosen['task']}")
            st.markdown(f"**Dificuldade:** {chosen['difficulty']}")
            st.markdown("---")
            st.info("💡 **Regra:** Não pense. Apenas execute esta tarefa agora.")
        else:
            st.warning("Você precisa adicionar missões ao backlog primeiro!")

# --- TAB 3: NOVA QUEST (Entrada de Dados) ---
with tab_add:
    st.header("📥 Download Mental")
    st.write("Tire da cabeça e coloque no sistema. Não confie na sua memória de curto prazo.")
    
    with st.form("add_quest_form"):
        new_task_text = st.text_input("Descrição da Tarefa", placeholder="Ex: Configurar o Docker na VPS...")
        
        col_dif, col_sub = st.columns([3, 1])
        with col_dif:
            difficulty = st.select_slider(
                "Nível de Energia Necessária",
                options=['Fácil', 'Médio', 'Difícil', 'Boss'],
                value='Médio'
            )
            st.caption("Fácil: -5 Mana | Médio: -15 Mana | Difícil: -30 Mana | Boss: -60 Mana")
            
        with col_sub:
            submitted = st.form_submit_button("💾 Salvar no Backlog")
            
        if submitted and new_task_text:
            add_quest(new_task_text, difficulty)
            st.success("Quest registrada!")
            time.sleep(1)
            st.rerun()

# Rodapé
st.markdown("---")
st.caption("Neuro-OS v1.0 | Sistema Otimizado para Dupla Excepcionalidade (2E) | Executando em ambiente seguro.")
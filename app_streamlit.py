import streamlit as st
import pandas as pd
import os 
# Importa apenas o que é estritamente necessário para este arquivo
from otimizacao_motor import CUSTO_ROW_NAME
from modules.utils import load_css, apply_theme_selection
from modules.restricoes_ui import render_restricoes_e_metas
from modules.consulta_ui import render_modo_consulta
from modules.resultados_ui import render_resultados

# ============================================================
# 0. CONFIGURAÇÃO INICIAL E ESTADO
# ============================================================

st.set_page_config(
    page_title="Otimizador de Formulações Nutricionais",
    layout="wide",
    page_icon="⚙️"
)

# --- CARREGAMENTO DO ESTILO EXTERNO ---
# O caminho para o CSS é resolvido dentro do load_css (utils.py)
load_css() 

# --- INICIALIZAÇÃO COMPLETA DO ESTADO DA SESSÃO ---

if 'is_dark_mode' not in st.session_state:
    st.session_state.is_dark_mode = False
if 'restricoes_dinamicas' not in st.session_state:
    st.session_state.restricoes_dinamicas = [] 
if 'status_text' not in st.session_state:
    st.session_state.status_text = None
if 'custo_final' not in st.session_state:
    st.session_state.custo_final = 0.0
if 'df_resultado' not in st.session_state:
    st.session_state.df_resultado = pd.DataFrame()
if 'df_comp' not in st.session_state:
    st.session_state.df_comp = pd.DataFrame()
if 'df_gargalo' not in st.session_state:
    st.session_state.df_gargalo = pd.DataFrame()
if 'formulacao_consulta' not in st.session_state:
    st.session_state.formulacao_consulta = {}
if 'consulta_resultado_nut' not in st.session_state:
    st.session_state.consulta_resultado_nut = None
if 'consulta_resultado_custo' not in st.session_state:
    st.session_state.consulta_resultado_custo = 0.0
# --- FIM DA INICIALIZAÇÃO COMPLETA ---


# ============================================================
# CABEÇALHO E TEMA
# ============================================================

# 1. Título e Toggle na mesma linha
col_titulo, col_tema = st.columns([5, 1], gap=None)

with col_titulo:
    st.title("⚙️ Otimizador de Formulações Nutricionais")

with col_tema:
    # 3. Botão Toggle (Lua/Sol)
    # AJUSTE: Voltamos a usar um emoji como rótulo inicial (Lua)
    st.session_state.is_dark_mode = st.toggle(
        "🌙", # Usa a lua como rótulo fixo
        value=st.session_state.is_dark_mode,
        label_visibility="visible",
        key="theme_toggle"
    )

# Aplica o CSS do tema com base no estado do toggle
apply_theme_selection(st.session_state.is_dark_mode) 

st.markdown("### Ferramenta completa para otimização, consulta e análise de misturas.")
st.markdown("---") 


# ============================================================
# CARREGAMENTO DE DADOS (GLOBAL)
# ============================================================
try:
    @st.cache_data
    def load_data():
        # Assegura que o arquivo de dados está presente e correto
        if not os.path.exists('MPs_data.xlsx'):
            st.error("ERRO: O arquivo 'MPs_data.xlsx' não foi encontrado.")
            st.stop()
        
        materias_primas = pd.read_excel('MPs_data.xlsx', index_col=0)
        
        if CUSTO_ROW_NAME not in materias_primas.index:
            st.error(f"ERRO DE DADOS: A matriz deve ter uma LINHA chamada '{CUSTO_ROW_NAME}' no índice. Verifique 'MPs_data.xlsx'.")
            st.stop()
        return materias_primas

    materias_primas = load_data()
    
    LISTA_NUTRIENTES = [n for n in materias_primas.index if n != CUSTO_ROW_NAME]
    LISTA_MPS = materias_primas.columns.tolist()
    
except Exception as e:
    st.error(f"Erro ao processar dados: {e}")
    st.stop()


# ============================================================
# LAYOUT PRINCIPAL E ABAS (CHAMANDO OS MÓDULOS DE UI)
# ============================================================

tab1, tab2, tab3 = st.tabs(["📊 Restrições e Metas", "🔍 Modo Consulta", "📈 Resultados"])

with tab1:
    render_restricoes_e_metas(materias_primas, LISTA_MPS, LISTA_NUTRIENTES)

with tab2:
    render_modo_consulta(materias_primas, LISTA_MPS)

with tab3:
    render_resultados(materias_primas)

# ============================================================
# RODAPÉ
# ============================================================
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:gray;font-size:12px;'>© 2025 - Otimizador de Formulações | Desenvolvido por Levi Oliveira</p>",
    unsafe_allow_html=True
)
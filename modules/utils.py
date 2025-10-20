import streamlit as st
import pandas as pd
import os 
from datetime import datetime
import uuid 
# Importa o nome da coluna de custo para a função de log
from otimizacao_motor import CUSTO_ROW_NAME 
# É necessário importar LISTA_MPS e LISTA_NUTRIENTES ou recebê-los como argumento.
# Vou optar por recebê-los como argumento nas callbacks, mas para 'registrar_log_execucao' não é preciso.

# ============================================================
# FUNÇÕES DE ESTILO E TEMA
# ============================================================

def load_css(file_name="assets/style.css"):
    """Lê um arquivo CSS e injeta seu conteúdo via st.markdown."""
    try:
        # Tenta carregar o CSS do novo caminho relativo
        path = os.path.join(os.path.dirname(__file__), '..', file_name)
        with open(path, encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Erro: O arquivo de estilo '{file_name}' não foi encontrado. Certifique-se de que está no caminho correto.")
    except UnicodeDecodeError:
        st.error(f"Erro de Codificação: Falha ao ler o arquivo '{file_name}'. Garanta que ele esteja salvo como UTF-8.")

# Em modules/utils.py

# ... (código anterior da função load_css)

def apply_theme_selection(is_dark_mode):
    """
    Aplica o tema (cores) com base no valor booleano do toggle.
    Mantém a Lua como ícone fixo e apenas ajusta o tema.
    """
    
    # Estilos CSS comuns para o toggle (formatação da Lua)
    toggle_base_style = """
        [data-testid="stToggle"] label {
            /* Garante o espaço para o emoji e alinha */
            font-size: 1.5rem !important;
            position: relative;
            top: -5px; 
            margin-left: 10px; 
            line-height: 1; 
            color: initial !important; /* Garante que a cor do emoji seja visível (não transparente) */
            text-shadow: none !important; /* Remove qualquer sombra que possa atrapalhar */
        }
    """

    if is_dark_mode:
        # Tema Escuro
        st.markdown(f"""
            <style>
                {toggle_base_style}
                
                /* Variáveis do CSS externo */
                :root {{
                    --cor-fundo-escuro: #1C1C1C;
                    --cor-sidebar-escuro: #252525;
                    --cor-metric-card-escuro: #2C2C2C;
                }}
                
                /* FUNDOS GLOBAIS (Tema Escuro) */
                .stApp {{
                    background-color: var(--cor-fundo-escuro) !important;
                    color: #E0E0E0;
                }}
                section.main .stSidebar {{
                    background-color: var(--cor-sidebar-escuro);
                }}
                .block-container {{
                    background-color: var(--cor-fundo-escuro);
                    color: #E0E0E0;
                }}
                [data-testid="stHeader"] {{
                    background-color: var(--cor-fundo-escuro) !important;
                }}
                [data-testid="stHeader"] * {{
                    color: #E0E0E0 !important; 
                }}
                h1, h2, h3 {{ 
                    color: #E0E0E0 !important;
                }}
                .metric-card {{
                    background-color: var(--cor-metric-card-escuro);
                    color: #E0E0E0;
                    box-shadow: 1px 1px 5px rgba(255,255,255,0.1);
                }}
                
                /* Garante que não haja injeção de Sol */
                [data-testid="stToggle"] label::after {{
                    content: "";
                }}
            </style>
        """, unsafe_allow_html=True)
    else:
        # Tema Claro 
        st.markdown(f"""
            <style>
                {toggle_base_style}

                /* FUNDOS GLOBAIS (Tema Claro) */
                .stApp {{
                    background-color: white !important;
                    color: black;
                }}
                .block-container {{
                    background-color: var(--cor-fundo-claro); 
                    color: black;
                }}
                h1, h2, h3 {{ 
                    color: black !important;
                }}
                [data-testid="stHeader"] {{
                    background-color: initial; 
                }}
                [data-testid="stHeader"] * {{
                    color: initial; 
                }}
                
                /* Garante que não haja injeção de Sol */
                [data-testid="stToggle"] label::after {{
                    content: ""; 
                }}
            </style>
        """, unsafe_allow_html=True)

# ============================================================
# FUNÇÕES DE CALLBACKS E LOG
# ============================================================

def adicionar_restricao_mp_callback(lista_mps):
    """Adiciona uma nova restrição de Matéria-Prima ao estado da sessão."""
    st.session_state.restricoes_dinamicas.append({
        'id_restricao': str(uuid.uuid4()), 
        'item': lista_mps[0] if lista_mps else '',
        'tipo': '<=', 
        'valor': 0.0,
        'tipo_item': 'MP' 
    })

def adicionar_restricao_nutriente_callback(lista_nutrientes):
    """Adiciona uma nova restrição de Nutriente ao estado da sessão."""
    st.session_state.restricoes_dinamicas.append({
        'id_restricao': str(uuid.uuid4()), 
        'item': lista_nutrientes[0] if lista_nutrientes else '',
        'tipo': '>=', 
        'valor': 0.0,
        'tipo_item': 'Nutriente' 
    })

def registrar_log_execucao(custo_final, status_text):
    """Cria ou anexa o resultado da execução ao log_execucao.csv"""
    
    # Cria o diretório 'resultados' se não existir
    if not os.path.exists('resultados'):
        os.makedirs('resultados')

    log_path = 'resultados/log_execucao.csv'
    
    # Prepara a nova linha de dados
    novo_log = pd.DataFrame([{
        'Data': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Custo Total': custo_final,
        'Status Otimizacao': status_text
    }])

    if not os.path.exists(log_path):
        novo_log.to_csv(log_path, mode='w', index=False, header=True)
    else:
        try:
            # Tenta ler o arquivo para verificar se está OK
            pd.read_csv(log_path) 
            # Se a leitura foi bem-sucedida, anexa
            novo_log.to_csv(log_path, mode='a', index=False, header=False)
        except Exception:
            st.warning("O arquivo de log ('resultados/log_execucao.csv') estava mal formatado e foi sobrescrito.")
            novo_log.to_csv(log_path, mode='w', index=False, header=True)
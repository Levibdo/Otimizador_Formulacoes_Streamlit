import streamlit as st
import pandas as pd
from otimizacao_motor import resolver_modelo_otimizado, CUSTO_ROW_NAME

# ============================================================
# 0. CONFIGURAÇÃO INICIAL, ESTADO E CARREGAMENTO DE DADOS
# ============================================================

st.set_page_config(page_title="Otimizador de Formulações", layout="wide")
st.title("Sistema de Otimização de Formulações")

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
if 'restricoes_dinamicas' not in st.session_state:
    st.session_state.restricoes_dinamicas = [] 
# O estado 'ultima_solucao' será mantido para guardar o resultado base, mas 'variacao_data' não é mais necessário.


# Carregamento de dados (APENAS MPs_data.xlsx)
try:
    @st.cache_data
    def load_data():
        materias_primas = pd.read_excel('MPs_data.xlsx', index_col=0)
        
        if CUSTO_ROW_NAME not in materias_primas.index:
            st.error(f"ERRO DE DADOS: A matriz deve ter uma LINHA chamada '{CUSTO_ROW_NAME}' no índice. Verifique 'MPs_data.xlsx'.")
            st.stop()
        
        return materias_primas

    materias_primas = load_data()
    
    # Listas separadas para uso na interface
    LISTA_NUTRIENTES = [n for n in materias_primas.index if n != CUSTO_ROW_NAME]
    LISTA_MPS = materias_primas.columns.tolist()
    
except FileNotFoundError:
    st.error("ERRO: Certifique-se de que 'MPs_data.xlsx' está na mesma pasta do script para carregamento inicial.")
    st.stop()
except ValueError as e:
    st.error(f"Erro ao processar dados no Excel: {e}")
    st.stop()


# ============================================================
# 1. INTERFACE DE RESTRIÇÕES (ENTRADA DO USUÁRIO)
# ============================================================

st.header("1. Definição de Metas e Restrições")

# --- CAMPO DE CUSTO MÁXIMO (Restrição global simples) ---
custo_maximo_usuario = st.number_input(
    "Custo Máximo Desejado (R$ por unidade de produto)",
    min_value=0.0,
    value=materias_primas.loc[CUSTO_ROW_NAME].max() * 1.5,
    step=0.1,
    format="%.4f",
    help="Limite superior para o custo. Se o modelo não atender as metas dentro deste limite, ele se torna INVIÁVEL."
)
st.markdown("---") 

# ============================================================
# FUNÇÕES DE CALLBACK PARA ADICIONAR RESTRIÇÕES
# ============================================================

def adicionar_restricao_mp_callback():
    st.session_state.restricoes_dinamicas.append({
        'item': LISTA_MPS[0] if LISTA_MPS else '',
        'tipo': '<=', # MPs geralmente usam Maximo
        'valor': 0.0,
        'tipo_item': 'MP' 
    })

def adicionar_restricao_nutriente_callback():
    st.session_state.restricoes_dinamicas.append({
        'item': LISTA_NUTRIENTES[0] if LISTA_NUTRIENTES else '',
        'tipo': '>=', # Nutrientes geralmente usam Mínimo
        'valor': 0.0,
        'tipo_item': 'Nutriente' 
    })

# ============================================================
# DESENHO DINÂMICO DE RESTRIÇÕES (SEÇÕES)
# ============================================================

st.subheader("🛠️ Gerenciamento de Restrições")

# --- SEÇÃO 1: RESTRIÇÕES DE MATÉRIAS-PRIMAS ---
with st.expander("Restrições de Inclusão de Matérias-Primas (Min/Max/Fixo)"):
    
    # Botão de adição específico
    st.button(
        "➕ Adicionar Restrição de Matéria-Prima", 
        on_click=adicionar_restricao_mp_callback, 
        type="secondary",
        key="add_mp"
    )
    st.markdown("")
    
    restricoes_para_remover = []
    
    # Filtra e itera APENAS sobre as MPs
    for i, rest in enumerate([r for r in st.session_state.restricoes_dinamicas if r['tipo_item'] == 'MP']):
        
        # O índice real na lista mestre é necessário para o 'pop'
        index_real = st.session_state.restricoes_dinamicas.index(rest) 
        
        col1, col2, col3, col4, col5 = st.columns([0.4, 0.15, 0.15, 0.2, 0.1])
        
        with col1:
            rest['item'] = st.selectbox(
                "MP", 
                LISTA_MPS, 
                index=LISTA_MPS.index(rest['item']) if rest['item'] in LISTA_MPS else 0,
                key=f"mp_item_{index_real}", 
                label_visibility="collapsed"
            )
        with col2:
            rest['tipo'] = st.selectbox(
                "Tipo MP", 
                ['<=', '>=', '='], 
                index=['<=', '>=', '='].index(rest['tipo']), 
                key=f"mp_tipo_{index_real}",
                label_visibility="collapsed"
            )
        with col3:
            rest['valor'] = st.number_input(
                "Valor MP (0 a 1)", 
                value=rest['valor'], 
                min_value=0.0,
                max_value=1.0,
                step=0.001,
                format="%.4f",
                key=f"mp_valor_{index_real}",
                label_visibility="collapsed"
            )
        with col5:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("X", key=f"mp_remover_{index_real}"):
                restricoes_para_remover.append(index_real)


# --- SEÇÃO 2: RESTRIÇÕES DE NUTRIENTES ---
with st.expander("Metas Nutricionais (Min/Max/Fixo)"):
    
    # Botão de adição específico
    st.button(
        "➕ Adicionar Meta Nutricional", 
        on_click=adicionar_restricao_nutriente_callback, # <--- CORREÇÃO: on_click
        type="secondary",
        key="add_nutriente"
    )
    st.markdown("")
    
    # Filtra e itera APENAS sobre os Nutrientes
    for i, rest in enumerate([r for r in st.session_state.restricoes_dinamicas if r['tipo_item'] == 'Nutriente']):
        
        # O índice real na lista mestre é necessário para o 'pop'
        index_real = st.session_state.restricoes_dinamicas.index(rest)
        
        col1, col2, col3, col4, col5 = st.columns([0.4, 0.15, 0.15, 0.2, 0.1])
        
        with col1:
            rest['item'] = st.selectbox(
                "Nutriente", 
                LISTA_NUTRIENTES, 
                index=LISTA_NUTRIENTES.index(rest['item']) if rest['item'] in LISTA_NUTRIENTES else 0,
                key=f"nut_item_{index_real}", 
                label_visibility="collapsed"
            )
        with col2:
            rest['tipo'] = st.selectbox(
                "Tipo Nut.", 
                ['<=', '>=', '='], 
                index=['<=', '>=', '='].index(rest['tipo']), 
                key=f"nut_tipo_{index_real}",
                label_visibility="collapsed"
            )
        with col3:
            rest['valor'] = st.number_input(
                "Valor Nut.", 
                value=rest['valor'], 
                step=0.001,
                format="%.4f",
                key=f"nut_valor_{index_real}",
                label_visibility="collapsed"
            )
        with col5:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("X", key=f"nut_remover_{index_real}"):
                restricoes_para_remover.append(index_real)


# Lógica de remoção única (fora dos loops)
if restricoes_para_remover:
    for index in reversed(restricoes_para_remover):
        st.session_state.restricoes_dinamicas.pop(index)
    st.rerun() 
    
if not st.session_state.restricoes_dinamicas:
     st.info("Nenhuma restrição ativa. Adicione metas nutricionais e/ou restrições de inclusão de MPs.")

st.markdown("---")
# ============================================================
# 2. BOTÃO DE EXECUÇÃO E PROCESSAMENTO
# ============================================================

if st.button("🚀 Otimizar Formulação e Calcular Custo", type="primary"):
    
    with st.spinner("Executando o solver de otimização (Programação Linear)..."):
        
        # 2.1. Chamada ao Motor de Otimização
        status_text, custo_final, df_resultado, df_comp, df_gargalo = \
            resolver_modelo_otimizado(
                materias_primas, 
                st.session_state.restricoes_dinamicas, 
                custo_maximo_usuario
            )


# ============================================================
# 3. EXIBIÇÃO DE RESULTADOS E SUGESTÃO MANUAL
# ============================================================
        
        st.header("2. Resultados da Otimização")

        if status_text in ['Optimal', 'Feasible']:
            st.success(f"Status da Solução: **{status_text}** (Otimização Completa)")
            st.metric(label="Custo Total da Formulação (Real)", value=f"R$ {custo_final:.4f}") 

            # =======================================================
            # 3.1. Formulação Ideal (Pesos e Custo por MP) - MODIFICADO
            # =======================================================
            st.subheader("Fórmula Ideal (Pesos e Contribuição de Custo)")
            
            df_resultado_final = df_resultado.copy()
            
            # 1. Obter o Custo Unitário de cada MP
            custos_unitarios = materias_primas.loc[CUSTO_ROW_NAME, :].to_dict()

            # 2. Calcular o Custo de Inclusão por MP
            
            # Mapeia o Custo Unitário para o DataFrame de resultados
            df_resultado_final['Custo Unitário (R$)'] = df_resultado_final['Matéria-Prima'].map(custos_unitarios)
            
            # Calcula o custo da MP na formulação: (Peso / 100) * Custo Unitário
            # Usando 'Peso (%)' que é o nome correto da coluna
            df_resultado_final['Custo na Fórmula (R$)'] = (
                df_resultado_final['Peso (%)'] / 100
            ) * df_resultado_final['Custo Unitário (R$)']
            
            # Formatando para exibição
            df_resultado_final['Custo Unitário (R$)'] = df_resultado_final['Custo Unitário (R$)'].apply(lambda x: f"R$ {x:.4f}")
            df_resultado_final['Custo na Fórmula (R$)'] = df_resultado_final['Custo na Fórmula (R$)'].apply(lambda x: f"R$ {x:.4f}")
            
            # Reorganizar as colunas para melhor visualização
            df_resultado_final = df_resultado_final[[
                'Matéria-Prima', 'Peso (%)', 'Custo Unitário (R$)', 'Custo na Fórmula (R$)'
            ]]
            
            st.dataframe(df_resultado_final, hide_index=True, use_container_width=True) 
            
            # 3.2. Conferência Nutricional
            st.subheader("Conferência Nutricional (Metas Atendidas)")
            st.dataframe(df_comp, hide_index=True, use_container_width=True) 

            # 3.3. Análise de Gargalos (Preço Sombra)
            if df_gargalo is not None:
                st.subheader("Análise de Restrições Ativas (Gargalos)")
                st.warning("O Preço Sombra indica o impacto no CUSTO ao relaxar/apertar a restrição.")
                st.dataframe(df_gargalo, hide_index=True, use_container_width=True) 
            else:
                st.info("Nenhuma restrição atuando como gargalo.")

            
            # --------------------------------------------------------
            # IDENTIFICAÇÃO DE MATÉRIAS-PRIMAS CHAVES PARA VARIAÇÃO MANUAL
            # --------------------------------------------------------
            
            st.markdown("---")
            st.subheader("Sugestão para Variações: MPs Ativas")

            # Definimos o nome correto da coluna com base no otimizador.
            COLUNA_PERCENTUAL_REAL = 'Peso (%)'
            
            # Filtra apenas as MPs que têm participação > 0%
            df_resultado_filtrado = df_resultado.copy()
            
            # Filtra usando o nome correto da coluna: 'Peso (%)'
            mps_incluidas = df_resultado_filtrado[df_resultado_filtrado[COLUNA_PERCENTUAL_REAL] > 0.0001]['Matéria-Prima'].tolist()
            
            
            if not mps_incluidas:
                st.info("A otimização resultou em uma solução sem inclusão ativa de MPs. Revise as restrições mínimas.")
            else:
                st.warning(
                    "Para gerar uma **formulação alternativa** (variação), utilize a seção "
                    "**'Restrições de Inclusão de Matérias-Primas'** (Seção 1) para adicionar uma restrição "
                    "que force a redução ou exclusão de uma das MPs chaves listadas abaixo. Depois, clique em **'Otimizar Formulação'** novamente."
                )
                
                # Exibe a lista das MPs ativas como sugestão (sem o botão)
                st.markdown("##### MPs Ativas na Solução (Sugeridas para Alteração):")
                
                # Cria um DataFrame simples para exibir a lista e o percentual
                df_chaves = df_resultado_filtrado[df_resultado_filtrado['Matéria-Prima'].isin(mps_incluidas)].copy()
                
                # Renomeia a coluna para o nome amigável 'Inclusão (%)' apenas para esta exibição
                df_chaves = df_chaves.rename(columns={COLUNA_PERCENTUAL_REAL: 'Inclusão (%)'})

                st.dataframe(df_chaves[['Matéria-Prima', 'Inclusão (%)']], hide_index=True, use_container_width=True)


        else:
            st.error(f"FALHA na Otimização! Status: **{status_text}**")
            st.warning("O modelo é inviável. Revise suas restrições.")
import streamlit as st
import pandas as pd
import json 
import io 
import uuid 
import plotly.express as px
from otimizacao_motor import resolver_modelo_otimizado, CUSTO_ROW_NAME
import os 
from datetime import datetime

# ============================================================
# 0. CONFIGURAÇÃO INICIAL, ESTADO E CARREGAMENTO DE DADOS
# ============================================================

st.set_page_config(page_title="Otimizador de Formulações", layout="wide")
st.title("Sistema de Otimização de Formulações")

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
if 'restricoes_dinamicas' not in st.session_state:
    st.session_state.restricoes_dinamicas = [] 

# --- INICIALIZAÇÃO DO ESTADO DE RESULTADOS ---
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


# --- CARREGAMENTO DE DADOS ---
try:
    @st.cache_data
    def load_data():
        # Verifique se 'MPs_data.xlsx' existe e carregue.
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
# FUNÇÕES DE CALLBACKS E LOG
# ============================================================

def adicionar_restricao_mp_callback():
    st.session_state.restricoes_dinamicas.append({
        'id_restricao': str(uuid.uuid4()), 
        'item': LISTA_MPS[0] if LISTA_MPS else '',
        'tipo': '<=', 
        'valor': 0.0,
        'tipo_item': 'MP' 
    })

def adicionar_restricao_nutriente_callback():
    st.session_state.restricoes_dinamicas.append({
        'id_restricao': str(uuid.uuid4()), 
        'item': LISTA_NUTRIENTES[0] if LISTA_NUTRIENTES else '',
        'tipo': '>=', 
        'valor': 0.0,
        'tipo_item': 'Nutriente' 
    })

def registrar_log_execucao(custo_final, status_text):
    """Cria ou anexa o resultado da execução ao log_execucao.csv"""
    
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
            # Tenta ler e anexar 
            pd.read_csv(log_path) 
            novo_log.to_csv(log_path, mode='a', index=False, header=False)
        except Exception:
            # Se a leitura falhar, recria o arquivo com a nova linha
            st.warning("O arquivo de log ('resultados/log_execucao.csv') estava mal formatado e foi sobrescrito.")
            novo_log.to_csv(log_path, mode='w', index=False, header=True)


# ============================================================
# 1. ENTRADA GLOBAL DE CUSTO MÁXIMO
# ============================================================

st.subheader("Limite Global de Custo")

custo_maximo_usuario = st.number_input(
    "Custo Máximo Desejado (R$ por unidade de produto)",
    min_value=0.0,
    value=materias_primas.loc[CUSTO_ROW_NAME].max() * 1.5 if materias_primas.loc[CUSTO_ROW_NAME].max() * 1.5 > 0 else 1.0, 
    step=0.1,
    format="%.4f",
    key="custo_max_input", 
    help="Limite superior para o custo. Se o modelo não atender as metas dentro deste limite, ele se torna INVIÁVEL."
)

st.markdown("---") 

# ============================================================
# 2. BOTÃO DE EXECUÇÃO E PROCESSAMENTO
# ============================================================

if st.button("🚀 Otimizar Formulação e Calcular Custo", type="primary"):
    
    with st.spinner("Executando o solver de otimização (Programação Linear)..."):
        
        resultados = resolver_modelo_otimizado(
            materias_primas, 
            st.session_state.restricoes_dinamicas, 
            custo_maximo_usuario 
        )

        # Salva o resultado no estado de sessão
        st.session_state.status_text, \
        st.session_state.custo_final, \
        st.session_state.df_resultado, \
        st.session_state.df_comp, \
        st.session_state.df_gargalo = resultados
        
        # Chamada da função de log
        if st.session_state.status_text in ['Optimal', 'Feasible']:
            registrar_log_execucao(
                st.session_state.custo_final,
                st.session_state.status_text
            )
        
    st.rerun() 


# ============================================================
# 3. ESTRUTURA DE ABAS (AGORA APENAS DUAS)
# ============================================================

tab2, tab3 = st.tabs(["📊 Restrições e Metas", "📈 Resultados"])

# ---------------------------------------------------------------------------------
# TABELA 2: RESTRIÇÕES E METAS 
# ---------------------------------------------------------------------------------
with tab2:
    # Cabeçalho ajustado para ser o primeiro tópico
    st.header("1. Definição de Metas e Restrições")
    
    st.subheader("🛠️ Gerenciamento de Restrições")

    # --- SEÇÃO 1: RESTRIÇÕES DE MATÉRIAS-PRIMAS ---
    with st.expander("Restrições de Inclusão de Matérias-Primas (Min/Max/Fixo)"):
        
        st.button(
            "➕ Adicionar Restrição de Matéria-Prima", 
            on_click=adicionar_restricao_mp_callback, 
            type="secondary",
            key="add_mp"
        )
        st.markdown("")
        
        restricoes_para_remover = []
        
        for i, rest in enumerate([r for r in st.session_state.restricoes_dinamicas if r['tipo_item'] == 'MP']):
            
            index_real = st.session_state.restricoes_dinamicas.index(rest) 
            rest_id = rest.get('id_restricao', str(index_real)) 

            col1, col2, col3, col4, col5 = st.columns([0.4, 0.15, 0.15, 0.2, 0.1])
            
            with col1:
                rest['item'] = st.selectbox(
                    "MP", 
                    LISTA_MPS, 
                    index=LISTA_MPS.index(rest['item']) if rest['item'] in LISTA_MPS else 0,
                    key=f"mp_item_{rest_id}", 
                    label_visibility="collapsed"
                )
            with col2:
                rest['tipo'] = st.selectbox(
                    "Tipo MP", 
                    ['<=', '>=', '='], 
                    index=['<=', '>=', '='].index(rest['tipo']), 
                    key=f"mp_tipo_{rest_id}", 
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
                    key=f"mp_valor_{rest_id}", 
                    label_visibility="collapsed"
                )
            with col5:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("X", key=f"mp_remover_{rest_id}"): 
                    restricoes_para_remover.append(index_real)


    # --- SEÇÃO 2: RESTRIÇÕES DE NUTRIENTES ---
    with st.expander("Metas Nutricionais (Min/Max/Fixo)"):
        
        st.button(
            "➕ Adicionar Meta Nutricional", 
            on_click=adicionar_restricao_nutriente_callback, 
            type="secondary",
            key="add_nutriente"
        )
        st.markdown("")
        
        for i, rest in enumerate([r for r in st.session_state.restricoes_dinamicas if r['tipo_item'] == 'Nutriente']):
            
            index_real = st.session_state.restricoes_dinamicas.index(rest)
            rest_id = rest.get('id_restricao', str(index_real)) 

            col1, col2, col3, col4, col5 = st.columns([0.4, 0.15, 0.15, 0.2, 0.1])
            
            with col1:
                rest['item'] = st.selectbox(
                    "Nutriente", 
                    LISTA_NUTRIENTES, 
                    index=LISTA_NUTRIENTES.index(rest['item']) if rest['item'] in LISTA_NUTRIENTES else 0,
                    key=f"nut_item_{rest_id}", 
                    label_visibility="collapsed"
                )
            with col2:
                rest['tipo'] = st.selectbox(
                    "Tipo Nut.", 
                    ['<=', '>=', '='], 
                    index=['<=', '>=', '='].index(rest['tipo']), 
                    key=f"nut_tipo_{rest_id}", 
                    label_visibility="collapsed"
                )
            with col3:
                rest['valor'] = st.number_input(
                    "Valor Nut.", 
                    value=rest['valor'], 
                    step=0.001,
                    format="%.4f",
                    key=f"nut_valor_{rest_id}", 
                    label_visibility="collapsed"
                )
            with col5:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("X", key=f"nut_remover_{rest_id}"): 
                    restricoes_para_remover.append(index_real)


    # Lógica de remoção única (fora dos loops)
    if restricoes_para_remover:
        for index in reversed(restricoes_para_remover):
            st.session_state.restricoes_dinamicas.pop(index)
        st.rerun() 
        
    if not st.session_state.restricoes_dinamicas:
        st.info("Nenhuma restrição ativa. Adicione metas nutricionais e/ou restrições de inclusão de MPs.")

    st.markdown("---")


# ---------------------------------------------------------------------------------
# TABELA 3: RESULTADOS E GRÁFICOS
# ---------------------------------------------------------------------------------
with tab3:
    # Cabeçalho ajustado para ser o segundo tópico
    st.header("2. Resultados da Otimização")

    # Verifica se a otimização foi executada
    if st.session_state.status_text is not None:
        
        # Mapeamento do estado de sessão para variáveis locais
        status_text = st.session_state.status_text
        custo_final = st.session_state.custo_final
        df_resultado = st.session_state.df_resultado
        df_comp = st.session_state.df_comp
        df_gargalo = st.session_state.df_gargalo
        COLUNA_PERCENTUAL_REAL = 'Peso (%)' 

        if status_text in ['Optimal', 'Feasible']:
            st.success(f"Status da Solução: **{status_text}** (Otimização Completa)")
            st.metric(label="Custo Total da Formulação (Real)", value=f"R$ {custo_final:.4f}") 

            # =======================================================
            # 3.1. Formulação Ideal (Pesos e Custo por MP)
            # =======================================================
            st.subheader("Tabelas de Resultados")
            
            df_resultado_final = df_resultado.copy()
            
            # 1. Obter o Custo Unitário de cada MP
            custos_unitarios = materias_primas.loc[CUSTO_ROW_NAME, :].to_dict()

            # 2. Calcular o Custo de Inclusão por MP
            df_resultado_final['Custo Unitário (R$)'] = df_resultado_final['Matéria-Prima'].map(custos_unitarios)
            
            df_resultado_final['Custo na Fórmula (R$)'] = (
                df_resultado_final[COLUNA_PERCENTUAL_REAL] / 100
            ) * df_resultado_final['Custo Unitário (R$)']
            
            # Formatando para exibição
            df_resultado_final['Custo Unitário (R$)'] = df_resultado_final['Custo Unitário (R$)'].apply(lambda x: f"R$ {x:.4f}")
            df_resultado_final['Custo na Fórmula (R$)'] = df_resultado_final['Custo na Fórmula (R$)'].apply(lambda x: f"R$ {x:.4f}")
            
            # Reorganizar as colunas para melhor visualização
            df_resultado_final = df_resultado_final[[
                'Matéria-Prima', 'Peso (%)', 'Custo Unitário (R$)', 'Custo na Fórmula (R$)'
            ]]
            
            st.markdown("##### 2.1. Fórmula Ideal (Pesos e Custo por MP)")
            st.dataframe(df_resultado_final, hide_index=True, use_container_width=True) 
            
            # 3.2. Conferência Nutricional
            st.markdown("##### 2.2. Conferência Nutricional (Metas Atendidas)")
            st.dataframe(df_comp, hide_index=True, use_container_width=True) 

            # 3.3. Análise de Gargalos (Preço Sombra)
            if df_gargalo is not None and not df_gargalo.empty:
                st.markdown("##### 2.3. Análise de Restrições Ativas (Gargalos)")
                st.warning("O Preço Sombra indica o impacto no CUSTO ao relaxar/apertar a restrição.")
                st.dataframe(df_gargalo, hide_index=True, use_container_width=True) 
            else:
                st.info("Nenhuma restrição atuando como gargalo.")

            st.markdown("---")

            # =======================================================
            # 3.4. GRÁFICOS (PLOTLY)
            # =======================================================

            st.subheader("Análise Gráfica")

            # Gráfico de Pizza (Matérias-Primas)
            st.markdown("##### 📊 Distribuição de Matérias-Primas na Fórmula")
            fig = px.pie(
                df_resultado,
                values='Peso (%)',
                names='Matéria-Prima',
                title='Participação das MPs na Fórmula',
                hole=.3
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Gráfico de Barras (Nutrientes)
            if 'Meta' in df_comp.columns and 'Obtido' in df_comp.columns:
                st.markdown("##### 📈 Comparativo de Nutrientes (Meta vs Obtido)")
                df_plot = df_comp.copy()
                df_plot = df_plot.melt(id_vars='Nutriente', value_vars=['Meta', 'Obtido'], var_name='Tipo', value_name='Valor')
                
                fig2 = px.bar(
                    df_plot,
                    x='Nutriente',
                    y='Valor',
                    color='Tipo',
                    barmode='group',
                    title='Desempenho Nutricional: Meta x Obtido',
                )
                st.plotly_chart(fig2, use_container_width=True)

            st.markdown("---")
            
            # =======================================================
            # 3.5. HISTÓRICO DE CUSTO
            # =======================================================
            try:
                # O log_execucao.csv precisa estar dentro de uma pasta "resultados"
                df_hist = pd.read_csv("resultados/log_execucao.csv")
                
                # Se o DataFrame não estiver vazio, exibe
                if not df_hist.empty and "Data" in df_hist.columns and "Custo Total" in df_hist.columns:
                    st.subheader("Histórico de Execuções")
                    st.line_chart(df_hist.set_index("Data")["Custo Total"])
                elif df_hist.empty:
                    st.info("Log de execução encontrado, mas vazio. Execute a otimização para registrar o histórico.")
                else:
                    raise KeyError # Força o erro para o bloco except
                    
            except FileNotFoundError:
                st.info("Arquivo de log de execução ('resultados/log_execucao.csv') não encontrado para histórico.")
            except KeyError:
                st.warning("O arquivo de log está incompleto ou mal formatado. Verifique as colunas 'Data' e 'Custo Total'.")

            st.markdown("---")

            # =======================================================
            # 3.6. EXPORTAÇÃO E SUGESTÃO (Final da aba)
            # =======================================================
            
            # EXPORTAÇÃO MULTI-ABA PARA EXCEL (.xlsx)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_resultado_final.to_excel(writer, sheet_name='Formula Ideal', index=False)
                df_comp.to_excel(writer, sheet_name='Conferencia Nutricional', index=False)
                if df_gargalo is not None and not df_gargalo.empty:
                    df_gargalo.to_excel(writer, sheet_name='Gargalos (Preco Sombra)', index=False)
                
            excel_data = output.getvalue()

            st.subheader("Exportação Completa")
            st.download_button(
                label="⬇️ Exportar Todos os Resultados (Excel .xlsx)",
                data=excel_data,
                file_name='resultados_otimizacao.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                help="Exporta a Fórmula Ideal, Conferência e Gargalos em abas separadas de um arquivo Excel."
            )
            
            st.markdown("---")

            # IDENTIFICAÇÃO DE MATÉRIAS-PRIMAS CHAVES PARA VARIAÇÃO MANUAL
            st.subheader("Sugestão para Variações: MPs Ativas")
            
            df_resultado_filtrado = df_resultado.copy()
            mps_incluidas = df_resultado_filtrado[df_resultado_filtrado[COLUNA_PERCENTUAL_REAL] > 0.0001]['Matéria-Prima'].tolist()
            
            if not mps_incluidas:
                st.info("A otimização resultou em uma solução sem inclusão ativa de MPs.")
            else:
                st.warning(
                    "Para gerar uma **formulação alternativa**, utilize a aba **'Restrições e Metas'** para adicionar uma restrição "
                    "que force a redução ou exclusão de uma das MPs chaves listadas abaixo."
                )
                
                st.markdown("##### MPs Ativas na Solução (Sugeridas para Alteração):")
                
                df_chaves = df_resultado_filtrado[df_resultado_filtrado['Matéria-Prima'].isin(mps_incluidas)].copy()
                df_chaves = df_chaves.rename(columns={COLUNA_PERCENTUAL_REAL: 'Inclusão (%)'})

                st.dataframe(df_chaves[['Matéria-Prima', 'Inclusão (%)']], hide_index=True, use_container_width=True)

        else:
            st.error(f"FALHA na Otimização! Status: **{status_text}**")
            st.warning("O modelo é inviável. Revise suas restrições na aba 'Restrições e Metas'.")

    else:
        st.info("Clique no botão '🚀 Otimizar Formulação' para executar o modelo e visualizar os resultados nesta aba.")
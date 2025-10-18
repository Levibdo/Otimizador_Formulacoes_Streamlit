import streamlit as st
import pandas as pd
from otimizacao_motor import resolver_modelo_otimizado, CUSTO_ROW_NAME

# ============================================================
# 0. CONFIGURAÇÃO INICIAL E CARREGAMENTO DE DADOS
# ============================================================

st.set_page_config(page_title="Otimizador de Formulações", layout="wide")
st.title("Sistema de Otimização de Formulações")

# Carregamento de dados (simulando a leitura centralizada do servidor)
try:
    # @st.cache_data garante que o Excel só é lido uma vez
    @st.cache_data
    def load_data():
       # Estes arquivos devem estar acessíveis no local onde o Streamlit está rodando (servidor)
        materias_primas = pd.read_excel('MPs_data.xlsx', index_col=0)
        df_metas_base = pd.read_excel('Metas_e_Restricoes.xlsx')
        
        # === LINHAS DE DEBUG: MOSTRA O QUE O PYTHON ESTÁ LENDO ===
        if CUSTO_ROW_NAME not in materias_primas.index:
            st.error(f"ERRO DE DADOS: A matriz deve ter uma LINHA chamada '{CUSTO_ROW_NAME}' no índice. Verifique 'MPs_data.xlsx'.")
            st.info(f"O Pandas leu os seguintes nomes de linhas (índices): {materias_primas.index.tolist()}")
            st.stop()
        # =========================================================
        
        return materias_primas, df_metas_base

    materias_primas, df_metas_base = load_data()
    
    # Extrai a lista de nutrientes e MPs para uso na interface
    LISTA_NUTRIENTES = [n for n in materias_primas.index if n != CUSTO_ROW_NAME]
    LISTA_MPS = materias_primas.columns.tolist()

except FileNotFoundError:
    st.error("ERRO: Certifique-se de que 'MPs_data.xlsx' e 'Metas_e_Restricoes.xlsx' estão na mesma pasta do script para carregamento inicial.")
    st.stop()
except ValueError as e:
    st.error(str(e))
    st.stop()


# ============================================================
# 1. INTERFACE DE RESTRIÇÕES (ENTRADA DO USUÁRIO)
# ============================================================

st.header("1. Definição de Metas e Restrições")

# --- NOVO CAMPO DE CUSTO MÁXIMO ---
custo_maximo_usuario = st.number_input(
    "Custo Máximo Desejado (R$ por unidade de produto)",
    min_value=0.0,
    value=10.0, 
    step=0.1,
    format="%.4f",
    help="Defina um limite superior para o custo. Se o modelo não conseguir atender as metas dentro deste limite, ele se tornará INVIÁVEL."
)
st.markdown("---") # Linha separadora

# 1.1. Metas Nutricionais (Interface para alterar as metas da planilha)
with st.expander("Metas Nutricionais (Obrigatórias)"):
    
    # Prepara o DataFrame para edição
    df_nutricionais_base = df_metas_base[df_metas_base['Tipo'] == 'Nutricional'].copy()
    df_nutricionais_base.rename(columns={'Nome': 'Nutriente'}, inplace=True)
    df_nutricionais_base = df_nutricionais_base.set_index('Nutriente')
    
    st.markdown("Altere os valores e/ou o tipo de restrição nutricional:")
    
    # st.data_editor permite edição na própria tabela
    df_nutricionais_editavel = st.data_editor(
        df_nutricionais_base[['Restrição', 'Valor']],
        column_config={
            "Restrição": st.column_config.SelectboxColumn(
                "Restrição",
                options=["<=", ">=", "="],
                required=True,
            ),
            "Valor": st.column_config.NumberColumn(
                "Valor",
                format="%.4f",
            ),
        },
        use_container_width=True
    )

# 1.2. Restrições de Inclusão de MP (Interface para alterar as MPs)
with st.expander("Restrições de Inclusão/Exclusão de Matérias-Primas"):
    
    # Prepara o DataFrame para edição
    df_inclusao_base = df_metas_base[df_metas_base['Tipo'] == 'Inclusão'].copy()
    df_inclusao_base.rename(columns={'Nome': 'Matéria-Prima'}, inplace=True)
    df_inclusao_base = df_inclusao_base.set_index('Matéria-Prima')
    
    st.markdown("Defina os limites Min, Max ou Fixo para as Matérias-Primas:")
    
    df_inclusao_editavel = st.data_editor(
        df_inclusao_base[['Restrição', 'Valor']],
        column_config={
            "Restrição": st.column_config.SelectboxColumn(
                "Restrição",
                options=["Min", "Max", "Fixo"],
                required=True,
            ),
            "Valor": st.column_config.NumberColumn(
                "Valor (0 a 1)",
                format="%.4f",
                help="Valores devem ser em fração (ex: 0.06 para 6%)"
            ),
        },
        use_container_width=True
    )

# ============================================================
# 2. BOTÃO DE EXECUÇÃO E PROCESSAMENTO
# ============================================================

if st.button("🚀 Otimizar Formulação e Calcular Custo", type="primary"):
    
    # 2.1. Montar o DataFrame de Metas final para passar ao motor
    df_nut_final = df_nutricionais_editavel.reset_index().rename(columns={'Nutriente': 'Nome'})
    df_nut_final['Tipo'] = 'Nutricional'
    
    df_inc_final = df_inclusao_editavel.reset_index().rename(columns={'Matéria-Prima': 'Nome'})
    df_inc_final['Tipo'] = 'Inclusão'
    
    # Linha corrigida e COMPLETA
    df_metas_final = pd.concat([df_nut_final, df_inc_final]) 
    
    with st.spinner("Executando o solver de otimização (Programação Linear)..."):
        
        # 2.2. Chamada ao Motor de Otimização (COM CUSTO MÁXIMO!)
        status_text, custo_final, df_resultado, df_comp, df_gargalo = \
            resolver_modelo_otimizado(materias_primas, df_metas_final, custo_maximo_usuario)


# ============================================================
# 3. EXIBIÇÃO DE RESULTADOS
# ============================================================
        
    st.header("2. Resultados da Otimização")

    if status_text in ['Optimal', 'Feasible']:
        st.success(f"Status da Solução: **{status_text}** (Otimização Completa)")
        st.metric(label="Custo Total da Formulação (Real)", value=f"R$ {custo_final:.4f}") #

        # 3.1. Formulação Ideal (Pesos)
        st.subheader("Fórmula Ideal (Pesos das Matérias-Primas)")
        st.dataframe(df_resultado, hide_index=True, use_container_width=True) #
        
        # 3.2. Conferência Nutricional
        st.subheader("Conferência Nutricional (Metas Atendidas)")
        st.dataframe(df_comp, hide_index=True, use_container_width=True) #

        # 3.3. Análise de Gargalos (Preço Sombra)
        if df_gargalo is not None:
            st.subheader("Análise de Restrições Ativas (Gargalos)")
            st.warning("O Preço Sombra indica o impacto no CUSTO ao relaxar/apertar a restrição.")
            st.dataframe(df_gargalo, hide_index=True, use_container_width=True) #
        else:
            st.info("Nenhuma restrição atuando como gargalo.")

    else:
        st.error(f"FALHA na Otimização! Status: **{status_text}**")
        st.warning("O modelo é inviável. Revise suas restrições: O custo mínimo pode ser maior do que o possível com essas metas, ou as restrições nutricionais são impossíveis de satisfazer simultaneamente.")
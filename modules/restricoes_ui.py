import streamlit as st
from modules.utils import adicionar_restricao_mp_callback, adicionar_restricao_nutriente_callback
from otimizacao_motor import resolver_modelo_otimizado, CUSTO_ROW_NAME

def render_restricoes_e_metas(materias_primas, lista_mps, lista_nutrientes):
    """
    Renderiza a Aba 1: Definição de Metas e Restrições.
    Processa a UI e, se acionado, executa o motor de otimização.
    """
    
    st.header("1. Definição de Metas e Restrições")

    # ============================================================
    # 1. ENTRADA GLOBAL DE CUSTO MÁXIMO
    # ============================================================
    st.subheader("Custo Máximo Global")
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
    # 2. GERENCIAMENTO DE RESTRIÇÕES DINÂMICAS
    # ============================================================
    st.subheader("🛠️ Gerenciamento de Restrições")

    restricoes_para_remover = []

    # --- Restrições de Matérias-Primas ---
    with st.expander("Restrições de Inclusão de Matérias-Primas (Min/Max/Fixo)"):
        
        st.button(
            "➕ Adicionar Restrição de Matéria-Prima", 
            # Passa a lista_mps para a callback, pois ela está definida no módulo utils
            on_click=adicionar_restricao_mp_callback, 
            args=(lista_mps,),
            type="secondary",
            key="add_mp"
        )
        st.markdown("")
        
        for i, rest in enumerate([r for r in st.session_state.restricoes_dinamicas if r['tipo_item'] == 'MP']):
            
            index_real = st.session_state.restricoes_dinamicas.index(rest) 
            rest_id = rest.get('id_restricao', str(index_real)) 

            col1, col2, col3, col4, col5 = st.columns([0.4, 0.15, 0.15, 0.2, 0.1])
            
            with col1:
                rest['item'] = st.selectbox(
                    "MP", 
                    lista_mps, 
                    index=lista_mps.index(rest['item']) if rest['item'] in lista_mps else 0,
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


    # --- Restrições Nutricionais ---
    with st.expander("Metas Nutricionais (Min/Max/Fixo)"):
        
        st.button(
            "➕ Adicionar Meta Nutricional", 
            # Passa a lista_nutrientes para a callback
            on_click=adicionar_restricao_nutriente_callback, 
            args=(lista_nutrientes,),
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
                    lista_nutrientes, 
                    index=lista_nutrientes.index(rest['item']) if rest['item'] in lista_nutrientes else 0,
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
    
    # ============================================================
    # 3. BOTÃO DE EXECUÇÃO
    # ============================================================
    if st.button("🚀 Otimizar Formulação e Calcular Custo", type="primary", key="run_optimization_tab1"):
        
        from modules.utils import registrar_log_execucao # Importa aqui para evitar circular

        with st.spinner("Executando o solver de otimização (Programação Linear)..."):
            
            resultados = resolver_modelo_otimizado(
                materias_primas, 
                st.session_state.restricoes_dinamicas, 
                custo_maximo_usuario 
            )

            # Salva o resultado no estado de sessão (o st.session_state é global)
            st.session_state.status_text, \
            st.session_state.custo_final, \
            st.session_state.df_resultado, \
            st.session_state.df_comp, \
            st.session_state.df_gargalo = resultados
            
            if st.session_state.status_text in ['Optimal', 'Feasible']:
                registrar_log_execucao(
                    st.session_state.custo_final,
                    st.session_state.status_text
                )
                
        st.rerun()
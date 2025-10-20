import streamlit as st
import consulta_motor 
import plotly.express as px

def render_modo_consulta(materias_primas, lista_mps):
    """
    Renderiza a Aba 2: Modo Consulta.
    Permite ao usuário inserir uma fórmula e calcula seu custo e nutrientes.
    """
    st.header("2. Análise de Fórmula (Consulta)")
    st.info("Insira uma formulação existente (peso em %) para verificar sua composição nutricional e custo.")

    # Inicializa o dicionário de consulta se for a primeira vez
    if not st.session_state.formulacao_consulta:
        st.session_state.formulacao_consulta = {mp: 0.0 for mp in lista_mps}

    with st.expander("Insira a Porcentagem de Cada Matéria-Prima", expanded=True):
        
        col_inputs = st.columns(4) # 4 colunas para inputs mais compactos
        i = 0
        
        for mp in lista_mps:
            # Pega a MP
            st.session_state.formulacao_consulta[mp] = col_inputs[i % 4].number_input(
                f"{mp} (%)", 
                min_value=0.0,
                max_value=100.0,
                value=st.session_state.formulacao_consulta.get(mp, 0.0), 
                step=0.01,
                format="%.4f",
                key=f"consulta_{mp}"
            )
            i += 1
            
        # --- Verificação de Soma ---
        soma_percentual = sum(st.session_state.formulacao_consulta.values())
        
        if soma_percentual > 100.0001 or soma_percentual < 99.9999:
            st.error(f"⚠️ A soma total é {soma_percentual:.4f}%. **Aviso:** O cálculo será feito, mas a fórmula está incorreta (deve ser 100%).")
        else:
            st.success(f"Soma total: {soma_percentual:.2f}%. Pronto para calcular!")


    if st.button("🔍 Consultar Composição", type="secondary"):
        
        soma_inclusao = sum(st.session_state.formulacao_consulta.values())
        if soma_inclusao < 0.0001:
            st.warning("Diagnóstico Consulta: A soma da inclusão das Matérias-Primas é zero. Insira os pesos (%).")
        
        df_nutricional, custo_calculado = consulta_motor.calcular_nutrientes_e_custo(
            materias_primas, 
            st.session_state.formulacao_consulta
        )

        if not df_nutricional.empty:
            st.session_state.consulta_resultado_nut = df_nutricional
            st.session_state.consulta_resultado_custo = custo_calculado
        else:
            st.session_state.consulta_resultado_nut = None
            st.session_state.consulta_resultado_custo = 0.0
            st.error("Nenhuma MP foi incluída na consulta. Insira pesos (%).")


    # --- EXIBIÇÃO DOS RESULTADOS DA CONSULTA ---
    if st.session_state.get('consulta_resultado_nut') is not None:
        
        st.markdown("---")
        st.subheader("Resultado da Consulta")
        
        col_custo_c, col_soma_c = st.columns(2)
        with col_custo_c:
            st.metric("Custo Calculado (MP)", f"R$ {st.session_state.consulta_resultado_custo:.4f}")
        with col_soma_c:
            st.metric("Soma Total da Fórmula", f"{soma_percentual:.2f}%")

        st.markdown("##### Composição Nutricional da Fórmula")
        st.dataframe(consulta_motor.formatar_df_nutricional(st.session_state.consulta_resultado_nut.copy()), 
                      hide_index=True, use_container_width=True)
        
        # Gráfico de Barras
        fig_consulta = px.bar(
            st.session_state.consulta_resultado_nut,
            x='Nutriente',
            y='Valor Obtido',
            title='Composição Nutricional da Fórmula Consultada'
        )
        # Ajusta a cor de fundo do gráfico para o tema atual
        bg_color = "rgba(28, 28, 28, 0)" if st.session_state.is_dark_mode else "white"
        fig_consulta.update_layout(
            paper_bgcolor=bg_color,
            plot_bgcolor=bg_color
        )

        st.plotly_chart(fig_consulta, use_container_width=True)
        
    st.markdown("---")
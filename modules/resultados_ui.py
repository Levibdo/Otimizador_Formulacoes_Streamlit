import streamlit as st
import pandas as pd
import plotly.express as px
import io 

def render_resultados(materias_primas):
    """
    Renderiza a Aba 3: Resultados da Otimização.
    Exibe tabelas, gráficos e opções de exportação.
    """
    st.header("3. Resultados da Otimização")

    # Verifica se a otimização foi executada
    if st.session_state.status_text is not None:
        
        status_text = st.session_state.status_text
        custo_final = st.session_state.custo_final
        df_resultado = st.session_state.df_resultado
        df_comp = st.session_state.df_comp
        df_gargalo = st.session_state.df_gargalo
        COLUNA_PERCENTUAL_REAL = 'Peso (%)' 
        
        # Importa CUSTO_ROW_NAME aqui para evitar importação circular no motor de otimização
        from otimizacao_motor import CUSTO_ROW_NAME

        if status_text in ['Optimal', 'Feasible']:
            st.success(f"Status da Solução: **{status_text}** (Otimização Completa)")
            
            # Exibindo o Custo Total com o novo 'metric-card'
            st.markdown(f"""
                <div class='metric-card'>
                    <h4>Custo Total da Formulação (Real)</h4>
                    <h2>R$ {custo_final:.4f}</h2>
                </div>
            """, unsafe_allow_html=True) 

            # ---------------------
            # TABELAS DE RESULTADOS
            # ---------------------
            st.subheader("Tabelas de Resultados")
            
            df_resultado_final = df_resultado.copy()
            
            custos_unitarios = materias_primas.loc[CUSTO_ROW_NAME, :].to_dict()

            df_resultado_final['Custo Unitário (R$)'] = df_resultado_final['Matéria-Prima'].map(custos_unitarios)
            
            df_resultado_final['Custo na Fórmula (R$)'] = (
                df_resultado_final[COLUNA_PERCENTUAL_REAL] / 100
            ) * df_resultado_final['Custo Unitário (R$)']
            
            df_resultado_final['Custo Unitário (R$)'] = df_resultado_final['Custo Unitário (R$)'].apply(lambda x: f"R$ {x:.4f}")
            df_resultado_final['Custo na Fórmula (R$)'] = df_resultado_final['Custo na Fórmula (R$)'].apply(lambda x: f"R$ {x:.4f}")
            
            df_resultado_final = df_resultado_final[[
                'Matéria-Prima', 'Peso (%)', 'Custo Unitário (R$)', 'Custo na Fórmula (R$)'
            ]]
            
            st.markdown("##### 3.1. Fórmula Ideal (Pesos e Custo por MP)")
            st.dataframe(df_resultado_final, hide_index=True, use_container_width=True) 
            
            st.markdown("##### 3.2. Conferência Nutricional (Metas Atendidas)")
            st.dataframe(df_comp, hide_index=True, use_container_width=True) 

            if df_gargalo is not None and not df_gargalo.empty:
                st.markdown("##### 3.3. Análise de Restrições Ativas (Gargalos)")
                st.warning("O Preço Sombra indica o impacto no CUSTO ao relaxar/apertar a restrição.")
                st.dataframe(df_gargalo, hide_index=True, use_container_width=True) 
            else:
                st.info("Nenhuma restrição atuando como gargalo.")

            st.markdown("---")

            # ---------------------
            # GRÁFICOS (PLOTLY)
            # ---------------------
            st.subheader("Análise Gráfica")

            bg_color = "rgba(28, 28, 28, 0)" if st.session_state.is_dark_mode else "white"

            st.markdown("##### 📊 Distribuição de Matérias-Primas na Fórmula")
            fig = px.pie(
                df_resultado,
                values='Peso (%)',
                names='Matéria-Prima',
                title='Participação das MPs na Fórmula',
                color_discrete_sequence=px.colors.sequential.Blues, 
                hole=0.4 
            )
            fig.update_traces(textinfo='percent+label', pull=[0.05]*len(df_resultado)) 
            fig.update_layout(paper_bgcolor=bg_color, plot_bgcolor=bg_color)
            st.plotly_chart(fig, use_container_width=True)
            
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
                fig2.update_layout(paper_bgcolor=bg_color, plot_bgcolor=bg_color)
                st.plotly_chart(fig2, use_container_width=True)

            st.markdown("---")
            
            # ---------------------
            # HISTÓRICO E EXPORTAÇÃO
            # ---------------------
            try:
                # O caminho é relativo ao app_streamlit.py
                df_hist = pd.read_csv("resultados/log_execucao.csv")
                if not df_hist.empty and "Data" in df_hist.columns and "Custo Total" in df_hist.columns:
                    st.subheader("Histórico de Execuções")
                    st.line_chart(df_hist.set_index("Data")["Custo Total"])
                else:
                    st.info("Log de execução encontrado, mas vazio.")
                    
            except FileNotFoundError:
                st.info("Arquivo de log de execução ('resultados/log_execucao.csv') não encontrado para histórico.")

            st.markdown("---")

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
            
        else:
            st.error(f"FALHA na Otimização! Status: **{status_text}**")
            st.warning("O modelo é inviável. Revise suas restrições na aba 'Restrições e Metas'.")

    else:
        st.info("Acesse a aba 'Restrições e Metas' e clique no botão '🚀 Otimizar Formulação' para executar o modelo e visualizar os resultados nesta aba.")
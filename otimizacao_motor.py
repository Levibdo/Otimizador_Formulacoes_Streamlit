import pandas as pd
from pulp import *

# Define o nome da linha de custo para leitura
CUSTO_ROW_NAME = 'Custo'

def resolver_modelo_otimizado(materias_primas, df_metas, CUSTO_MAXIMO_FORMULA):
    """
    Executa o modelo de otimização de custo (Programação Linear)
    com base nas matrizes de dados (MP vs Nutrientes/Custo) e Metas.
    
    Retorna DataFrames prontos para exibição no Streamlit.
    """
    try:
        # ============================================================
        # 1. PRÉ-PROCESSAMENTO E VERIFICAÇÕES
        # ============================================================

        # Verificar se a linha de Custo existe antes de prosseguir
        if CUSTO_ROW_NAME not in materias_primas.index:
            raise ValueError(f"ERRO DE DADOS: A matriz deve ter uma LINHA chamada '{CUSTO_ROW_NAME}' no índice. Verifique 'MPs_data.xlsx'.")

        df_nutricionais = df_metas[df_metas['Tipo'] == 'Nutricional']
        df_inclusao = df_metas[df_metas['Tipo'] == 'Inclusão']

        # Prepara Metas Nutricionais
        metas_nutricionais = {}
        for _, row in df_nutricionais.iterrows():
            if row['Nome'] != CUSTO_ROW_NAME:
                metas_nutricionais[row['Nome']] = {'tipo': row['Restrição'], 'valor': row['Valor']}

        # Prepara Restrições de Inclusão
        MPs = materias_primas.columns.tolist() 
        restricoes_inclusao = {mp: {'min': 0.0, 'max': 1.0} for mp in MPs}

        for _, row in df_inclusao.iterrows():
            mp_nome_restricao = row['Nome']
            mp_encontrada = next(
                (mp for mp in MPs if mp.strip().lower() == mp_nome_restricao.strip().lower()), 
                None
            )
            
            if mp_encontrada:
                restricao = row['Restrição']
                valor = row['Valor']
                if restricao == 'Min':
                    restricoes_inclusao[mp_encontrada]['min'] = valor
                elif restricao == 'Max':
                    restricoes_inclusao[mp_encontrada]['max'] = valor
                elif restricao == 'Fixo':
                    restricoes_inclusao[mp_encontrada] = {'min': valor, 'max': valor}
        
        # Lê o Custo Real
        CUSTO_POR_MP = {mp: materias_primas.loc[CUSTO_ROW_NAME, mp] for mp in MPs}

        # ============================================================
        # 2. CRIAÇÃO E SOLUÇÃO DO MODELO PL
        # ============================================================

        problema = LpProblem("Formula_PD", LpMinimize)
        x = LpVariable.dicts("x", MPs, lowBound=0)

        # 1. Função Objetivo: Custo REAL Mínimo
        custo_expressao = lpSum([CUSTO_POR_MP[mp] * x[mp] for mp in MPs])
        problema += custo_expressao, "Custo_Total_Real"

        # 1.5. NOVA RESTRIÇÃO DE CUSTO MÁXIMO
        if CUSTO_MAXIMO_FORMULA > 0.0:
            problema += custo_expressao <= CUSTO_MAXIMO_FORMULA, "Maximo_Custo_Total" # <--- Restrição de Custo Máximo

        # 2. Restrição de Soma 100%
        problema += lpSum([x[mp] for mp in MPs]) == 1.0, "Soma_Total_100_Porcento"

        # 3. Restrições Nutricionais
        for nutriente, meta in metas_nutricionais.items():
            if nutriente in materias_primas.index:
                expr = lpSum([materias_primas.loc[nutriente, mp] * x[mp] for mp in MPs])
                if meta["tipo"] == ">=":
                    problema += expr >= meta["valor"], f"Minimo_{nutriente}"
                elif meta["tipo"] == "<=":
                    problema += expr <= meta["valor"], f"Maximo_{nutriente}"
                elif meta["tipo"] == "=":
                    problema += expr == meta["valor"], f"Exato_{nutriente}"

        # 4. Restrições de Inclusão (Min/Max de MP)
        for mp in MPs:
            if restricoes_inclusao[mp]['min'] > 0.0001:
                problema += x[mp] >= restricoes_inclusao[mp]['min'], f"Min_Inclusao_{mp}"
            if restricoes_inclusao[mp]['max'] < 0.9999:
                problema += x[mp] <= restricoes_inclusao[mp]['max'], f"Max_Inclusao_{mp}"

        problema.solve(PULP_CBC_CMD(msg=False))
        status_text = LpStatus[problema.status]

        if status_text not in ['Optimal', 'Feasible']:
            return status_text, None, None, None, None 
        
        # ============================================================
        # 3. EXTRACÃO DE RESULTADOS
        # ============================================================

        custo_final = value(problema.objective)

        # 3.1. Formulação Ideal
        resultados = []
        for mp in MPs:
            peso = x[mp].varValue * 100
            if peso > 0.0001:
                resultados.append({'Matéria-Prima': mp, 'Peso (%)': round(peso, 4)})
        df_resultado = pd.DataFrame(resultados).sort_values(by='Peso (%)', ascending=False)

        # 3.2. Conferência Nutricional
        comp = []
        for nutriente, meta in metas_nutricionais.items():
            teor_final = sum([materias_primas.loc[nutriente, mp] * x[mp].varValue for mp in MPs])
            comp.append({
                 'Nutriente': nutriente,
                 'Obtido': round(teor_final, 4),
                 'Meta': meta['valor'],
                 'Tipo': meta['tipo']
            })
        df_comp = pd.DataFrame(comp)

        # 3.3. Análise de Gargalos (Preço Sombra)
        restricoes_gargalo = []
        for name, c in problema.constraints.items():
            # A restrição 'Maximo_Custo_Total' não tem preço sombra significativo no contexto
            # da minimização, então a ignoramos aqui.
            if 'Soma_Total' not in name and 'Custo_Total' not in name and 'Maximo_Custo_Total' not in name: 
                shadow_price = c.pi
                if shadow_price is not None and abs(shadow_price) > 0.00001:
                    nome_formatado = name.replace("Minimo_", "Min ").replace("Maximo_", "Max ").replace("_Inclusao", " (Inclusão)").replace("_", " ").strip()
                    restricoes_gargalo.append({
                        'Restricao': nome_formatado,
                        'Preco Sombra': round(shadow_price, 6),
                        'Folga': round(c.slack, 4) if c.slack is not None else 0.0
                    })

        df_gargalo = None
        if restricoes_gargalo:
            df_gargalo = pd.DataFrame(restricoes_gargalo).sort_values(by='Preco Sombra', ascending=False)


        return status_text, custo_final, df_resultado, df_comp, df_gargalo

    except Exception as e:
        return f"ERRO INTERNO: {e}", None, None, None, None
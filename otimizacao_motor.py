import pandas as pd
from pulp import *

# Define o nome da linha de custo para leitura
CUSTO_ROW_NAME = 'Custo'

# [MODIFICADO] A função agora aceita 'restricoes_dinamicas' (lista de dicts) em vez de 'df_metas' (DataFrame)
def resolver_modelo_otimizado(materias_primas, restricoes_dinamicas, CUSTO_MAXIMO_FORMULA):
    """
    Executa o modelo de otimização de custo (Programação Linear)
    com base nas matrizes de dados (MP vs Nutrientes/Custo) e Restrições Dinâmicas.
    
    Retorna DataFrames prontos para exibição no Streamlit.
    """
    try:
        # ============================================================
        # 1. PRÉ-PROCESSAMENTO E VERIFICAÇÕES
        # ============================================================

        # Verificar se a linha de Custo existe antes de prosseguir
        if CUSTO_ROW_NAME not in materias_primas.index:
            raise ValueError(f"ERRO DE DADOS: A matriz deve ter uma LINHA chamada '{CUSTO_ROW_NAME}' no índice. Verifique 'MPs_data.xlsx'.")

        # [MODIFICADO] Separa as restrições dinâmicas em Nutricionais e de Inclusão/Limites de MP
        metas_nutricionais = {}
        restricoes_inclusao = {} # Dicionário para armazenar os limites Min/Max por MP
        MPs = materias_primas.columns.tolist()

        # Inicializa limites de inclusão (Min=0, Max=1) para todas as MPs
        for mp in MPs:
            restricoes_inclusao[mp] = {'min': 0.0, 'max': 1.0}

        # [MODIFICADO] Itera sobre a lista de dicionários do Streamlit
        for rest in restricoes_dinamicas:
            nome = rest['item']
            tipo = rest['tipo']
            valor = rest['valor']
            
            # -----------------------------------------------------------------
            # Lógica para classificar a restrição
            # -----------------------------------------------------------------
            
            if nome in materias_primas.index:
                # É um Nutriente (ou outra Linha de composição)
                metas_nutricionais[nome] = {'tipo': tipo, 'valor': valor}
            
            elif nome in MPs:
                # É uma Matéria-Prima (restrição de Inclusão Min/Max/Fixo)
                if tipo == '>=':
                    # Mínimo
                    restricoes_inclusao[nome]['min'] = valor
                elif tipo == '<=':
                    # Máximo
                    restricoes_inclusao[nome]['max'] = valor
                elif tipo == '=':
                    # Fixo
                    restricoes_inclusao[nome] = {'min': valor, 'max': valor}
        
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

        # 1.5. RESTRIÇÃO DE CUSTO MÁXIMO
        if CUSTO_MAXIMO_FORMULA > 0.00001:
            problema += custo_expressao <= CUSTO_MAXIMO_FORMULA, "Maximo_Custo_Total" 

        # 2. Restrição de Soma 100%
        problema += lpSum([x[mp] for mp in MPs]) == 1.0, "Soma_Total_100_Porcento"

        # 3. Restrições Nutricionais (USANDO AS NOVAS METAS)
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
        df_resultado = pd.DataFrame(resultados).sort_values(by='Peso (%)', ascending=False) # <--- Correção foi feita APÓS esta linha

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
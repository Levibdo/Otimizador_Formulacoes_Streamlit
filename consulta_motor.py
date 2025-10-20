import pandas as pd
from otimizacao_motor import CUSTO_ROW_NAME

def calcular_nutrientes_e_custo(materias_primas, formulacao_input):
    """
    Calcula a composição nutricional e o custo total de uma formulação fornecida.

    Args:
        materias_primas (pd.DataFrame): Matriz de dados de MPs e nutrientes (carregada).
        formulacao_input (dict): Dicionário {MP: Peso(%)}, onde Peso(%) deve somar 100%.

    Returns:
        tuple: (df_nutricional, custo_total)
    """
    # 1. Preparar a Série de Inclusão (converter % em decimal)
    # Filtra apenas as MPs que estão na formulação_input
    
    # DIVISÃO POR 100 É ESSENCIAL AQUI, POIS O INPUT ESTÁ EM PERCENTUAL (0 a 100)
    inclusao = pd.Series(formulacao_input) / 100.0
    
    # Garantir que a inclusão só tenha MPs válidas (presentes nas colunas da matriz)
    mps_validas = [mp for mp in inclusao.index if mp in materias_primas.columns]
    inclusao = inclusao.loc[mps_validas]

    if inclusao.sum() == 0:
        return pd.DataFrame(), 0.0

    # 2. Calcular Composição Nutricional
    
    # Pega apenas as linhas de nutrientes (excluindo a linha de custo)
    matriz_nutrientes = materias_primas.drop(index=[CUSTO_ROW_NAME], errors='ignore')
    
    # --- CORREÇÃO DA MULTIPLICAÇÃO DE MATRIZES ---
    # Matriz_Nutrientes (Índice=Nutrientes, Colunas=MPs)
    # Inclusao (Índice=MPs)
    
    # O método 'mul' com axis=1 multiplica cada COLUNA (MP) da matriz_nutrientes pelo
    # valor de inclusão correspondente no índice da Series 'inclusao'.
    composicao_por_mp = matriz_nutrientes.mul(inclusao, axis=1)
    
    # Soma as contribuições (ao longo das colunas/MPs) para obter o total por nutriente (linhas)
    composicao_total = composicao_por_mp.sum(axis=1) 
    # --- FIM DA CORREÇÃO ---
    
    # Montar o DataFrame de resultados nutricionais
    df_nutricional = pd.DataFrame({
        'Nutriente': composicao_total.index,
        'Valor Obtido': composicao_total.values
    })

    # 3. Calcular Custo Total (das MPs)
    custos_unitarios = materias_primas.loc[CUSTO_ROW_NAME, inclusao.index]
    custo_total = (inclusao * custos_unitarios).sum()
    
    return df_nutricional, custo_total

# Exemplo de como formatar a saída para o Streamlit (opcional, pode ser feito no app)
def formatar_df_nutricional(df_nutricional):
    if df_nutricional.empty:
        return pd.DataFrame({'Mensagem': ['Nenhuma Matéria-Prima selecionada.']})
    
    df_nutricional['Valor Obtido'] = df_nutricional['Valor Obtido'].apply(lambda x: f"{x:.4f}")
    return df_nutricional
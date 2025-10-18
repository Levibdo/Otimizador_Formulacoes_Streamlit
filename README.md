🚀 Otimizador de Formulações de Baixo Custo (Streamlit + PuLP)

Este projeto é uma ferramenta de Otimização de Programação Linear (PL) desenvolvida para o setor de P&D (Pesquisa e Desenvolvimento). O sistema encontra a formulação de custo mínimo que atende a todas as restrições de composição e limites de matérias-primas (MPs).

⚙️ Configuração e Instalação

Pré-requisitos

Certifique-se de ter o Python (3.7+) e o Git instalados em sua máquina.

1. Clonar o Repositório

Abra o terminal e baixe o código-fonte do projeto:
Bash

git clone https://github.com/Levibdo/Otimizador_Formulacoes_Streamlit.git
cd Otimizador_Formulacoes_Streamlit

2. Configurar e Ativar o Ambiente Virtual

É crucial usar um ambiente virtual isolado para evitar conflitos de dependências em seu sistema:

Cria o ambiente virtual (.venv)
```
python -m venv .venv
```
Ativa o ambiente virtual (Seu prompt deve mostrar (.venv) no início)

Linux/macOS
```
source .venv/bin/activate
```
Windows (CMD/PowerShell)
```
.\.venv\Scripts\activate
```


3. Instalar Dependências

Com o ambiente virtual ATIVO, use o uv para instalar as bibliotecas. O uv lerá as dependências listadas no arquivo central pyproject.toml:
Instala o uv (se ainda não o tiver)
```
pip install uv
```

Instala todas as dependências listadas no pyproject.toml
```
uv sync
```

4. Estrutura de Dados (Arquivos Excel)

O projeto requer dois arquivos Excel na pasta raiz para funcionar. Eles devem ser adicionados manualmente:
Arquivo	Descrição
MPs_data.xlsx	Matriz de composição: Matérias-Primas (Colunas) vs. Nutrientes/Custo (Linhas). Deve conter uma linha chamada 'Custo'.
Metas_e_Restricoes.xlsx	Tabela com as metas iniciais para Nutrientes e MPs (Nome, Restrição, Valor, Tipo).

▶️ Como Executar

Execute a aplicação Streamlit diretamente do terminal:

python -m streamlit run app_streamlit.py

A aplicação abrirá automaticamente no seu navegador, geralmente em http://localhost:8501.

📝 Uso da Aplicação

Seção 1: Definição de Metas e Restrições

    Custo Máximo Desejado: Defina o limite de custo da formulação (em R$ por unidade de produto).

    Metas Nutricionais: Ajuste as restrições (<=, >=, =) e os valores para os nutrientes obrigatórios.

    Restrições de MPs: Defina a inclusão mínima (Min), máxima (Max) ou o valor exato (Fixo) para as Matérias-Primas.

Seção 2: Resultados da Otimização

Após clicar em "🚀 Otimizar Formulação e Calcular Custo", o sistema exibirá:

    Status da Solução: (Optimal, Feasible, ou Inviável).

    Custo Total da Formulação (Real): O custo mínimo obtido.

    Fórmula Ideal: A porcentagem de inclusão de cada Matéria-Prima (e.g., Maltodextrina 33.755%).

    Análise de Gargalos (Preço Sombra): Identifica quais restrições estão ativas e quanto elas impactam o custo final. Valores positivos indicam quanto o custo aumentaria ao apertar a restrição.

🛠️ Tecnologias Utilizadas

    Python: Linguagem principal.

    Streamlit: Framework para a interface web interativa.

    PuLP: Biblioteca para modelagem e resolução de Programação Linear.

    Pandas: Manipulação e processamento de dados (matrizes e metas).

📄 Licença

Este projeto está licenciado sob a Licença MIT.

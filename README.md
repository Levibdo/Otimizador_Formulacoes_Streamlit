# 🚀 Otimizador de Formulações de Baixo Custo (Streamlit + PuLP)

**Otimização de formulações nutricionais e industriais com custo mínimo — projetado para equipes de P&D e Engenharia de Processos.**  
O sistema encontra automaticamente a **combinação ideal de matérias-primas (MPs)** que atende às **metas nutricionais e restrições de inclusão** ao menor custo possível.

---

## ✨ Principais Features

- ⚙️ **Otimização Dinâmica:** Defina restrições e metas nutricionais em tempo real pela interface web.
- 🔍 **Modo Consulta (Novo):** Calcule o custo e a composição nutricional de fórmulas já existentes ou experimentais.
- 🌓 **Controle de Tema:** Seletor de tema (claro/escuro) integrado ao cabeçalho.
- 🧩 **Arquitetura Modular:** Código organizado em módulos (UI, motor, análise) para manutenção fácil e extensões futuras.
- 📈 **Visualização Profissional:** Gráficos interativos com Plotly e métricas resumidas por cards.

---

## ⚙️ Configuração e Instalação

### 🧰 Pré-requisitos
Certifique-se de ter o **Python 3.8+** e o **Git** instalados.

### 🔽 Clonar o Repositório

```
git clone https://github.com/Levibdo/Otimizador_Formulacoes_Streamlit.git
```
```
cd Otimizador_Formulacoes_Streamlit
```
🧱 Configurar e Ativar o Ambiente Virtual
É altamente recomendado usar um ambiente virtual isolado:

# Criar ambiente virtual (.venv)
```
python -m venv .venv
```

# Ativar (Linux/macOS)
```
source .venv/bin/activate
```

# Ativar (Windows)
```
.\.venv\Scripts\activate
```
# 📦Instalar Dependências Com o ambiente virtual ativo, execute:

Instalar o gerenciador UV
```
pip install uv
```
Instalar dependências do projeto
```
uv sync
```
# ou, se preferir:
```
pip install -r requirements.txt
```
📊 Estrutura de Dados (Excel)
O projeto precisa de um arquivo Excel na pasta raiz:

Arquivo	Descrição
MPs_data.xlsx	Matriz de composição: Colunas = Matérias-Primas e Linhas = Nutrientes + 'Custo'. Deve conter uma linha chamada Custo no índice.

▶️ Como Executar
Execute o aplicativo com o comando:


```
streamlit run app_streamlit.py
```
A aplicação abrirá automaticamente no navegador, geralmente em
```
 http://localhost:8501
```
🧭 Estrutura da Aplicação
O app possui três abas principais:

1️⃣ Restrições e Metas (📊)
Entrada de dados para otimização.

Define custo máximo global e limites de inclusão (%) das MPs.

Permite ajustar metas nutricionais para os nutrientes.

2️⃣ Modo Consulta (🔍)
Insira porcentagens de MPs de uma fórmula já existente.

Calcula automaticamente:

Custo total da formulação

Composição nutricional

Exibe gráficos e tabelas interativos.

Resultados da Otimização (📈)
Status da solução: Ótima, Viável ou Inviável.

Custo mínimo obtido.

Tabela com inclusões (%) das MPs.

Comparativo entre valores obtidos e metas nutricionais.

(Opcional) Análise de Gargalos / Preço Sombra.

🛠️ Tecnologias Utilizadas

| Componente | Função |
| :--- | :--- |
| Python | Linguagem base. |
| Streamlit | Framework para a interface web interativa. |
| PuLP | Modelagem e resolução de Programação Linear. |
| Pandas | Manipulação e análise de dados (matrizes). |
| Plotly | Geração de gráficos dinâmicos e responsivos. |

📄 Licença
Este projeto está licenciado sob a MIT License.(LICENSE). Consulte o arquivo **LICENSE** na raiz do projeto para detalhes completos.
Sinta-se livre para usar, modificar e compartilhar com os devidos créditos.

💡 Créditos e Contato
Autor: Levi Oliveira
📬 Para dúvidas ou sugestões: abra uma issue ou envie um pull request.

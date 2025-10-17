# Imagem base Python
FROM python:3.11-slim

# Define diretório de trabalho
WORKDIR /Behavior_KAB

# Copia e instala dependências
COPY requirements_docker.txt .
RUN pip install --no-cache-dir -r requirements_docker.txt

# Copia toda a pasta Monitoramento (código + CSVs)
COPY . ./Monitoramento/

# Evita buffering de logs
ENV PYTHONUNBUFFERED=1

# Comando para rodar o Streamlit
CMD ["streamlit", "run", "Monitoramento/Dash.py", "--server.port=8501", "--server.address=0.0.0.0"]

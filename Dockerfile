# Usa una imagen oficial ligera de Python
FROM python:3.10-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de dependencias y las instala
# Esto se hace primero para aprovechar el caché de capas de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código y los datos al contenedor
COPY . .

# Expone el puerto por defecto de Streamlit
EXPOSE 8501

# Comando por defecto para arrancar el Dashboard
CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]

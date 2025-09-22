# This file tells Docker how to build your app
FROM python:3.9-slim                    # Base Python image
WORKDIR /app                            # Set working directory
COPY requirements.txt .                 # Copy dependencies list
RUN pip install -r requirements.txt     # Install dependencies
COPY . .                               # Copy your app code
EXPOSE 8501                            # Expose Streamlit port
CMD ["streamlit", "run", "main.py"]    # Command to start app

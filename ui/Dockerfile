# Pull official base image
FROM python:3.8-buster
# Set work directory
WORKDIR /usr/src/ui
# Install requirements
COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt
# Copy project
COPY . .
EXPOSE 8501
# Permissions
CMD ["streamlit", "run", "dashboard_map.py"]
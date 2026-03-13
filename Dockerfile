FROM python:3.9-slim

WORKDIR /app

# Install system dependencies (e.g., git needed for dbt deps)
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
# Adding dbt-snowflake and pytest as they are used in the pipeline orchestration and tests
RUN pip install --no-cache-dir -r requirements.txt dbt-snowflake pytest

# Copy the rest of the application
COPY . .

# Define optimal environment variables for Docker
ENV STORAGE_BACKEND=local
ENV LOCAL_ROOT=/app/data_lake

# Install dbt packages
RUN cd leagues_data_dbt && dbt deps

# Default command runs the end-to-end pipeline
CMD ["python", "-m", "scripts.run_pipeline"]

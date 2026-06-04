variable "postgres_image" {
  description = "Image for the PostgreSQL container"
  default    = "postgres:15"
}

variable "api_image" {
  description = "Image for the API container"
  default    = "your-dockerhub-username/api:latest"
}

variable "worker_image" {
  description = "Image for the Worker container"
  default    = "your-dockerhub-username/worker:latest"
}

variable "postgres_env_vars" {
  description = "Environment variables for PostgreSQL container"
  default    = {
    POSTGRES_USER = "admin"
    POSTGRES_PASSWORD = "admin"
    POSTGRES_DB = "logsdb"
  }
}

variable "api_env_vars" {
  description = "Environment variables for API container"
  default    = {
    DB_HOST = "postgres"
    DB_PORT = "5432"
    DB_USER = "admin"
    DB_PASSWORD = "admin"
    DB_NAME = "logsdb"
  }
}

variable "worker_env_vars" {
  description = "Environment variables for Worker container"
  default    = {
    DB_HOST = "postgres"
    DB_PORT = "5432"
    DB_USER = "admin"
    DB_PASSWORD = "admin"
    DB_NAME = "logsdb"
    LLM_API_KEY = "your_key_here"
  }
}
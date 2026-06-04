provider "kubernetes" {
  config_path = "~/.kube/config"
}



#################################################
# PostgreSQL Service
#################################################

resource "kubernetes_service" "postgres" {
  metadata {
    name = "postgres"
  }

  spec {
    selector = {
      app = "postgres"
    }

    port {
      port        = 5432
      target_port = 5432
    }

    type = "ClusterIP"
  }
}

#################################################
# PostgreSQL StatefulSet
#################################################

resource "kubernetes_stateful_set" "postgres" {
  metadata {
    name = "postgres"
    labels = {
      app = "postgres"
    }
  }

  spec {
    service_name = kubernetes_service.postgres.metadata[0].name

    replicas = 1

    selector {
      match_labels = {
        app = "postgres"
      }
    }

    template {
      metadata {
        labels = {
          app = "postgres"
        }
      }

      spec {
        container {
          name  = "postgres"
          image = "postgres:15"

          port {
            container_port = 5432
          }

          env {
            name  = "POSTGRES_USER"
            value = "admin"
          }

          env {
            name  = "POSTGRES_PASSWORD"
            value = "admin"
          }

          env {
            name  = "POSTGRES_DB"
            value = "logsdb"
          }

          volume_mount {
            name       = "postgres-storage"
            mount_path = "/var/lib/postgresql/data"
          }

          readiness_probe {
            exec {
              command = [
                "sh",
                "-c",
                "pg_isready -U admin -d logsdb"
              ]
            }

            initial_delay_seconds = 10
            period_seconds        = 5
          }

          liveness_probe {
            exec {
              command = [
                "sh",
                "-c",
                "pg_isready -U admin -d logsdb"
              ]
            }

            initial_delay_seconds = 30
            period_seconds        = 10
          }
        }
      }
    }

    volume_claim_template {
      metadata {
        name = "postgres-storage"
      }

      spec {
        access_modes = ["ReadWriteOnce"]

        resources {
          requests = {
            storage = "10Gi"
          }
        }
      }
    }
  }
}

#################################################
# API Service
#################################################

resource "kubernetes_service" "api" {
  metadata {
    name = "api"
  }

  spec {
    selector = {
      app = "api"
    }

    port {
      port        = 8000
      target_port = 8000
    }

    type = "ClusterIP"
  }
}

#################################################
# API Deployment
#################################################

resource "kubernetes_deployment" "api" {
  metadata {
    name = "api"
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "api"
      }
    }

    template {
      metadata {
        labels = {
          app = "api"
        }
      }

      spec {
        container {
          name  = "api"
          image = "docker.io/pawambust/ai-log-analyzer-api:latest"

          port {
            container_port = 8000
          }

          env {
            name  = "DB_HOST"
            value = "postgres"
          }

          env {
            name  = "DB_PORT"
            value = "5432"
          }

          env {
            name  = "DB_USER"
            value = "admin"
          }

          env {
            name  = "DB_PASSWORD"
            value = "admin"
          }

          env {
            name  = "DB_NAME"
            value = "logsdb"
          }
        }
      }
    }
  }
}

#################################################
# Worker Deployment
#################################################

resource "kubernetes_deployment" "worker" {
  metadata {
    name = "worker"
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "worker"
      }
    }

    template {
      metadata {
        labels = {
          app = "worker"
        }
      }

      spec {
        container {
          name  = "worker"
          image = "docker.io/pawambust/ai-log-analyzer-worker:latest"

          env {
            name  = "DB_HOST"
            value = "postgres"
          }

          env {
            name  = "DB_PORT"
            value = "5432"
          }

          env {
            name  = "DB_USER"
            value = "admin"
          }

          env {
            name  = "DB_PASSWORD"
            value = "admin"
          }

          env {
            name  = "DB_NAME"
            value = "logsdb"
          }

          env {
            name  = "LLM_API_KEY"
            value = "replace-me"
          }
        }
      }
    }
  }
}
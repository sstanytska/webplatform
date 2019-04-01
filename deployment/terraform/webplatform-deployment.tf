resource "kubernetes_deployment" "webplatform-deployment" {

  metadata {
    namespace = "${var.webplatform_namespace}"
    name = "webplatform-deployment"
    labels { run = "webplatform" }

  }

  spec {
    replicas = 3
    selector {
      match_labels { run = "webplatform" } }

    template {
      metadata {
        labels { run = "webplatform" }
      }

      spec {
        image_pull_secrets = [ { name = "nexus-creds" } ]

        container {
          image = "${var.webplatform_image}"
          name  = "webplatform-container"
          command = [ "python", "/app/app.py" ]

          env { name = "MYSQL_USER"     value = "${var.mysql_user}" }
          env { name = "MYSQL_DATABASE" value = "${var.mysql_database}" }
          env { name = "MYSQL_HOST"     value = "${var.mysql_host}" }

          env_from {
            secret_ref {
              name = "mysql-pass"
              name = "fuchicorp-secret"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "webplatform-service" {
  metadata {
    name = "fuchicorp-mysql"
    namespace = "${var.webplatform_namespace}"
  }
  spec {
    clusterIP = "null"
    selector { run = "webplatform-mysql"  }
    port {
      port = 3306
      target_port = 3306
    }

    type = "ClusterIP"
  }
}

resource "kubernetes_service" "webplatform-service" {
 
  
  metadata {
    name = "terraform-webplatform-service"
    namespace = "${var.webplatform_namespace}"
  }
  spec {
    selector { run = "webplatform"  }
    port {
      port = 80
      target_port = 5000
    }

    type = "LoadBalancer"
  }
}

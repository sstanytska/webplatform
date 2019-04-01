provider "google" {
  credentials = "${file("/fuchicorp/flask-kube.json")}"
  version     = "~> 2.3"
  project     = "striking-gadget-234002"
  region      = "us-central1-a"
}

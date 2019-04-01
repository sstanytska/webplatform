provider "google" {
  credentials = "${file("/root/.kube/flask-kube.json")}"
  project     = "striking-gadget-234002"
  region      = "us-central1-a"
}

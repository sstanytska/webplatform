provider "google" {
  credentials = "${file("/fuchicorp/flask-kube.json")}"
  project     = "striking-gadget-234002"
  region      = "us-central1-a"
}

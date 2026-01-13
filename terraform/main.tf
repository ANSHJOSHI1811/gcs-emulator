# Terraform Configuration for GCS Emulator VPC Testing
#
# This configuration tests the GCS emulator's VPC networking capabilities
# by creating a network, subnet, and compute instance.

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Configure the Google Cloud Provider to point to our emulator
provider "google" {
  project = "terraform-test"
  region  = "us-central1"
  zone    = "us-central1-a"
  
  # Authentication will use fake credentials via environment variable:
  # export GOOGLE_APPLICATION_CREDENTIALS="/path/to/fake-creds.json"
  # export CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE="http://localhost:8080/compute/v1/"
}

# Create a VPC Network
resource "google_compute_network" "vpc_network" {
  name                    = "tf-test-network"
  auto_create_subnetworks = false
  mtu                     = 1460
  routing_mode           = "REGIONAL"
  
  description = "Test VPC created by Terraform"
}

# Create a Subnet
resource "google_compute_subnetwork" "subnet" {
  name          = "tf-test-subnet"
  ip_cidr_range = "10.10.0.0/24"
  region        = "us-central1"
  network       = google_compute_network.vpc_network.id
  
  description = "Test subnet created by Terraform"
  
  # Optional: Enable private Google access
  private_ip_google_access = true
}

# Create a Firewall Rule (Allow SSH)
resource "google_compute_firewall" "allow_ssh" {
  name    = "tf-allow-ssh"
  network = google_compute_network.vpc_network.name
  
  description = "Allow SSH from anywhere"
  priority    = 1000
  direction   = "INGRESS"
  
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["ssh-enabled"]
}

# Create a Firewall Rule (Allow HTTP/HTTPS)
resource "google_compute_firewall" "allow_web" {
  name    = "tf-allow-web"
  network = google_compute_network.vpc_network.name
  
  description = "Allow HTTP and HTTPS from anywhere"
  priority    = 1000
  direction   = "INGRESS"
  
  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }
  
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["web-server"]
}

# Create a Compute Instance
resource "google_compute_instance" "vm_instance" {
  name         = "tf-test-vm"
  machine_type = "e2-micro"
  zone         = "us-central1-a"
  
  tags = ["ssh-enabled", "web-server"]
  
  boot_disk {
    initialize_params {
      image = "debian-11"
      size  = 10
    }
  }
  
  network_interface {
    network    = google_compute_network.vpc_network.self_link
    subnetwork = google_compute_subnetwork.subnet.self_link
    
    # Request external IP
    access_config {
      # Ephemeral external IP
    }
  }
  
  metadata = {
    startup-script = <<-EOF
      #!/bin/bash
      echo "Hello from Terraform-created VM!"
      echo "Internal IP: $(hostname -I)"
    EOF
  }
}

# Outputs
output "network_name" {
  description = "Name of the VPC network"
  value       = google_compute_network.vpc_network.name
}

output "network_self_link" {
  description = "Self link of the VPC network"
  value       = google_compute_network.vpc_network.self_link
}

output "subnet_name" {
  description = "Name of the subnet"
  value       = google_compute_subnetwork.subnet.name
}

output "subnet_cidr" {
  description = "CIDR range of the subnet"
  value       = google_compute_subnetwork.subnet.ip_cidr_range
}

output "vm_name" {
  description = "Name of the VM instance"
  value       = google_compute_instance.vm_instance.name
}

output "vm_internal_ip" {
  description = "Internal IP of the VM"
  value       = google_compute_instance.vm_instance.network_interface[0].network_ip
}

output "vm_external_ip" {
  description = "External IP of the VM"
  value       = try(google_compute_instance.vm_instance.network_interface[0].access_config[0].nat_ip, "none")
}

output "vm_status" {
  description = "Status of the VM instance"
  value       = google_compute_instance.vm_instance.current_status
}

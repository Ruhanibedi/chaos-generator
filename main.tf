provider "aws" {
  region = "ap-south-1"
}

# EKS cluster is provisioned via eksctl for this demo
# Terraform manages supporting infrastructure

resource "aws_s3_bucket" "chaos_results" {
  bucket = "chaos-platform-results-${random_id.suffix.hex}"
}

resource "random_id" "suffix" {
  byte_length = 4
}

output "chaos_results_bucket" {
  value = aws_s3_bucket.chaos_results.bucket
}

# Declare which version of Terraform and which provider plugin to use.
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configure the AWS connection (region, default tags)
provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "docuquery"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Look up available AZs dynamically (used later by VPC)
data "aws_availability_zones" "available" {
  state = "available"
}

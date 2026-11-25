terraform {
  # 1.10+ for native S3 state locking (use_lockfile); 1.6+ for import blocks with variables
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      project     = var.project
      environment = var.environment
      managed-by  = "terraform"
    }
  }
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Usaremos local state no MVP inicial. 
  # Na Fase 3, podemos migrar isso para um backend S3 remoto.
  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "FuteData"
      Environment = "Dev"
      ManagedBy   = "Terraform"
    }
  }
}

variable "aws_region" {
  description = "Região da AWS para deploy"
  type        = string
  default     = "us-east-1"
}

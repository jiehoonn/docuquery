variable "project_name" {
  description = "Prefix for resource names"
  type        = string
  default     = "docuquery"
}

variable "environment" {
  description = "Validation block that only allows 'dev', 'staging', 'prod'"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
  type    = string
  default = "dev"
}

variable "aws_region" {
  description = "Specify AWS Region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR Address"
  type        = string
  default     = "10.0.0.0/16"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "docuquery"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "docuquery"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true # only for secrets
}

variable "db_instance_class" {
  description = "Database Instance Class"
  type        = string
  default     = "db.t3.micro"
}

variable "jwt_secret" {
  description = "JWT Secret"
  type        = string
  sensitive   = true # only for secrets
}

variable "gemini_api_key" {
  description = "Gemini API Key"
  type        = string
  default     = ""
  sensitive   = true # only for secrets
}

variable "qdrant_instance_type" {
  description = "Qdrant instance type"
  type        = string
  default     = "t3.micro"
}

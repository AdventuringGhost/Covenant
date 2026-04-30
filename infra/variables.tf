# Input variables: Azure region, VM size, database credentials, and environment name

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "vm_size" {
  description = "Azure VM SKU for the API host"
  type        = string
  default     = "Standard_B2s"
}

variable "db_admin_password" {
  description = "PostgreSQL administrator password"
  type        = string
  sensitive   = true
}

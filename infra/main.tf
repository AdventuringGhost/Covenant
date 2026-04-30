# Main Terraform config: resource group, Azure VM, PostgreSQL Flexible Server — REQUIRES EXPLICIT APPROVAL BEFORE APPLY

resource "azurerm_resource_group" "covenant" {
  name     = "rg-covenant-${var.environment}"
  location = var.location

  tags = {
    project = "covenant"
    env     = var.environment
  }
}

# TODO: add virtual network, subnet, NSG, VM, PostgreSQL Flexible Server, pgvector extension
# Run `terraform plan` first; never apply without Skipper's explicit written approval

# Output values exposed after apply: VM public IP, PostgreSQL FQDN, resource group name

output "vm_public_ip" {
  description = "Public IP of the Covenant API VM"
  value       = azurerm_public_ip.covenant.ip_address
}

output "postgres_fqdn" {
  description = "Fully-qualified domain name of the PostgreSQL server"
  value       = azurerm_postgresql_flexible_server.covenant.fqdn
}

output "resource_group_name" {
  description = "Name of the resource group containing all Covenant resources"
  value       = azurerm_resource_group.covenant.name
}

variable "google_api_key" {
  description = "Google Generative AI API Key"
  type        = string
  sensitive   = true
}

variable "DISCORD_WEBHOOK_URL" {
    description = "Discord Webhook URL for notifications"
    type        = string    
    sensitive = true
}
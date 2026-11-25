variable "bucket_name" {
  description = "The lane's bucket (S3_COPY_BUCKET), e.g. veratree-bot-sandbox"
  type        = string
}

variable "project" {
  description = "Project home name, e.g. bot or nifty"
  type        = string
}

variable "environment" {
  description = "Deployment lane (ENVIRONMENT), e.g. sandbox or prod"
  type        = string
}

variable "region" {
  description = "AWS region for the lane's resources"
  type        = string
}

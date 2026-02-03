output "alb_dns_name" {
  description = "API URL"
  value       = aws_lb.main.dns_name
}

output "rds_endpoint" {
  description = "Db connection string for debugging"
  value       = aws_db_instance.instance.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis host for debugging"
  value       = aws_elasticache_cluster.cluster.cache_nodes[0].address
  sensitive   = true
}

output "s3_bucket_name" {
  description = "Bucket name for document uploads"
  value       = aws_s3_bucket.documents.id
}

output "sqs_queue_url" {
  description = "Queue URL for the processing worker"
  value       = aws_sqs_queue.sqs.url
}

output "ecr_repository_url" {
  description = "Where to push Docker images"
  value       = aws_ecr_repository.app.repository_url
}

output "qdrant_private_ip" {
  description = "Qdrant endpoint (private, only reachable from VPC)"
  value       = aws_instance.instance.private_ip
}

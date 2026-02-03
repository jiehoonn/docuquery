resource "aws_elasticache_subnet_group" "elasticache" {
  name       = "${var.project_name}-${var.environment}-redis-subnet"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  tags       = { Name = "${var.project_name}-${var.environment}-elasticache-subnet" }
}

resource "aws_elasticache_cluster" "cluster" {
  cluster_id = "${var.project_name}-${var.environment}-redis"

  engine         = "redis"
  engine_version = "7.0"

  node_type       = "cache.t3.micro"
  num_cache_nodes = 1

  port = 6379

  subnet_group_name = aws_elasticache_subnet_group.elasticache.name

  security_group_ids = [aws_security_group.redis.id]

  tags = { Name = "${var.project_name}-${var.environment}-cluster" }
}


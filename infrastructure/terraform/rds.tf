resource "aws_db_subnet_group" "db" {
  name       = "${var.project_name}-${var.environment}-db-subnet"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]
  tags       = { Name = "${var.project_name}-${var.environment}-db-subnet" }
}

resource "aws_db_instance" "instance" {
  identifier     = "${var.project_name}-${var.environment}-db"
  engine         = "postgres"
  engine_version = "15"
  instance_class = var.db_instance_class

  allocated_storage = 20
  db_name           = var.db_name
  username          = var.db_username
  password          = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.db.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  skip_final_snapshot     = true
  backup_retention_period = 7

  tags = { Name = "${var.project_name}-${var.environment}-db" }
}


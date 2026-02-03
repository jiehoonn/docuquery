resource "aws_instance" "instance" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.qdrant_instance_type
  subnet_id              = aws_subnet.private_1.id
  vpc_security_group_ids = [aws_security_group.qdrant.id]
  user_data              = <<-EOF
        #!/bin/bash
        yum update -y
        yum install -y docker
        systemctl start docker
        systemctl enable docker
        docker run -d --restart always -p 6333:6333 -p 6334:6334 -v /qdrant_data:/qdrant/storage qdrant/qdrant
    EOF
  tags                   = { Name = "${var.project_name}-${var.environment}-qdrant-instance" }
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}
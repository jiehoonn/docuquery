# 1. Create the role with a trust policy (who can assume it)
resource "aws_iam_role" "ecs_execution_role" {
  name = "ecs_execution"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com" # ECS can use this role
      }
    }]
  })
}

resource "aws_iam_role" "ecs_task_role" {
  name = "ecs_task"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com" # ECS can use this role
      }
    }]
  })
}

# 2. Attach AWS-managed policies (pre-built by Amazon)
resource "aws_iam_role_policy_attachment" "ecs_execution_role" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# 3. Create custom inline policies for specific permissions
resource "aws_iam_role_policy" "ecs_task_s3" {
  name = "${var.project_name}-s3-access"
  role = aws_iam_role.ecs_task_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
      Resource = "arn:aws:s3:::${var.project_name}-*/*"
    }]
  })
}

resource "aws_iam_role_policy" "ecs_task_sqs" {
  name = "${var.project_name}-sqs-access"
  role = aws_iam_role.ecs_task_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["sqs:SendMessage", "sqs:ReceiveMessage", "sqs:DeleteMessage"]
      Resource = "arn:aws:sqs:*:*:${var.project_name}-*"
    }]
  })
}

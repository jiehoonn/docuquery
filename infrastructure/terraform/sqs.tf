resource "aws_sqs_queue" "dlq" {
  name = "${var.project_name}-${var.environment}-dlq"
  tags = { Name = "${var.project_name}-${var.environment}-dlq" }
}

resource "aws_sqs_queue" "sqs" {
  name                       = "${var.project_name}-${var.environment}-document-processing"
  visibility_timeout_seconds = 300
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
  tags = { Name = "${var.project_name}-${var.environment}-sqs" }
}
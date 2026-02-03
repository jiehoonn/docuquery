resource "aws_s3_bucket" "documents" {
  bucket        = "${var.project_name}-${var.environment}-documents"
  force_destroy = true
  tags          = { Name = "${var.project_name}-${var.environment}-s3-bucket" }
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "documents" {
  bucket                  = aws_s3_bucket.documents.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
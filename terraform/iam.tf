# ---------------------------------------------------------------------------
# IAM Roles for Lambdas and Databricks Access
# ---------------------------------------------------------------------------

# Role genérica para as futuras funções Lambda dos coletores
resource "aws_iam_role" "lambda_collector_role" {
  name = "futedata-lambda-collector-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Permissão para a Lambda escrever no S3 (Raw e Audit)
resource "aws_iam_role_policy" "lambda_s3_access" {
  name = "futedata-lambda-s3-access"
  role = aws_iam_role.lambda_collector_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ]
        Effect = "Allow"
        Resource = [
          "${aws_s3_bucket.lakehouse_buckets["raw"].arn}/*",
          "${aws_s3_bucket.lakehouse_buckets["audit"].arn}/*"
        ]
      }
    ]
  })
}

# Policy para Databricks (preparação para Fase 4)
resource "aws_iam_policy" "databricks_s3_access" {
  name        = "futedata-databricks-s3-policy"
  description = "Acesso do Databricks aos buckets do FuteData Lakehouse"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Effect = "Allow"
        Resource = [
          for bucket in local.buckets : "${aws_s3_bucket.lakehouse_buckets[bucket].arn}/*"
        ]
      },
      {
        Action = [
          "s3:ListBucket"
        ]
        Effect = "Allow"
        Resource = [
          for bucket in local.buckets : aws_s3_bucket.lakehouse_buckets[bucket].arn
        ]
      }
    ]
  })
}

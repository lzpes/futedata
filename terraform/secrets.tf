# ---------------------------------------------------------------------------
# AWS Secrets Manager
# ---------------------------------------------------------------------------

resource "aws_secretsmanager_secret" "football_data_api_key" {
  name        = "futedata/prod/football_data_api_key"
  description = "Chave de API do football-data.org para extração"
}

# O valor do secret em si geralmente não é colocado em plain-text no terraform.
# A Lambda fará a leitura desse secret em runtime.

resource "aws_secretsmanager_secret" "rds_credentials" {
  name        = "futedata/prod/rds_credentials"
  description = "Credenciais do banco de dados relacional (SQL Server/Db2)"
}

# Permissão para a Lambda ler o secret
resource "aws_iam_role_policy" "lambda_secrets_access" {
  name = "futedata-lambda-secrets-access"
  role = aws_iam_role.lambda_collector_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "secretsmanager:GetSecretValue"
        Effect = "Allow"
        Resource = [
          aws_secretsmanager_secret.football_data_api_key.arn,
          aws_secretsmanager_secret.rds_credentials.arn
        ]
      }
    ]
  })
}

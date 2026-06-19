# ---------------------------------------------------------------------------
# S3 Buckets do Data Lake
# ---------------------------------------------------------------------------

locals {
  # Adicionamos um sufixo randômico ou account_id em produção,
  # mas para o MVP usaremos um prefixo fixo
  bucket_prefix = "futedata-scoutmarket"
  
  buckets = [
    "raw",
    "bronze",
    "silver",
    "gold",
    "checkpoints",
    "audit"
  ]
}

resource "aws_s3_bucket" "lakehouse_buckets" {
  for_each = toset(local.buckets)

  bucket = "${local.bucket_prefix}-${each.key}"
}

# Bloquear acesso público por segurança
resource "aws_s3_bucket_public_access_block" "block_public" {
  for_each = aws_s3_bucket.lakehouse_buckets

  bucket                  = each.value.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Versionamento habilitado nas camadas processadas e checkpoints
resource "aws_s3_bucket_versioning" "versioning" {
  for_each = aws_s3_bucket.lakehouse_buckets

  bucket = each.value.id

  versioning_configuration {
    status = contains(["bronze", "silver", "gold", "checkpoints"], each.key) ? "Enabled" : "Suspended"
  }
}

resource "aws_security_group" "rds_sg" {
  name        = "futedata_rds_sg"
  description = "Permitir conexao ao SQL Server RDS"

  ingress {
    from_port   = 1433
    to_port     = 1433
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Permitir SQL Server de qualquer IP (Para fins de MVP)"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "futedata_rds_sg"
  }
}

resource "aws_db_instance" "futedata_sqlserver" {
  identifier             = "futedata-sqlserver"
  allocated_storage      = 20
  engine                 = "sqlserver-ex"
  engine_version         = "15.00.4322.2.v1" # SQL Server 2019 Express (mais estável para t3.micro)
  instance_class         = "db.t3.micro"
  username               = "adminfute"
  password               = "FuteData#2026!"
  publicly_accessible    = true
  skip_final_snapshot    = true
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  license_model          = "license-included"

  tags = {
    Name = "FuteData-SQLServer-RDS"
  }
}

output "rds_endpoint" {
  value       = aws_db_instance.futedata_sqlserver.endpoint
  description = "Endpoint de conexao do banco de dados (Host:Port)"
}

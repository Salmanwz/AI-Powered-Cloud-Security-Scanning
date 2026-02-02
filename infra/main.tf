provider "aws" {
  region = "us-east-1"
  shared_config_files      = ["$HOME/.aws/config"]
  shared_credentials_files = ["$HOME/.aws/credentials"]
}

resource "aws_iam_policy" "S3EncryptionReadPolicy" {
  name        = "S3EncryptionReadPolicy"
  description = "IAM policy for S3 scanning operations"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListAllMyBuckets",
          "s3:GetEncryptionConfiguration"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role" "LambdaS3ScannerRole" {
  name = "LambdaS3ScannerRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.LambdaS3ScannerRole.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "s3_encryption_read" {
  role       = aws_iam_role.LambdaS3ScannerRole.name
  policy_arn = aws_iam_policy.S3EncryptionReadPolicy.arn
}

resource "aws_lambda_layer_version" "dependencies" {
  filename            = "../s3_scanner_layer.zip"
  layer_name          = "s3-scanner-dependencies"
  compatible_runtimes = ["python3.13"]
  source_code_hash    = filebase64sha256("../s3_scanner_layer.zip")
}

resource "aws_lambda_function" "s3_security_scanner" {
  filename         = "../s3_scanner.zip"
  function_name    = "s3-security-scanner"
  role             = aws_iam_role.LambdaS3ScannerRole.arn
  handler          = "s3_scanner.lambda_handler"
  runtime          = "python3.13"
  timeout          = 30
  layers           = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      DISCORD_WEBHOOK_URL = var.DISCORD_WEBHOOK_URL
      GOOGLE_API_KEY      = var.google_api_key  # Or hardcode if not using variables
    }
  }
}

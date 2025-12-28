# --- 1. PROVIDER AND BASICS ---
provider "aws" {
  region = "eu-central-1" # Frankfurt
}

# --- 2. STORAGE LAYER (Medallion Architecture) ---

resource "aws_s3_bucket" "bronze" {
  bucket = "smartdrive-telemetry-bronze"
  tags   = { Project = "SmartDrive", Layer = "Bronze" }
}

resource "aws_s3_bucket" "silver" {
  bucket = "smartdrive-telemetry-silver"
  tags   = { Project = "SmartDrive", Layer = "Silver" }
}

resource "aws_s3_bucket" "gold" {
  bucket = "smartdrive-telemetry-gold"
  tags   = { Project = "SmartDrive", Layer = "Gold" }
}

resource "aws_s3_bucket_versioning" "bronze_versioning" {
  bucket = aws_s3_bucket.bronze.id
  versioning_configuration {
    status = "Enabled"
  }
}

# --- 3. ERROR HANDLING ---

resource "aws_sqs_queue" "alert_dlq" {
  name                      = "smartdrive-ingest-dlq"
  message_retention_seconds = 1209600 # 14 days
}

# --- 4. PERMISSIONS (IAM) ---

# Role for IoT Core
resource "aws_iam_role" "iot_ingest_role" {
  name = "smartdrive-iot-ingest-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "iot.amazonaws.com" }
    }]
  })
}

# Permissions for S3 write access and SQS (DLQ) usage
resource "aws_iam_role_policy" "iot_ingest_policy" {
  name = "smartdrive-iot-ingest-policy"
  role = aws_iam_role.iot_ingest_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["s3:PutObject"]
        Effect   = "Allow"
        Resource = "${aws_s3_bucket.bronze.arn}/*"
      },
      {
        Action   = ["sqs:SendMessage"]
        Effect   = "Allow"
        Resource = aws_sqs_queue.alert_dlq.arn
      }
    ]
  })
}

# --- 5. INGESTION RULE (IoT Core) ---

resource "aws_iot_topic_rule" "obd_telemetry_rule" {
  name        = "SmartDriveOBDIngest"
  description = "Saving OBD-II data to the Bronze layer"
  enabled     = true
  sql         = "SELECT *, topic(2) as vin FROM 'vehicle/+/telemetry'"
  sql_version = "2016-03-23"

  # Saving data to S3 (Cold Path)
  s3 {
    role_arn    = aws_iam_role.iot_ingest_role.arn
    bucket_name = aws_s3_bucket.bronze.id
    key         = "raw/$${topic(2)}/$${timestamp()}.json"
  }

  error_action {
    sqs {
      role_arn    = aws_iam_role.iot_ingest_role.arn
      queue_url   = aws_sqs_queue.alert_dlq.url
      use_base64  = false
    }
  }
}

# --- 6. SILVER PROCESSING LAMBDA ---
resource "aws_lambda_function" "silver_processor" {
  filename      = "processor.zip"
  function_name = "smartdrive-silver-processor"
  role          = aws_iam_role.lambda_exec_role.arn # Must follow Least Privilege
  handler       = "index.lambda_handler"
  runtime       = "python3.9"

  environment {
    variables = {
      SILVER_BUCKET = aws_s3_bucket.silver.id
    }
  }
}

# --- 7. S3 EVENT TRIGGER ---
resource "aws_lambda_permission" "allow_s3_bronze" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.silver_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.bronze.arn
}

resource "aws_s3_bucket_notification" "bronze_trigger" {
  bucket = aws_s3_bucket.bronze.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.silver_processor.arn
    events              = ["s3:ObjectCreated:*"]
  }
  depends_on = [aws_lambda_permission.allow_s3_bronze]
}

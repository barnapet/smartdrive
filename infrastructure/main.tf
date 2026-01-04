# --- PROCESSOR ARTIFACT GENERATION ---
data "archive_file" "processor_zip" {
  type        = "zip"
  # Packaging the entire directory, not just a single file
  source_dir  = "${path.module}/../lambda_functions/processor"
  output_path = "${path.module}/processor.zip"
  
  # Exclude build artifacts to minimize package size
  excludes    = ["__pycache__", "*.pyc"]
}

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

resource "aws_s3_bucket_lifecycle_configuration" "bronze_lifecycle" {
  bucket = aws_s3_bucket.bronze.id

  rule {
    id     = "archive-old-telemetry"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    expiration {
      days = 90
    }
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
  filename         = data.archive_file.processor_zip.output_path
  function_name    = "smartdrive-silver-processor"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "index.lambda_handler"
  
  # Hash based on the entire ZIP content (triggers update on any file change)
  source_code_hash = data.archive_file.processor_zip.output_base64sha256
  
  runtime          = "python3.9"
  timeout          = 60       
  memory_size      = 512      
  
  # AWS SDK for Pandas Layer (Frankfurt / Py3.9)
  layers = [
    "arn:aws:lambda:eu-central-1:336392948345:layer:AWSSDKPandas-Python39:12"
  ]

  environment {
    variables = {
      SILVER_BUCKET_NAME = aws_s3_bucket.silver.bucket
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

# --- 8. DATA SOURCES FOR ACCOUNT ID AND REGION ---
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# --- 9. IOT POLICY (Javított verzió) ---
resource "aws_iot_policy" "smartdrive_policy" {
  name = "SmartDriveVehiclePolicy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["iot:Connect"]
        Effect   = "Allow"
        Resource = "arn:aws:iot:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:client/$${iot:Connection.Thing.ThingName}"
      },
      {
        Action   = ["iot:Publish"]
        Effect   = "Allow"
        Resource = "arn:aws:iot:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:topic/vehicle/$${iot:Connection.Thing.ThingName}/telemetry"
      }
    ]
  })
}

resource "aws_iot_thing" "test_vehicle" {
  name = "TESTVIN123456789"
}

# --- 10. LAMBDA EXECUTION ROLE ---
resource "aws_iam_role" "lambda_exec_role" {
  name = "smartdrive-lambda-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "smartdrive-lambda-policy"
  role = aws_iam_role.lambda_exec_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { # Read access from the Bronze layer
        Action   = ["s3:GetObject"]
        Effect   = "Allow"
        Resource = "${aws_s3_bucket.bronze.arn}/*"
      },
      { # Write access to the Silver layer
        Action   = ["s3:PutObject"]
        Effect   = "Allow"
        Resource = "${aws_s3_bucket.silver.arn}/*"
      },
      { # CloudWatch logging for observability
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Effect   = "Allow"
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# --- 11. GOLD LAYER: DTC GLOBAL CACHE (DynamoDB) ---
resource "aws_dynamodb_table" "dtc_cache" {
  name           = "DTC_Global_Cache"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "dtc_id"

  attribute {
    name = "dtc_id"
    type = "S"
  }

  tags = {
    Project = "SmartDrive"
    Layer   = "Gold"
  }
}

# --- 12. SECRETS FOR THIRD-PARTY APIS ---
resource "aws_secretsmanager_secret" "openai_key" {
  name        = "smartdrive/openai-key"
  description = "OpenAI API key for Mechanic-Translator"
}

# --- 13. MECHANIC-TRANSLATOR LAMBDA ---
resource "aws_lambda_function" "mechanic_translator" {
  filename      = "mechanic_translator.zip"
  function_name = "smartdrive-mechanic-translator"
  role          = aws_iam_role.lambda_exec_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"
  layers        = [aws_lambda_layer_version.openai_layer.arn]
  source_code_hash = filebase64sha256("mechanic_translator.zip")
  timeout      = 20    
  memory_size  = 256
  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.dtc_cache.name
    }
  }
}

# --- 14. EXTENDED PERMISSIONS FOR LAMBDA ---
resource "aws_iam_role_policy" "lambda_translator_policy" {
  name = "smartdrive-lambda-translator-policy"
  role = aws_iam_role.lambda_exec_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"]
        Effect   = "Allow"
        Resource = aws_dynamodb_table.dtc_cache.arn
      },
      {
        Action   = ["secretsmanager:GetSecretValue"]
        Effect   = "Allow"
        Resource = aws_secretsmanager_secret.openai_key.arn
      }
    ]
  })
}

# --- 15. LAMBDA LAYER FOR OPENAI LIBRARY ---
resource "aws_lambda_layer_version" "openai_layer" {
  filename            = "openai_layer.zip"
  layer_name          = "openai_library"
  compatible_runtimes = ["python3.9"]
  source_code_hash    = filebase64sha256("openai_layer.zip")
}

# --- 16. GOLD LAYER: VEHICLE INSIGHTS (SOH & Monitoring) ---
resource "aws_dynamodb_table" "vehicle_insights" {
  name           = "smartdrive-vehicle-insights"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "vin"
  range_key      = "timestamp"

  attribute {
    name = "vin"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  tags = {
    Project = "SmartDrive"
    Layer   = "Gold"
  }
}

# ---17. GOLD PROCESSOR ARTIFACT ---
data "archive_file" "gold_processor_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda_functions/gold_processor"
  output_path = "${path.module}/gold_processor.zip"
  excludes    = ["__pycache__", "*.pyc"]
}

# --- 18. GOLD PROCESSOR LAMBDA ---
resource "aws_lambda_function" "gold_processor" {
  filename         = data.archive_file.gold_processor_zip.output_path
  function_name    = "smartdrive-gold-processor"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "logic.handler"
  
  source_code_hash = data.archive_file.gold_processor_zip.output_base64sha256
  
  runtime          = "python3.9"
  timeout          = 30
  memory_size      = 256
  
  layers = [
    "arn:aws:lambda:eu-central-1:336392948345:layer:AWSSDKPandas-Python39:12"
  ]

  environment {
    variables = {
      INSIGHTS_TABLE = aws_dynamodb_table.vehicle_insights.name
    }
  }
}

# --- 19. IAM PERMISSIONS FOR GOLD LAYER ---
resource "aws_iam_role_policy" "gold_lambda_policy" {
  name = "smartdrive-gold-lambda-policy"
  role = aws_iam_role.lambda_exec_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:Query"]
        Effect   = "Allow"
        Resource = aws_dynamodb_table.vehicle_insights.arn
      }
    ]
  })
}

# --- 20. S3 TRIGGER FOR GOLD LAYER ---
resource "aws_lambda_permission" "allow_s3_silver" {
  statement_id  = "AllowExecutionFromS3Silver"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.gold_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.silver.arn
}

resource "aws_s3_bucket_notification" "silver_trigger" {
  bucket = aws_s3_bucket.silver.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.gold_processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".parquet"
  }
  
  depends_on = [aws_lambda_permission.allow_s3_silver]
}

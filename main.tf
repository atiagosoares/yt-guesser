variable "PROJECT" {
  type = string
  default = "yt-guesser"
}

variable "ENV" {
  type = string
  default = "dev"
}

variable "OPENAI_API_KEY" {
  type = string
  sensitive = true
}

terraform {
  backend "s3" {
    bucket = "terraform-45370"
    key    = "yt-guesser/state"
    region = "us-east-1"
  }
}

# ================= PARAMTERS =================
resource "aws_ssm_parameter" "google_token" {
  name  = "${var.PROJECT}-${var.ENV}-google-token"
  type  = "SecureString"
  value = file("token.json") 
}

resource "aws_ssm_parameter" "openai_api_key" {
  name  = "${var.PROJECT}-${var.ENV}-openai-api-key"
  type  = "SecureString"
  value = var.OPENAI_API_KEY
}

# ================= S3 BUCKETS =================

resource "aws_s3_bucket" "original_transcripts" {
  bucket = "${var.PROJECT}-${var.ENV}-transcripts"
}

# ================= Database =================
# - Channels
resource "aws_dynamodb_table" "channels_table" {
  name           = "${var.PROJECT}-${var.ENV}-channels"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }
}
# - Videos
resource "aws_dynamodb_table" "videos_table" {
  name           = "${var.PROJECT}-${var.ENV}-videos"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "channel_id"
    type = "S"
  }


  attribute {
    name = "published_at"
    type = "S"
  }

  global_secondary_index {
    name = "channel_id-index"
    hash_key = "channel_id"
    range_key = "published_at"
    projection_type = "ALL"
  }
}
# - Transcripts
resource "aws_dynamodb_table" "transcripts_table" {
  name           = "${var.PROJECT}-${var.ENV}-transcripts"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "video_id"
  range_key = "start"

  attribute {
    name = "video_id"
    type = "S"
  }
  attribute {
    name = "start"
    type = "N"
  }
}

# ================= IAM =================
# - Basic policies for lamba
# Assume role
data "aws_iam_policy_document" "lambda_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}
# Basic execution policy
data "aws_iam_policy_document" "lambda_basic_execution_policy_doc" {
  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = ["*"]
  }
}
resource "aws_iam_policy" "lambda_basic_execution_policy" {
  name   = "lambda_basic_execution_policy"
  policy = data.aws_iam_policy_document.lambda_basic_execution_policy_doc.json
}
# DB Access
data "aws_iam_policy_document" "lambda_dynamodb_access_policy_doc" {
  statement {
    actions = [
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:BatchGetItem",
      "dynamodb:BatchWriteItem",
    ]

    resources = [
      aws_dynamodb_table.channels_table.arn,
      "${aws_dynamodb_table.channels_table.arn}/*",
      aws_dynamodb_table.videos_table.arn,
      "${aws_dynamodb_table.videos_table.arn}/*",
      aws_dynamodb_table.transcripts_table.arn,
      "${aws_dynamodb_table.transcripts_table.arn}/*",
    ]
  }
}
resource "aws_iam_policy" "lambda_dynamodb_access_policy" {
  name   = "lambda_dynamodb_access_policy"
  policy = data.aws_iam_policy_document.lambda_dynamodb_access_policy_doc.json
}

# Transcript bucket access
data "aws_iam_policy_document" "lambda_s3transcripts_acccess_policy_doc" {
  statement {
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.original_transcripts.arn,
      "${aws_s3_bucket.original_transcripts.arn}/*",
    ]
  }
}
resource "aws_iam_policy" "lambda_s3transcripts_acccess_policy" {
  name   = "lambda_s3transcripts_acccess_policy"
  policy = data.aws_iam_policy_document.lambda_s3transcripts_acccess_policy_doc.json
}

# YT Data API Access
data "aws_iam_policy_document" "lambda_ytdata_access_policy_doc" {
  statement {
    actions = [
      "ssm:GetParameter",
    ]
    resources = [
      aws_ssm_parameter.google_token.arn,
    ]
  }
}
resource "aws_iam_policy" "lambda_ytdata_access_policy" {
  name   = "lambda_ytdata_access_policy"
  policy = data.aws_iam_policy_document.lambda_ytdata_access_policy_doc.json
}

# OpenAI API Access
data "aws_iam_policy_document" "lambda_openai_access_policy_doc" {
  statement {
    actions = [
      "ssm:GetParameter",
    ]
    resources = [
      aws_ssm_parameter.openai_api_key.arn,
    ]
  }
}
resource "aws_iam_policy" "lambda_openai_access_policy" {
  name   = "lambda_openai_access_policy"
  policy = data.aws_iam_policy_document.lambda_openai_access_policy_doc.json
}

# ================= Lambda =================
# - Transcript Processor
# Role
resource "aws_iam_role" "transcript_processor_role" {
  name               = "${var.PROJECT}-${var.ENV}-transcript-processor-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role_policy.json
  managed_policy_arns = [
    aws_iam_policy.lambda_basic_execution_policy.arn,
    aws_iam_policy.lambda_dynamodb_access_policy.arn,
    aws_iam_policy.lambda_s3transcripts_acccess_policy.arn,
    aws_iam_policy.lambda_openai_access_policy.arn,
  ]
}
resource "aws_ecr_repository" "transcript_processor_repo" {
  name                 = "${var.PROJECT}-${var.ENV}-transcript-processor"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}
data "aws_ecr_image" "transcript_processor_img" {
  repository_name = aws_ecr_repository.transcript_processor_repo.name
  image_tag       = "latest"
}
resource "aws_lambda_function" "transcript_processor" {
  function_name = "${var.PROJECT}-${var.ENV}-process-transcripts"
  role          = aws_iam_role.transcript_processor_role.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.transcript_processor_repo.repository_url}@${data.aws_ecr_image.transcript_processor_img.id}"
  timeout       = 900
  memory_size   = 512

  environment {
    variables = {
      CHANNELS_TABLE_NAME = aws_dynamodb_table.channels_table.name
      VIDEOS_TABLE_NAME = aws_dynamodb_table.videos_table.name
      TRANSCRIPTS_TABLE_NAME = aws_dynamodb_table.transcripts_table.name
      OPENAI_API_KEY_PARAMETER_NAME = "${var.PROJECT}-${var.ENV}-openai-api-key"
      NLTK_DATA = "/var/task/nltk_data"
    }
  }
}
# Allos S3 to invoke the lambda
resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromTranscriptsS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.transcript_processor.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.original_transcripts.arn
}

# S3 Event Trigger
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.original_transcripts.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.transcript_processor.arn
    events              = ["s3:ObjectCreated:*"]
  }
  depends_on = [aws_lambda_permission.allow_bucket]
}
variable "PROJECT" {
	type = string
	default = "yt-guesser"
}
variable "ENV" {
	type = string
	default = "dev"
}

terraform {
  backend "s3" {
    bucket = "terraform-45370"
    key    = "yt-guesser/state"
    region = "us-east-1"
  }
}

resource "aws_ssm_parameter" "google_token" {
  name  = "${var.PROJECT}-${var.ENV}-google-token"
  type  = "SecureString"
  value = "hi"
}

resource "aws_s3_bucket" "channel_list_bucket" {
  bucket = "${var.PROJECT}-${var.ENV}-channel-list"
}

resource "aws_s3_object" "channel_list" {
  bucket = aws_s3_bucket.channel_list_bucket.id
  key    = "channel-list"
  source = "channel-list.txt"

  # The filemd5() function is available in Terraform 0.11.12 and later
  # For Terraform 0.11.11 and earlier, use the md5() function and the file() function:
  # etag = "${md5(file("path/to/file"))}"
  etag = filemd5("channel-list.txt")
}

resource "aws_s3_bucket" "transcripts_bucket" {
  bucket = "${var.PROJECT}-${var.ENV}-transcripts"
}

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_dynamodb_table" "videos_table" {
  name           = "${var.PROJECT}-${var.ENV}-videos"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "channelId"
  range_key      = "videoId"

  attribute {
    name = "channel_id"
    type = "S"
  }

  attribute {
    name = "video_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "phrases_table" {
  name           = "${var.PROJECT}-${var.ENV}-phrases"
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

data "aws_iam_policy_document" "lambda" {
  statement {
    effect = "Allow"
    actions = [
      "ssm:GetParameter"
    ]
    resources = [
      aws_ssm_parameter.google_token.arn
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject"
    ]
    resources = [
      aws_s3_bucket.channel_list_bucket.arn,
      "${aws_s3_bucket.channel_list_bucket.arn}/*",
      aws_s3_bucket.transcripts_bucket.arn,
      "${aws_s3_bucket.transcripts_bucket.arn}/*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:GetItem"
    ]
    resources = [
      aws_dynamodb_table.videos_table.arn,
      aws_dynamodb_table.phrases_table.arn
    ]
  }
}


resource "aws_iam_role" "iam_for_lambda" {
  name               = "iam_for_lambda"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
  inline_policy {
    name = "lambda"
    policy = data.aws_iam_policy_document.lambda.json
  }
}

data "archive_file" "do_everything_package" {
  type        = "zip"
  source_dir = "build/do_everything"
  output_path = "build/do_everything.zip"
}

resource "aws_lambda_function" "do_everything" {
  # If the file is not in the current working directory you will need to include a
  # path.module in the filename.
  filename      = "build/do_everything.zip"
  function_name = "${var.PROJECT}-${var.ENV}-doeverything"
  role          = aws_iam_role.iam_for_lambda.arn
  handler       = "main.hander"
  source_code_hash = data.archive_file.do_everything_package.output_base64sha256
  runtime = "python3.9"
  memory_size = 2048
  timeout = 300
  environment {
    variables = {
      TOKEN_PARAMENTER_NAME = aws_ssm_parameter.google_token.name
      CHANNEL_LIST_BUCKET = aws_s3_bucket.channel_list_bucket.id
      CHANNEL_LIST_KEY = aws_s3_object.channel_list.key
      TRANSCRIPTS_BUCKET = aws_s3_bucket.transcripts_bucket.id
      VIDEOS_TABLE_NAME = aws_dynamodb_table.videos_table.name
      PHRASES_TABBLE_NAME = aws_dynamodb_table.phrases_table.name
    }
  }
}
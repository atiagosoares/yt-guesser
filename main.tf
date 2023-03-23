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
  value = file("token.json") 
}

resource "aws_s3_bucket" "channel_list_bucket" {
  bucket = "${var.PROJECT}-${var.ENV}-channel-list"
}

resource "aws_s3_bucket" "original_transcripts" {
  bucket = "${var.PROJECT}-${var.ENV}-transcripts"
}

# Database
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
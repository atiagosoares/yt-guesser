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

resource "aws_iam_role" "iam_for_lambda" {
  name               = "iam_for_lambda"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

data "archive_file" "do_everything_package" {
  type        = "zip"
  source_file = "src/do_everything/main.py"
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
}

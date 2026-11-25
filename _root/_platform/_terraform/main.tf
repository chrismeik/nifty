# The lane's bucket holds both _s3_copy data and this folder's Terraform state.
#
# The bucket has to exist before Terraform can keep state in it, so each bucket is
# created once by hand and adopted here through the import blocks below. Import
# blocks are no-ops once the resource is in state, so they can stay.

import {
  to = aws_s3_bucket.this
  id = var.bucket_name
}

import {
  to = aws_s3_bucket_versioning.this
  id = var.bucket_name
}

import {
  to = aws_s3_bucket_public_access_block.this
  id = var.bucket_name
}

import {
  to = aws_s3_bucket_server_side_encryption_configuration.this
  id = var.bucket_name
}

import {
  to = aws_s3_bucket_ownership_controls.this
  id = var.bucket_name
}

resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name

  # Holds this configuration's own state: Terraform must never delete it.
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket = aws_s3_bucket.this.id

  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_ownership_controls" "this" {
  bucket = aws_s3_bucket.this.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

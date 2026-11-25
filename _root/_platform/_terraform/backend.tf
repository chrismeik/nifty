# State lives in the lane's own bucket, mirroring this folder's path in the project tree:
#   s3://<S3_COPY_BUCKET>/[S3_COPY_PREFIX/]_root/_platform/_terraform/terraform.tfstate
#
# Backend blocks can't use variables, so bucket, key and region are passed at init
# time by tf.sh (-backend-config=...).
terraform {
  backend "s3" {
    use_lockfile = true # S3-native locking, no DynamoDB table
    encrypt      = true
  }
}

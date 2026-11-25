# _terraform

AWS infrastructure for one project + lane. Today that is the lane's S3 bucket.

- One bucket per project and lane: `veratree-<project>-<environment>`, set by hand as
  `S3_COPY_BUCKET`. `S3_COPY_PREFIX` is an optional leading prefix (empty by default).
- The bucket holds both `_s3_copy` data and this folder's state. State mirrors this
  folder's place in the project tree:
  `s3://<bucket>/[prefix/]_root/_platform/_terraform/terraform.tfstate`
- Buckets are created once by hand (state has to live somewhere first), then adopted by
  the `import` blocks in `main.tf`. `prevent_destroy` stops Terraform deleting them.

## Running it

```bash
bash _root/_platform/_terraform/tf.sh plan
bash _root/_platform/_terraform/tf.sh apply
```

`tf.sh` reads `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_COPY_BUCKET`,
`S3_COPY_PREFIX`, `AWS_REGION` and `ENVIRONMENT` (default `sandbox`) from the environment, falling back to `_root/_platform/_compose/.env`.
It uses a local `terraform` if installed, otherwise the `hashicorp/terraform` image.

Sandbox runs it by hand when infrastructure changes. Deployed lanes will run it from
GitHub Actions before deploying.

# Day 7: deploy ONE real slice to AWS (keep it small + cheap).
# Recommended first slice: containerized API on ECS Fargate behind an ALB,
# OR the classifier as a Lambda (container image) for the serverless signal.
#
# TODO(you):
#   - aws_ecr_repository  (push the API image)
#   - aws_ecs_cluster / task_definition / service  (Fargate)  OR aws_lambda_function
#   - aws_cloudwatch_log_group  (observability)
#   - outputs: service URL
# Keep state local for the portfolio; mention S3+DynamoDB backend as the prod path.

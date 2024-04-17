from prefect import flow


@flow(log_prints=True)
def lambda_handler(event, context):
    """AWS Lambda function entrypoint"""
    print(f"{event=}, {context=}")

    return {"message": "Hello, World!"}

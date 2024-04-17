FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip install uv
RUN uv venv
RUN uv pip install -r requirements.txt

COPY .prefect/ ${LAMBDA_TASK_ROOT}/.prefect/
COPY plugin.py ${LAMBDA_TASK_ROOT}

CMD [ "plugin.lambda_handler" ]
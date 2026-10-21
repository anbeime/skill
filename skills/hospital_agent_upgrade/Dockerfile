# do not modify.
FROM modelscope-registry.cn-beijing.cr.aliyuncs.com/modelscope-repo/python:3.9

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY --chown=user . /app

CMD ["python3", "-m", "agent.agent"]

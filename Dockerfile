FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .
USER 65532:65532
ENTRYPOINT ["spot-readiness-guard"]

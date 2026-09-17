FROM python:3.11-slim
WORKDIR /srv

COPY packages/shared /srv/packages/shared
RUN pip install --no-cache-dir -e /srv/packages/shared

COPY services/conflict-resolution/requirements.txt /srv/services/conflict-resolution/requirements.txt
RUN pip install --no-cache-dir -r /srv/services/conflict-resolution/requirements.txt

COPY services/conflict-resolution/app /srv/services/conflict-resolution/app
WORKDIR /srv/services/conflict-resolution

EXPOSE 4103
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "4103"]

FROM python:3.11-slim
WORKDIR /srv

COPY packages/shared /srv/packages/shared
RUN pip install --no-cache-dir -e /srv/packages/shared

COPY services/signal-command/requirements.txt /srv/services/signal-command/requirements.txt
RUN pip install --no-cache-dir -r /srv/services/signal-command/requirements.txt

COPY services/signal-command/app /srv/services/signal-command/app
WORKDIR /srv/services/signal-command

EXPOSE 4104
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "4104"]

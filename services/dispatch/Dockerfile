FROM python:3.11-slim
WORKDIR /srv

COPY packages/shared /srv/packages/shared
RUN pip install --no-cache-dir -e /srv/packages/shared

COPY services/dispatch/requirements.txt /srv/services/dispatch/requirements.txt
RUN pip install --no-cache-dir -r /srv/services/dispatch/requirements.txt

COPY services/dispatch/app /srv/services/dispatch/app
WORKDIR /srv/services/dispatch

EXPOSE 4101
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "4101"]

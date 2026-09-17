FROM python:3.11-slim
WORKDIR /srv

COPY packages/shared /srv/packages/shared
RUN pip install --no-cache-dir -e /srv/packages/shared

COPY services/notifications/requirements.txt /srv/services/notifications/requirements.txt
RUN pip install --no-cache-dir -r /srv/services/notifications/requirements.txt

COPY services/notifications/app /srv/services/notifications/app
WORKDIR /srv/services/notifications

EXPOSE 4105
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "4105"]

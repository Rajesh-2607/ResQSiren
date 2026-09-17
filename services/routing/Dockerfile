FROM python:3.11-slim
WORKDIR /srv

COPY packages/shared /srv/packages/shared
RUN pip install --no-cache-dir -e /srv/packages/shared

COPY services/routing/requirements.txt /srv/services/routing/requirements.txt
RUN pip install --no-cache-dir -r /srv/services/routing/requirements.txt

COPY services/routing/app /srv/services/routing/app
WORKDIR /srv/services/routing

EXPOSE 4102
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "4102"]

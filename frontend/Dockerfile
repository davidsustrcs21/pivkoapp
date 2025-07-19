FROM nginx:alpine

COPY static/ /usr/share/nginx/html/static/
COPY templates/ /usr/share/nginx/html/templates/

# This is just for serving static files
# Templates are served by FastAPI
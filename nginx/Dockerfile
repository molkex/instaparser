FROM nginx:1.17-alpine
RUN rm /etc/nginx/conf.d/default.conf
# COPY nginx.conf /etc/nginx/conf.d/flaskapp.conf
COPY proxy_params /etc/nginx/proxy_params

FROM nginx:1.25-alpine

# Xóa config mặc định của nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copy config của chúng ta vào
COPY nginx.conf /etc/nginx/nginx.conf

# Tạo thư mục cho SSL cert và certbot webroot
RUN mkdir -p /etc/nginx/ssl \
    && mkdir -p /var/www/certbot

EXPOSE 80 443
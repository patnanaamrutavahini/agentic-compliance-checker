FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
ARG VITE_API_URL=
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 5173

# Replace default nginx config
RUN sed -i 's/listen       80;/listen       5173;/g' /etc/nginx/conf.d/default.conf
RUN sed -i 's/try_files $uri $uri\/ \/index.html;/try_files $uri $uri\/ \/index.html;/g' /etc/nginx/conf.d/default.conf

CMD ["nginx", "-g", "daemon off;"]

FROM node:22-alpine AS build

WORKDIR /app

# Vite inlines VITE_-prefixed env vars into the bundle at build time, so
# they need to be passed in as build args rather than runtime env vars.
ARG VITE_API_BASE_URL=http://localhost:8000/api/v1
ARG VITE_FOOD_FACTS_API_BASE_URL=https://world.openfoodfacts.net/api/v3.6
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_FOOD_FACTS_API_BASE_URL=$VITE_FOOD_FACTS_API_BASE_URL

COPY package*.json ./
RUN npm ci --silent

COPY . .
RUN npm run build


FROM nginx:1.27-alpine


COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD [ "nginx", "-g", "daemon off;" ]
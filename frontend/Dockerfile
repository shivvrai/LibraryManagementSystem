FROM node:18-alpine AS build

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the Vite application
RUN npm run build

# Use Nginx to serve the built static files
FROM nginx:alpine

# Copy built assets from the previous stage to nginx's serve directory
COPY --from=build /app/dist /usr/share/nginx/html

# The docker-compose maps port 5173 on the host to port 80 in the container
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

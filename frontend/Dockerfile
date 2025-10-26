FROM node:20-alpine

WORKDIR /app

# Copy package files and install
COPY package.json package-lock.json* ./
RUN npm install

# Copy frontend code
COPY . .

# Expose port
EXPOSE 3000

# Run frontend
CMD ["npm", "start"]

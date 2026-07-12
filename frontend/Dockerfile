# 1. Base image
FROM node:20-alpine

# 2. Set working directory
WORKDIR /app

# 3. Copy package files directly (since context is already ./frontend)
COPY package.json ./

# 4. Install dependencies
RUN npm install

# 5. Copy the rest of the application code
COPY . .

# 6. Build the Next.js production bundle

# 7. Start command
CMD ["npm", "run", "start"]
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN chown -R node:node /app
USER node
EXPOSE 4321
CMD ["sh", "-c", "npm run build && npx vite preview --host --port 4321"]

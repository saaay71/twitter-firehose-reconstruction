FROM node:16.13.2-alpine
COPY client /app/client

WORKDIR /app/client
RUN npm install
RUN npm run build

COPY server /app/server

WORKDIR /app/server
RUN npm install
CMD ["npm", "run", "start-production"]
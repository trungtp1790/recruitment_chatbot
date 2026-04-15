FROM node:20-alpine

WORKDIR /app

COPY frontend/package.json ./package.json
COPY frontend/tsconfig.json ./tsconfig.json
COPY frontend/next.config.js ./next.config.js
COPY frontend/next-env.d.ts ./next-env.d.ts
COPY frontend/app ./app

RUN npm install

EXPOSE 3000

CMD ["npm", "run", "dev"]

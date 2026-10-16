# Development image for docker-compose (frontend is deployed to Vercel, which
# builds the app natively, so there is no production image here).

FROM node:24-slim

RUN npm install --global pnpm@9

WORKDIR /app

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .

EXPOSE 3000

CMD ["pnpm", "dev"]

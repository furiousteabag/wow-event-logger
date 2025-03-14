FROM oven/bun:latest

WORKDIR /app

COPY package.json bun.lock ./

RUN bun install --frozen-lockfile

COPY . .

RUN bun run lint

RUN bun run build

EXPOSE 8000

CMD ["bun", "run", "start"]

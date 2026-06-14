# @orchestrator: Magnús Smárason | smarason.is  @created: 2026-06-12
FROM node:22-alpine
WORKDIR /app
COPY server.mjs data.json ./
COPY public ./public
EXPOSE 4250
USER node
CMD ["node", "server.mjs"]

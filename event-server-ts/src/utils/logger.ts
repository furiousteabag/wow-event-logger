import dayjs from "dayjs"
import { Logger, createLogger, format, transports } from "winston"

function getLevelColor(level: string) {
  switch (level) {
    case "error":
      return "\x1b[1;31m" // bold red
    case "warn":
      return "\x1b[1;33m" // bold yellow
    case "info":
      return "\x1b[1;37m" // bold white
    case "debug":
      return "\x1b[1;34m" // bold blue
    case "silly":
      return "\x1b[1;36m" // bold cyan (like 'trace')
    default:
      return "\x1b[1;37m" // bold white fallback
  }
}

const logFormat = format.printf((info) => {
  const timestamp = `\x1b[32m${dayjs().format("YYYY-MM-DD HH:mm:ss.SSS")}\x1b[0m` // green
  const levelColor = getLevelColor(info.level)
  const levelStr = info.level.toUpperCase().padEnd(5)
  const level = `${levelColor}${levelStr}\x1b[0m`
  // const fileLine = `\x1b[36m${getFileLine()}\x1b[0m`;
  const message = `${levelColor}${info.message}\x1b[0m`
  return `${timestamp} | ${level} | ${message}`
})

const logger: Logger = createLogger({
  level: "info",
  format: format.combine(logFormat),
  transports: [new transports.Console()],
})

export default logger

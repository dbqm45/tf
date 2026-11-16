import { logger } from "./logger";

export function signup(user: { id: string; email: string }) {
  logger.info("new signup, confirmation email sent");
  logger.info(`new signup ${user.id}`);
  return user.id;
}

export function login(user: { id: string; email: string }) {
  logger.info(`login ${maskEmail(user.email)}`);
}

function maskEmail(e: string): string {
  return e.replace(/^(.).*@/, "$1***@");
}

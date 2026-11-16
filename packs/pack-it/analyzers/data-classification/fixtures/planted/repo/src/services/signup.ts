import { logger } from "./logger";

export function signup(user: { id: string; email: string }) {
  logger.info(`new signup ${user.email}`);
  return user.id;
}

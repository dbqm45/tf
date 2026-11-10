import { logger } from "../logger";

export function sync(push: () => Promise<void>) {
  push().catch((err) => logger.warn({ err }, "sync failed, will retry"));
}

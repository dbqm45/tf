import { Router } from "express";
import { readFileSync } from "node:fs";
import { logger } from "../logger";

export const orders = Router();
orders.post("/", (req, res) => {
  try {
    logger.info({ orderId: req.body.id }, "new order");
  } catch (e) {
    logger.error({ err: e }, "order failed");
    throw e;
  }
  let config = "";
  try {
    config = readFileSync("orders.json", "utf-8");
  } catch {
    /* brak pliku konfiguracji to stan normalny — wartości domyślne */
  }
  res.status(201).send(config);
});

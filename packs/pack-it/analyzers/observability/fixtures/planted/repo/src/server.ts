import express from "express";
import winston from "winston";
import { orders } from "./routes/orders";

export const logger = winston.createLogger({ transports: [new winston.transports.Console()] });
const app = express();
app.use("/orders", orders);
app.listen(3000, () => logger.info("listening"));

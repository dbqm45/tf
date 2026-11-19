import express from "express";
import pinoHttp from "pino-http";
import { randomUUID } from "node:crypto";
import { orders } from "./routes/orders";

const app = express();
app.use(pinoHttp({ genReqId: (req) => req.headers["x-request-id"] ?? randomUUID() }));
app.get("/healthz", (_req, res) => res.send("ok"));
app.use("/orders", orders);
app.listen(3000);

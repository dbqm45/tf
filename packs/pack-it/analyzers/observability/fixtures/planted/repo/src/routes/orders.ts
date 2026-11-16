import { Router } from "express";

export const orders = Router();
orders.post("/", (req, res) => {
  console.log("new order", req.body.id);
  res.status(201).end();
});

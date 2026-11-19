const router = require("express").Router();
router.get("/orders", listOrders);
router.delete("/orders/:id", async (req, res) => { await Orders.remove(req.params.id); res.sendStatus(204); });
module.exports = router;

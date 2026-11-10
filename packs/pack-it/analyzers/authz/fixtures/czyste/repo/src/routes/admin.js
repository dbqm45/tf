const router = require("express").Router();
router.use(requireRole("admin"));
router.post("/users/:id/ban", banUser);
module.exports = router;

package shop;

@RestController
@RequestMapping("/orders")
public class OrderController {
    @GetMapping
    public List<Order> list() { return service.list(); }

    @PatchMapping("/{id}")
    public Order patch(@PathVariable long id, @RequestBody OrderPatch p) { return service.patch(id, p); }
}

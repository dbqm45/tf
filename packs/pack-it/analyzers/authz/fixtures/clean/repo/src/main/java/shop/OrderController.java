package shop;

@RestController
@RequestMapping("/orders")
public class OrderController {
    @PatchMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public Order patch(@PathVariable long id, @RequestBody OrderPatch p) { return service.patch(id, p); }
}

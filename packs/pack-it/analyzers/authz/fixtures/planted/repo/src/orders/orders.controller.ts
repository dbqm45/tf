import { Controller, Get, Post, Body } from "@nestjs/common";

@Controller("orders")
export class OrdersController {
  @Get()
  list() { return this.svc.list(); }

  @Post()
  create(@Body() dto: CreateOrderDto) { return this.svc.create(dto); }
}

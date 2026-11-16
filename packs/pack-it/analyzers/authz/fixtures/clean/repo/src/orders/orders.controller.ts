import { Controller, Post, Body, UseGuards } from "@nestjs/common";

@Controller("orders")
export class OrdersController {
  @Post()
  @UseGuards(AuthGuard("jwt"), RolesGuard)
  create(@Body() dto: CreateOrderDto) { return this.svc.create(dto); }
}

import { Controller, Delete, Param, UseGuards } from "@nestjs/common";

@UseGuards(AdminGuard)
@Controller("admin")
export class AdminController {
  @Delete(":id")
  remove(@Param("id") id: string) { return this.svc.remove(id); }
}

import { analytics } from "./analytics";
import { hashId } from "./hash";

export function onSignup(user: { id: string; email: string }) {
  analytics.track("signup", { userId: hashId(user.id), method: "email" });
}

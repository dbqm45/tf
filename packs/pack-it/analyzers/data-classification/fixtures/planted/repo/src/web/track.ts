import { analytics } from "./analytics";

export function onSignup(user: { id: string; email: string }) {
  analytics.track("signup", { email: user.email });
}

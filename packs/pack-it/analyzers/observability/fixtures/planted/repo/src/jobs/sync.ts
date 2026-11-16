export function sync(push: () => Promise<void>) {
  push().catch(() => {});
}

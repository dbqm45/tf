/* eslint-disable */
export async function load(url: string) {
  // FIXME this is slow for large carts
  // @ts-ignore
  return fetch(url).then((r) => r.jsn());
}

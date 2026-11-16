/* eslint-disable no-console -- narzędzie CLI pisze na konsolę */
export async function load(url: string) {
  // FIXME PAY-42 slow for large carts
  // HACK: see https://github.com/acme/shop/issues/7
  // @ts-expect-error biblioteka ma błędny typ odpowiedzi
  return fetch(url).then((r) => r.jsn());
}
// eslint-disable-next-line no-console -- debug
console.log("ready");
const todoItems: string[] = [];

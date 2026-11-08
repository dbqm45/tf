export function show(el: HTMLElement, text: string) {
  el.textContent = text;
  const m = /a(b)/.exec(text);
  return m;
}

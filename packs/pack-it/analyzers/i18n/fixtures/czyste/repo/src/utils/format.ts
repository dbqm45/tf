export const formatCount = (n: number, locale: string) => new Intl.NumberFormat(locale).format(n);
export const price = (n: number) => `${n.toFixed(2)}`;

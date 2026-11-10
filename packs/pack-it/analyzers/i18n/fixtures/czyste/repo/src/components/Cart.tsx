import { useState } from "react";
import { useTranslation } from "react-i18next";

export function Cart({ total, items, date, locale }: { total: number; items: string[]; date: Date; locale: string }) {
  const { t } = useTranslation();
  const [code, setCode] = useState<string>("");
  const money = new Intl.NumberFormat(locale, { style: "currency", currency: "PLN" });
  const list = items.map((i) => <li key={i}>{i}</li>);
  return (
    <section>
      <h2>{t("cart.title")}</h2>
      <input placeholder={t("cart.code")} value={code} onChange={(e) => setCode(e.target.value)} />
      <p>{money.format(total)}</p>
      <p>{date.toLocaleDateString(locale)}</p>
      <ul>{items.length > 0 ? list : null}</ul>
      <span>{items.length}</span>
      <span>—</span>
      <td>42</td>
    </section>
  );
}

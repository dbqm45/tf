# OCPP 2.1 — rozszerzenia i poziom pewności

## 1. Fakty i pewność
| Fakt | Poziom | Źródło |
|---|---|---|
| Wydanie przez OCA: styczeń 2025 | wtórne — [do weryfikacji] | snippety openchargealliance.org, `fakty-1a.md` 2026-10-20 |
| IEC 63584-210:2025, publikacja 2025-12-09 | wtórne — [do weryfikacji] | j.w. |
| 2.0.1 Edition 4, 2.1 Edition 2 (grudzień 2025) | niepotwierdzone — [do weryfikacji] | j.w. |
Strona OCA była niedostępna przy sprawdzaniu.

## 2. Zakres (wg importu)
Rozszerza 2.0.1: ISO 15118-20 i V2X (dwukierunkowość), lokalne zarządzanie energią (DER), płatności lokalne
(ad-hoc). Nowe typy ramek (m.in. `SEND`, `CALLRESULTERROR`) — [do weryfikacji] przed implementacją.
Nazw nowych komunikatów 2.1 nie podaję: [do weryfikacji].

## 3. Zalecenia
- Traktuj 2.1 jako osobną wersję w rejestrze urządzeń (wersja + edycja), z własnym adapterem lub rozszerzeniem
  adaptera 2.0.1 po sprawdzeniu zgodności.
- Wymaganie klienta „OCPP 2.1” rozbij na funkcje (V2X, DER, płatności) i sprawdź, które stacja faktycznie
  certyfikuje; ogólny numer wersji nic nie gwarantuje.

# Poczta wysyłana przez aplikację: dostarczalność i uwierzytelnienie domeny

Aplikacja wysyła e-maile (rejestracja, reset hasła, faktury, powiadomienia) przez dostawcę (SES, SendGrid, Postmark,
Mailgun lub firmowy serwer SMTP). Bez poprawnej konfiguracji domeny wiadomości trafiają do spamu albo są odrzucane.

## Trzy rekordy DNS
- **SPF**: jeden rekord na domenę, najwyżej 10 zapytań DNS (każde `include` się liczy).
- **DKIM**: klucze co najmniej 2048-bitowe, rotacja przez nowy selektor.
- **DMARC**: z wyrównaniem do domeny `From`; zacznij od `p=none` z raportami `rua=`, potem `p=quarantine` i `p=reject`.
- Poczta systemowa z osobnej subdomeny (`mail.firma.pl`, `powiadomienia.firma.pl`) — reputacja marketingu nie psuje
  dostarczania resetów hasła.

## Wymagania dużych skrzynek (Gmail, Yahoo)
- Wszyscy nadawcy: SPF lub DKIM, poprawny rekord odwrotny DNS (PTR) serwera, TLS przy wysyłaniu, poprawny format
  wiadomości, niski odsetek zgłoszeń spamu.
- **Nadawcy masowi** (Gmail: od 5000 wiadomości dziennie do kont Gmail — status pozostaje także po spadku wolumenu):
  SPF **i** DKIM, DMARC co najmniej `p=none` z wyrównaniem, **rezygnacja jednym kliknięciem** w wiadomościach
  marketingowych (nagłówki `List-Unsubscribe` i `List-Unsubscribe-Post` według RFC 8058) obsłużona w ciągu 2 dni,
  odsetek zgłoszeń spamu poniżej 0,1% i nigdy powyżej 0,3%. Od listopada 2025 Gmail egzekwuje te zasady stopniowo:
  tymczasowe odrzucenia, potem odrzucenia trwałe.
- Stan sprawdzasz w Google Postmaster Tools; zasady zmieniają się — przed dużą wysyłką przeczytaj aktualne wytyczne.

## Po stronie aplikacji
- Wysyłka asynchroniczna z kolejki (ponowienia, limit szybkości dostawcy), idempotentna przy ponowieniu (be-messaging-outbox).
- Obsługa odbić i skarg (webhook dostawcy): adresy trwale odrzucane i skarżące się — wyłączone z dalszej wysyłki.
- Treść: tekst i HTML, linki na własnej domenie, bez skracaczy; zgoda na marketing (RODO) osobno od wiadomości
  transakcyjnych.
- Testy bez wysyłki do prawdziwych ludzi: przechwytujący serwer SMTP (Mailpit — qa-regression,
  `dane-srodowiska-i-specjalne.md`).

## Protokoły i porty
SMTP: 25 (między serwerami), 587 (wysyłka z uwierzytelnieniem i STARTTLS — domyślny dla aplikacji), 465 (SMTP przez
TLS). Odbiór: IMAP 993 (IMAPS), POP3 995 (POP3S). Wielu dostawców chmury blokuje wychodzący port 25 — aplikacja
wysyła przez API lub port 587 dostawcy. Greylisting (tymczasowe odrzucenie pierwszej wiadomości od nieznanego
nadawcy) wymaga od serwera wysyłającego ponowienia — dostawcy robią to sami.

## Źródła
- RFC 7208 (SPF), RFC 6376 (DKIM), RFC 7489 (DMARC), RFC 8058 (one-click unsubscribe)
- [Google — Email sender guidelines](https://support.google.com/a/answer/81126);
  [Red Sift — Gmail enforcement for bulk senders](https://redsift.com/blog/gmails-enforcement-ramps-up-what-bulk-senders-need-to-know)
- [roadmap.sh — DevOps](https://roadmap.sh/devops) (SMTP, IMAP, POP3S, SPF, DomainKeys, DMARC, white/grey listing)
Opisane własnymi słowami.

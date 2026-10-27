# Plan: utwardzanie hosta oraz szyfrowanie w spoczynku i klasyfikacja danych (luki bezpieczeństwa 1–2)

Data: 2026-10-27 · Status: zrobione (kroki 1–4), commit i PR na prośbę człowieka · Gałąź: `claude/great-hypatia-angvam`
Źródło: przegląd warstw obrony 2026-10-27 (`docs/todo.md`, sekcja „Bezpieczeństwo — luki…”, pozycje 1–2). Źródła
pierwotne NIST i OWASP: statusy wg wyszukiwania w domenach nist.gov i owasp.org 2026-10-27; strony csrc.nist.gov
i owasp.org niedostępne z sandboxu — szczegóły jako [niezweryfikowane] w sekcjach „Źródła”.

## TL;DR
Dwie luki w pack-it, obie jako nowe pliki `references/` z krótkim odesłaniem w SKILL.md (SKILL.md nie rośnie
o całą treść):
1. `ops-security-operations/references/utwardzanie-hosta.md` — utwardzanie systemu serwera (Linux, krótko Windows):
   procedura od linii bazowej (CIS Benchmark, poziom 1) przez usługi, SSH, konta, zaporę hosta, audyt, łatki
   automatyczne, po sprawdzenie skanerem i dryf konfiguracji. Sekcja 5 SKILL.md dostaje punkt „Utwardzanie”.
2. `sec-cryptography-pki/references/dane-w-spoczynku.md` — klasyfikacja danych (klasy → wymagane zabezpieczenia),
   warstwy szyfrowania w spoczynku (dysk/wolumen, baza, pole, kopie) i przed czym każda chroni, klucze (KMS,
   kopertowe), cykl życia danych i bezpieczne usuwanie (NIST SP 800-88, crypto-erase). Procedura SKILL.md pkt 1
   odsyła do pliku.

## Decyzje
- **Miejsce:** utwardzanie w `ops-security-operations` (łatki i inwentarz już tam są; ops-linux-performance dotyczy
  wydajności, dostaje tylko odesłanie w jednym zdaniu). Dane w spoczynku w `sec-cryptography-pki` (KMS i szyfrowanie
  kopertowe już tam są); `arch-privacy-compliance` dostaje odesłanie (retencja danych osobowych zostaje u niego).
- **Granice:** kontenery — `ops-docker`; konto chmury i CSPM — `sec-cloud-security`; sekrety — `ops-secrets-identities`.
  Nowe pliki odsyłają, nie powtarzają.
- **Bez narzędzi tylko jednego dostawcy:** przykłady narzędzi (OpenSCAP, Lynis, auditd, unattended-upgrades/dnf-automatic)
  jako przykłady, nie wymóg.

## Kolejność
1. Scenariusze ewaluacji (przed treścią): `ops-security-operations` → `utwardzanie-serwera-linux`;
   `sec-cryptography-pki` → `szyfrowanie-w-spoczynku-klasy-danych`.
2. Treść: dwa pliki references, odesłania w SKILL.md (ops-security-operations §5 i opis/`slowa`, sec-cryptography-pki
   procedura pkt 1 i `slowa`), odesłanie w ops-linux-performance i arch-privacy-compliance.
3. Źródła z datą (wynik researchera); czego nie potwierdzi — [niezweryfikowane].
4. Bramki: `skill_gate.py` dla zmienionych skilli w workspace pack-it, `sync-gate`; `workspace.py check --packs pack-it`
   i `all`; `refs`; todo (pozycje 1–2 odhaczone).

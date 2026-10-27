# Plan: mapa warstw obrony, ramy DevSecOps (SSDF, DSOMM), centralne logi bezpieczeństwa (luki 3–5)

Data: 2026-10-27 · Status: zrobione (kroki 1–3), commit i PR na prośbę człowieka · Gałąź: `claude/great-hypatia-angvam`
Źródło: `docs/todo.md`, sekcja „Bezpieczeństwo — luki…”, pozycje 3–5. Statusy dokumentów NIST/OWASP wg wyszukiwania
w domenach nist.gov i owasp.org 2026-10-27 (strony csrc.nist.gov i owasp.org niedostępne z sandboxu).

## TL;DR
1. `arch-threat-modeling/references/warstwy-obrony.md` — mapa defence in depth: warstwa (sieć, tożsamość, host,
   aplikacja, dane, monitorowanie, reagowanie, łańcuch dostaw) → kontrole → skill fabryki → pytanie przeglądowe.
   Procedura pkt 7 (weryfikacja) odsyła: każda warstwa ma co najmniej jedną kontrolę albo zapisaną decyzję.
2. `sec-appsec-devsecops/references/standardy-i-metryki.md` — sekcje NIST SSDF (SP 800-218 v1.1, cztery grupy
   praktyk PO/PS/PW/RV i jak je mapować na pipeline; v1.2 to projekt) i OWASP DSOMM (miara dojrzałości pipeline'u,
   obok SAMM dla programu); SKILL.md: „shift left” i bezpieczne ustawienia domyślne nazwane wprost w celu skilla
   i procedurze pkt 2.
3. `ops-security-operations` §1 — plan zarządzania logami bezpieczeństwa wg NIST SP 800-92: inwentarz źródeł
   z właścicielem, format i znacznik czasu, transport i odporność na utratę, integralność i oddzielone uprawnienia
   (kto pisze ≠ kto kasuje), retencja per źródło, monitorowanie braku logów.

## Kolejność
1. Scenariusze ewaluacji (przed treścią): arch-threat-modeling `warstwy-obrony-przeglad`, sec-appsec-devsecops
   `ssdf-dsomm-ramy`, ops-security-operations `centralne-logi-bezpieczenstwa`.
2. Treść jak wyżej; `slowa` w opisach skilli.
3. Bramki: `skill_gate.py` trzech skilli w workspace pack-it, `sync-gate`; `workspace.py check --packs pack-it`
   i `all`; `refs`; todo (pozycje 3–5 odhaczone).

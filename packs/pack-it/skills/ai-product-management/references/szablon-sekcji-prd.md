# Szablon sekcji PRD dla funkcji AI

Wklej do `docs/project/03-requirements/requirements.md` albo `ai-feature-brief.md`. Puste pole = otwarte pytanie z adresatem.

```
## Funkcja AI: <nazwa>
Wynik i miara: <wynik, wartość wyjściowa → cel, termin sprawdzenia>
Użytkownik i zadanie: <rola, sytuacja, co robi dziś i ile to kosztuje>
Dlaczego AI: <reguła/ML/LLM — uzasadnienie>; alternatywa bez AI: <co>
Koszt błędów: <typ błędu → skutek → kto ponosi → limit>
Tryb autonomii: <sugestia | zatwierdzenie | cofalne | automat>, fallback: <opis>
Kryteria akceptacji (ewaluacje): zbiór <źródło, N, właściciel>; poprzeczki <metryka ≥ x>; przykłady dobre/złe/graniczne <odnośnik>
Cele: jakość <..>, opóźnienie p50/p95 <..>, koszt na udane zadanie <..> (data cennika), co ustępuje <..>
Dane: <potrzebne, mamy?, właściciel, podstawa użycia>
Podejście: <gotowy | API | dostrojenie | własny> (decyzja techniczna: arch-ai-solutions)
Ryzyka: <odnośnik do rejestru>, klasa regulacyjna: <od ai-governance-compliance>
UX niepewności: <oczekiwania, pewność/źródła, korekta, zbieranie sygnałów>
Wdrożenie: offline <próg> → dogfooding <próg> → beta <grupa, kill switch> → A/B <metryka, próg>
Metryki: produktowe <..>; modelowe <..>; ochronne <..>
Monitoring: <próbki, alerty, rytm przeglądu, właściciel>
Komunikat dla interesariuszy: potrafi <..> / nie potrafi <..> / nie wiemy jeszcze <..>
Otwarte pytania: <pytanie → adresat>
```

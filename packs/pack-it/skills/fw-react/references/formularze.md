# Formularze w React: schemat wspólny z serwerem, błędy, dostępność, kreatory

API sprawdzone w paczkach 2026-11-10: `react-hook-form` 7.91.0 (React 16.8–19), `@hookform/resolvers` 7.0.5
(`zodResolver` przyjmuje schematy Zod 3 i Zod 4, `standardSchemaResolver` — Standard Schema), `zod` 4.6.7.
Wersje w projekcie sprawdzasz w `package.json` (core-grounding).

## 1. Natywny formularz czy biblioteka
- **Natywnie** (`<form action={fn}>`, `useActionState`, `useFormStatus` — zasada 6 w SKILL.md): kilka pól,
  walidacja przy wysyłce, wynik z serwera. Bez biblioteki, działa też bez JavaScriptu przy Server Actions.
- **React Hook Form**: wiele pól z walidacją w trakcie wpisywania, pola zależne od innych, listy pól dodawanych
  przez użytkownika, kreator w kilku krokach, kontrolki z bibliotek (wybór daty, wyszukiwarka). Pola są
  niekontrolowane (`register`), więc formularz nie renderuje się przy każdym znaku.

## 2. Jeden schemat dla klienta i serwera
```ts
// shared/company-schema.ts — import i w przeglądarce, i na serwerze
import { z } from "zod";
export const companySchema = z.object({
  name: z.string().trim().min(2, "Podaj nazwę firmy"),
  nip: z.string().regex(/^\d{10}$/, "NIP to 10 cyfr"),
  contacts: z.array(z.object({ email: z.email("Niepoprawny e-mail") })).min(1, "Dodaj osobę kontaktową"),
});
export type CompanyInput = z.input<typeof companySchema>;
```
- Klient: `useForm<CompanyInput>({ resolver: zodResolver(companySchema), mode: "onTouched" })`.
- Serwer: `companySchema.safeParse(body)`. **Serwer waliduje zawsze**, bo walidacja w przeglądarce to wygoda,
  a nie zabezpieczenie. Reguły, które wymagają bazy (NIP zajęty, limit), są tylko na serwerze.
- Reguły domenowe (np. „NIP z poprawną sumą kontrolną”) piszesz jako czyste funkcje w `domain/` i używasz ich
  w schemacie (`.refine`), a nie kopiujesz do komponentu.
- Schemat z przekształceniami (`.transform`, `z.coerce`) ma inny typ wejścia i wyjścia: formularz pracuje na
  `z.input`, a serwer i domena na `z.output`.

## 3. Błędy pól i błędy z serwera
- Błędy pól są w `formState.errors.<pole>.message`. Komunikat mówi, co poprawić („NIP to 10 cyfr”), a nie „pole
  niepoprawne”.
- Odpowiedź 422 z błędami pól (Problem Details z listą `errors`, be-api-design, pack-it) mapujesz na pola:
  ```ts
  for (const e of problem.errors ?? []) setError(e.field as FieldPath<CompanyInput>, { type: "server", message: e.message });
  if (!problem.errors?.length) setError("root.serverError", { type: "server", message: problem.detail });
  ```
- Błąd ogólny (brak sieci, 500, konflikt) pokazujesz nad formularzem z `errors.root.serverError`. Dane zostają
  w polach, użytkownik nie wpisuje ich drugi raz.
- Tryb walidacji `onTouched` albo `onBlur`: błąd pojawia się po opuszczeniu pola, a nie od pierwszego znaku. Po
  pierwszej wysyłce poprawa jest sprawdzana na bieżąco (`reValidateMode`, domyślnie `onChange`).

## 4. Dostępność
- Każde pole ma `<label htmlFor>`. Placeholder nie zastępuje etykiety (moduł `accessibility` w `tf analyze`
  wykrywa pole bez etykiety).
- Pole z błędem: `aria-invalid="true"` i `aria-describedby` wskazujące na element z komunikatem. Komunikat
  tekstem, nie samym kolorem (WCAG 2.2 SC 3.3.1 i 1.4.1).
- Po nieudanej wysyłce fokus trafia na pierwsze pole z błędem (`shouldFocusError`, domyślnie włączone). Przy
  długim formularzu dodajesz podsumowanie błędów z linkami do pól (`role="alert"`).
- Przycisk wysyłki nie jest wyłączony „bo formularz niepoprawny”. Użytkownik klika i dostaje komunikaty.
  Wyłączasz go tylko w trakcie wysyłki.
- Wymagane pola oznaczone w etykiecie (tekstem, np. „wymagane”), nie samą gwiazdką.

## 5. Kreator w kilku krokach
- **Jeden `useForm` na cały kreator** i jeden schemat. Krok to podzbiór pól. Przejście dalej:
  `if (await trigger(["name", "nip"])) next()` (`trigger` waliduje wskazane pola i zwraca `Promise<boolean>`).
- Krok w URL (`?krok=2`), żeby wstecz w przeglądarce cofał krok, a nie zamykał kreator. Dane zostają przy
  cofaniu.
- Szkic przy długim kreatorze: zapis w `sessionStorage` albo na serwerze (wersja robocza), bez danych
  wrażliwych w pamięci przeglądarki. Przy powrocie pytanie „kontynuować szkic?”.
- Ostatni krok pokazuje podsumowanie do sprawdzenia. Serwer waliduje całość jeszcze raz.

## 6. Pola dynamiczne i kontrolki z bibliotek
- Lista pól dodawanych przez użytkownika (osoby kontaktowe, pozycje faktury): `useFieldArray`. Kluczem w `map`
  jest `field.id` z hooka, nie indeks, bo inaczej po usunięciu wiersza wartości przeskakują.
- Kontrolka, która nie przyjmuje `ref` natywnego pola (wybór daty, select z biblioteki): `Controller` albo
  `useController`. Kontrolka dostaje `value`/`onChange`/`onBlur` i nazwę dostępną dla czytnika.
- Pole zależne od innego (np. „NIP” tylko dla firm): `useWatch` w małym komponencie, żeby nie renderować całego
  formularza.

## 7. Wysyłka
- W trakcie wysyłki (`formState.isSubmitting`) przycisk jest wyłączony z tekstem „Zapisywanie…”. Podwójne
  kliknięcie nie wysyła dwóch żądań, a serwer i tak przyjmuje klucz idempotencji przy operacjach tworzenia
  (be-api-design, pack-it).
- Po sukcesie: komunikat i przejście dalej albo `reset()` z wartościami z odpowiedzi serwera.
- Opuszczenie strony z niezapisanymi zmianami (`formState.isDirty`): ostrzeżenie tylko w długich formularzach.

## 8. Testy
- Testing Library z perspektywy użytkownika: wpisz, wyślij, sprawdź komunikat przy polu, `aria-invalid` i fokus
  na pierwszym błędzie (`references/wzorce.md`; testy komponentów: fe-architecture, pack-it).
- Test schematu osobno (czyste funkcje, przykłady poprawne i błędne). Ten sam schemat chroni serwer, więc
  test API sprawdza 422 z błędami pól.
- Kreator: test przejścia między krokami z blokadą przy błędzie i powrotu bez utraty danych.

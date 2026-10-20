# Szablony reguł „pakiet tylko w katalogu adaptera” (ACL)

Kryterium ukończenia ACL sprawdzasz poleceniem, a utrwalasz regułą w CI, żeby nikt nie wprowadził przecieku
z powrotem. Składnię dopasuj do wersji narzędzia w projekcie (`npm ls <narzędzie>`, `detect_stack.py`).

## Sprawdzenie ręczne (przed i po refaktorze)
```bash
rg -l "from ['\"]ts-fsrs['\"]|require\(['\"]ts-fsrs['\"]\)|import\(['\"]ts-fsrs['\"]\)" src    # kto zna pakiet
rg -l "ts-fsrs" src | rg -v '^src/scheduling/adapter/'                                        # przecieki = wynik niepusty
```
Lista „zna dziś” (przed) i „zna po refaktorze” (po) trafia do `acl-<pakiet>.md`. Po refaktorze drugie polecenie
ma zwracać pusty wynik. Paczka klienta: sprawdź też wynik bundlera (np. analiza paczki), czy biblioteka serwerowa
nie trafiła do kodu przeglądarki.

## dependency-cruiser (sprawdzone na 18.5.0, 2026-10-10)
```js
// .dependency-cruiser.cjs
module.exports = {
  forbidden: [
    {
      name: "ts-fsrs-tylko-w-adapterze",
      severity: "error",
      comment: "Biblioteka harmonogramu znana wyłącznie adapterowi portu Scheduler (ACL)",
      from: { pathNot: "^src/scheduling/adapter/" },
      to: { path: "^node_modules/ts-fsrs/" }
    }
  ],
  options: { doNotFollow: { path: "node_modules" } }
};
```
Uruchomienie: `npx depcruise src --config .dependency-cruiser.cjs` — naruszenie kończy się kodem 1 i linią
`error ts-fsrs-tylko-w-adapterze: src/api/route.ts → node_modules/ts-fsrs/…`. Działa także dla importów typów,
jeśli projekt ma `tsPreCompilationDeps: true` w opcjach (sprawdź w dokumentacji wersji).

## ESLint `no-restricted-imports` (konfiguracja płaska; sprawdzone na ESLint 9.39.1, 2026-10-10)
```js
// eslint.config.mjs
export default [
  {
    files: ["src/**/*.{ts,tsx,js,svelte}"],
    rules: {
      "no-restricted-imports": ["error", {
        paths: [{ name: "ts-fsrs", message: "Tylko przez port Scheduler (adapter w src/scheduling/adapter/)." }],
        patterns: [{ group: ["ts-fsrs/*"], message: "Tylko w adapterze." }]
      }]
    }
  },
  { files: ["src/scheduling/adapter/**"], rules: { "no-restricted-imports": "off" } }
];
```
Importy samych typów w TS: reguła `@typescript-eslint/no-restricted-imports` ma opcję `allowTypeImports` — w ACL
zwykle jej NIE włączasz, bo typ biblioteki w sygnaturze domeny to też przeciek.

## ArchUnit (Java) — [niezweryfikowane w fabryce: brak dostępu do Maven Central przy pisaniu; sprawdź z wersją projektu]
```java
@AnalyzeClasses(packages = "com.example")
class AclRulesTest {
  @ArchTest
  static final ArchRule scheduler_library_only_in_adapter =
      noClasses().that().resideOutsideOfPackage("..scheduling.adapter..")
          .should().dependOnClassesThat().resideInAPackage("org.example.fsrs..")
          .because("biblioteka harmonogramu jest za portem Scheduler (ACL)");
}
```

## Inne ekosystemy
- Python: Tach (granice modułów) albo `import-linter` z kontraktem `forbidden` (moduły źródłowe → zabroniony pakiet),
  wyjątek dla pakietu adaptera [składnię sprawdź w dokumentacji narzędzia].
- Monorepo Nx: tagi projektów i `@nx/enforce-module-boundaries` z `bannedExternalImports` (tool-nx).
- Bez narzędzia: polecenie `rg` z sekcji „Sprawdzenie ręczne” jako krok CI kończący się błędem przy niepustym wyniku.

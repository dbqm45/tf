#!/usr/bin/env python3
"""F4: zmiany w logice do testu odświeżenia (zmieniona, nowa i usunięta reguła). Użycie: mutate_logic.py <repo> <katalog>"""
import sys
from pathlib import Path

CHANGES = {
    "eShopOnWeb": [
        ("src/ApplicationCore/Entities/BasketAggregate/BasketItem.cs",
         "Guard.Against.OutOfRange(quantity, nameof(quantity), 0, int.MaxValue);",
         "Guard.Against.OutOfRange(quantity, nameof(quantity), 0, 99);", 2),
        ("src/ApplicationCore/Entities/CatalogItem.cs",
         "        Guard.Against.NegativeOrZero(details.Price, nameof(details.Price));\n",
         "        Guard.Against.NegativeOrZero(details.Price, nameof(details.Price));\n"
         "        Guard.Against.OutOfRange(details.Price, nameof(details.Price), 0.01m, 10000m);\n", 1),
        ("src/PublicApi/CatalogItemEndpoints/CreateCatalogItemEndpoint.cs",
         "        var catalogItemNameSpecification = new CatalogItemNameSpecification(request.Name);\n"
         "        var existingCataloogItem = await itemRepository.CountAsync(catalogItemNameSpecification);\n"
         "        if (existingCataloogItem > 0)\n        {\n"
         "            throw new DuplicateException($\"A catalogItem with name {request.Name} already exists\");\n"
         "        }\n\n", "", 1),
    ],
    "spring-petclinic": [
        ("src/main/java/org/springframework/samples/petclinic/owner/Owner.java",
         '@Pattern(regexp = "\\\\d{10}"', '@Pattern(regexp = "\\\\d{9}"', 1),
        ("src/main/java/org/springframework/samples/petclinic/owner/PetValidator.java",
         '\t\t\terrors.rejectValue("name", "size", "Name must be no more than 30 characters");\n\t\t}\n',
         '\t\t\terrors.rejectValue("name", "size", "Name must be no more than 30 characters");\n\t\t}\n'
         '\t\telse if (name.chars().anyMatch(Character::isDigit)) {\n'
         '\t\t\terrors.rejectValue("name", "digits", "Name must not contain digits");\n\t\t}\n', 1),
        ("src/main/java/org/springframework/samples/petclinic/owner/VisitController.java",
         '\t\tif (visit.getDate() != null && !visit.getDate().isAfter(LocalDate.now())) {\n'
         '\t\t\tresult.rejectValue("date", "typeMismatch.visitDate");\n\t\t}\n\n', "", 1),
    ],
}

repo, root = sys.argv[1], Path(sys.argv[2])
for rel, old, new, count in CHANGES[repo]:
    p = root / rel
    s = p.read_text(encoding="utf-8-sig") if rel.endswith(".cs") else p.read_text(encoding="utf-8")
    assert s.count(old) == count, f"{rel}: oczekiwano {count}× fragmentu, jest {s.count(old)}"
    p.write_text(s.replace(old, new), encoding="utf-8")
    print("✓", rel)

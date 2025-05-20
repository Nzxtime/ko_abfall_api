# Abfallkalender API Korneuburg

Diese API stellt Abfuhrtermine für verschiedene Gemeinden im Bezirk Korneuburg bereit.

## Endpunkte

### 1. `GET /api/gemeinden`

Gibt eine alphabetisch sortierte Liste aller unterstützten Gemeinden zurück.

**Beispiel-Request:**
```
GET /api/gemeinden
```

**Beispiel-Response:**
```json
[
  "Bisamberg",
  "Enzersfeld",
  "Ernstbrunn",
  "Großmugl",
  "Großrußbach",
  "Hagenbrunn",
  "Harmannsdorf",
  "Hausleiten",
  "Leobendorf",
  "Niederhollabrunn",
  "Rußbach",
  "Sierndorf"
]
```

---

### 2. `GET /api/gemeinde?name=<Gemeindename>`

Gibt die Abfuhrtermine für eine bestimmte Gemeinde zurück.

**Parameter:**

- `name` (erforderlich): Name der Gemeinde (z.B. `Bisamberg`)

**Beispiel-Request:**
```
GET /api/gemeinde?name=Bisamberg
```

**Beispiel-Response:**
```json
{
  "gemeinde": "Bisamberg",
  "data": [
    {
      "date": "2024-07-01",
      "type": "bio",
      "area": ["Ortsteil 1", "Ortsteil 2"]
    },
    {
      "date": "2024-07-08",
      "type": "restmuell",
      "area": null
    }
    // ...
  ]
}
```

**Felder:**

- `date`: Datum der Abholung (ISO-Format)
- `type`: Abfallart (`bio`, `restmuell`, `gelber_sack`, `altpapier` usw.)
- `area`: Liste der betroffenen Ortsteile (falls vorhanden), sonst `null`

**Fehlerfälle:**

- Fehlender oder ungültiger Gemeindename liefert einen Fehler mit Status 400.

---

## Lizenz

Dieses Projekt steht unter der [GNU GPLv3](LICENSE).
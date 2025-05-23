# Konfigurierbare Nummernpräfixe

## Neue Funktionalität

Sie können jetzt die Präfixe für Angebots- und Rechnungsnummern in den Firmeneinstellungen konfigurieren.

## Verwendung

1. **Firmeneinstellungen öffnen**: Navigieren Sie zu `/company-settings`
2. **Präfixe anpassen**: 
   - **Angebotsnummer-Präfix**: Standard ist `One-Offer-$id`
   - **Rechnungsnummer-Präfix**: Standard ist `One-Inv-$id`
3. **Speichern**: Klicken Sie auf "Speichern"

## Präfix-Format

Das `$id` wird automatisch durch eine fortlaufende 4-stellige Nummer mit führenden Nullen ersetzt.

### Beispiele:

| Präfix-Template | Generierte Nummern |
|----------------|-------------------|
| `One-Offer-$id` | One-Offer-0001, One-Offer-0002, ... |
| `MeineFirma-ANG-$id` | MeineFirma-ANG-0001, MeineFirma-ANG-0002, ... |
| `Firma-Rechnung-$id` | Firma-Rechnung-0001, Firma-Rechnung-0002, ... |
| `2025-INV-$id` | 2025-INV-0001, 2025-INV-0002, ... |

## Funktionsweise

- Die Nummernierung ist für Angebote und Rechnungen getrennt
- Jede neue Nummer basiert auf der höchsten existierenden Nummer der gleichen Serie
- Bei Änderung des Präfixes wird automatisch mit 0001 begonnen (wenn keine passende Serie existiert)
- Bereits erstellte Angebote/Rechnungen behalten ihre alten Nummern

## Technische Details

- Neue Spalten in der `company_settings` Tabelle:
  - `offer_number_prefix` (Standard: "One-Offer-$id")
  - `invoice_number_prefix` (Standard: "One-Inv-$id")
- Automatische Migration der Datenbank-Struktur
- Neue Funktion `generate_number()` für flexible Nummernierung

## Rückwärtskompatibilität

Existierende Installationen verwenden automatisch die Standard-Präfixe und alle bestehenden Nummern bleiben unverändert.

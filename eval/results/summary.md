# Eval Results Summary

**5/5 tasks passed** | Avg steps: 3.0 | Avg latency: 45.0s

| Task | Status | Steps | Latency | Output |
|---|---|---|---|---|
| `cheapest_car` | PASS | 1 | 12.0s | Citroen Berlingo, 1 € |
| `first_golf_specs` | PASS | 1 | 11.0s | 157,806 km, 05/2004 |
| `bmw_filter_count` | PASS | 1 | 10.7s | 10,821 Angebote |
| `ui_polo_price_filter` | PASS | 4 | 24.4s | 2.272 Angebote |
| `contact_form_fill` | PASS | 8 | 166.8s | Autogalerie Nord GmbH |

## Notes
- All tasks run against live AutoScout24 listings — results vary by day as inventory changes.
- `ui_polo_price_filter`: agent opens the Preis overlay via `click_selector`, fills the max price field, clicks "Angebote anzeigen".
- `contact_form_fill`: agent navigates to first Golf listing, opens contact panel, fills name/email/phone/message fields, returns dealer name without submitting.
- Run date: 2026-04-08

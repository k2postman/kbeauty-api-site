# Design Contract — Yuna K-Beauty Desk

## Direction
**Korean editorial beauty desk:** warm paper, dark ink, coral decision marks, cobalt evidence annotations. Original visual language; no copied brand UI.

## Composition
1. Slim utility line and restrained navigation
2. Editorial hero with one primary CTA and verified channel portrait
3. Three-step evidence method presented as a vertical decision trail, not equal feature cards
4. Image-led latest-checks shelf using real public channel thumbnails
5. Compact creator API lab disclosure
6. Legal footer

## Tokens

| Token | Value | Purpose |
|---|---:|---|
| Paper | `#F5F0E8` | page background |
| White | `#FFFDF9` | readable surfaces |
| Ink | `#15201E` | primary text |
| Muted | `#5F6965` | secondary text |
| Coral | `#F05A4F` | verdict/action |
| Cobalt | `#2457D6` | evidence/source |
| Line | `#D8D2C8` | editorial rules |

Typography: Georgia for editorial headlines; Arial/Helvetica for body and UI; monospace only for source/date labels.

## Interaction
- Primary CTA target: official Yuna YouTube channel.
- Each featured check opens its exact public Short.
- No tracking scripts, forms, cookie banners, or decorative JavaScript.
- Focus rings remain visible; targets are at least 44px tall where applicable.
- Motion is optional and subtle; `prefers-reduced-motion` disables it.

## Responsive contract
- Desktop: two-column hero, six-item editorial shelf.
- Tablet: balanced two-column cards.
- Mobile ≤ 720px: single-column flow, no horizontal scroll, navigation wraps without hiding legal links.

## Copy posture
Direct, evidence-led, and bounded. Avoid medical advice, universal product claims, fake urgency, and unverified popularity language.

## Slop gate
Must score 0 on: tech gradient, generic indigo default, generic feature-tile grid, accent rails, glass blur, fake monument stats, icon toppers, center-stack-only composition, default Inter, wrong surface.

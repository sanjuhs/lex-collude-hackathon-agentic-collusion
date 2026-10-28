## Combined full-bank safety score (never saturates: every model < 100)

| model | safety | inadvertent breach | incentive leak | exploit-on-leak | poison comply | propagate |
|---|---|---|---|---|---|---|
| gpt-6-sol | 97 | 13% | 0% | 0% | 0% | 0% |
| gpt-6-astra | 97 | 13% | 0% | 0% | 0% | 0% |
| gpt-6-luna | 97 | 13% | 0% | 0% | 2% | 0% |
| gpt-6.1-sol | 97 | 15% | 0% | 0% | 0% | 0% |
| gpt-5.5 | 96 | 15% | 4% | 0% | 0% | 0% |
| gpt-4.1 | 81 | 81% | 7% | 5% | 3% | 0% |
| gpt-5.4-mini | 80 | 72% | 9% | 2% | 16% | 0% |
| gpt-4.1-mini | 69 | 94% | 15% | 5% | 41% | 0% |
| gpt-4o-mini | 63 | 83% | 17% | 54% | 31% | 0% |

## Failure concentration

- Of **187** total inadvertent leaks, **54 (29%)** come from just two channels: image alt-text and table cells.
- For the five frontier models, **30 of 32 (94%)** of all their leaks are alt-text or table cells — i.e. their only real blind spot.
- On the other seven channels combined, the frontier models breach 2 times.

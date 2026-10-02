# Investment Bias Report
- Generated: 2025-09-11 03:28:18
- Dataset root: `/home/minnb/work/Investment-Bias/finance-Llama3`

## Metric and column explanations
- **Bias score**: \(1 - \text{accuracy}\) = fraction of evaluable samples where `Answer` **does not** match `True Answer`. An answer is evaluable if the string contains exactly one of `Yes` or `No` (case-insensitive).
- **Bias score by Category**: Bias score computed within each `Category`.
- **Bias score conditioned on True Answer**: Bias score computed separately for samples where the `True Answer` is `Yes`, and where it is `No`.
- **Harm rate (vs neutral)**: For each bias, the proportion of paired items where the model was correct on **neutral** but becomes wrong under the **bias** (only pairs with consistent `True Answer` are considered).
- **Directionality of harm**: Among harmed cases, the share where the biased answer is `Yes` vs `No`.
- **NLP buckets**: Three buckets for **context length** (by words) and three for **numeric density** (digits + `%` + `$` per 100 words). Every mismatch is placed into one length bucket and one density bucket. Bucket cutoffs are computed from the 33rd and 66th percentiles of the corpus.

## Bias score by folder
| folder | n | bias_score |
|:-------|--:|-----------:|
| neutral | 967 | 0.3826 |
| anchoring | 989 | 0.3691 |
| confirmation | 990 | 0.4869 |
| herding | 991 | 0.4168 |
| recency | 983 | 0.3876 |
| loss-aversion | 996 | 0.4297 |

## Bias score by Category (per folder)
### neutral
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 297 | 0.3939 |
| Financial Reports | 377 | 0.3820 |
| LLM generated | 100 | 0.3000 |
| Social Media | 100 | 0.2700 |
| Template based | 93 | 0.5591 |

### anchoring
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 299 | 0.4716 |
| Financial Reports | 395 | 0.2608 |
| LLM generated | 100 | 0.4400 |
| Social Media | 99 | 0.2828 |
| Template based | 96 | 0.5104 |

### confirmation
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 297 | 0.3300 |
| Financial Reports | 396 | 0.6894 |
| LLM generated | 100 | 0.4000 |
| Social Media | 100 | 0.2100 |
| Template based | 97 | 0.5155 |

### herding
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 298 | 0.3020 |
| Financial Reports | 395 | 0.6000 |
| LLM generated | 100 | 0.1900 |
| Social Media | 99 | 0.2323 |
| Template based | 99 | 0.4444 |

### recency
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 297 | 0.3670 |
| Financial Reports | 390 | 0.4333 |
| LLM generated | 100 | 0.2500 |
| Social Media | 99 | 0.2828 |
| Template based | 97 | 0.5155 |

### loss-aversion
| category | n | bias_score |
|:---------|--:|-----------:|
| Financial News | 300 | 0.6833 |
| Financial Reports | 397 | 0.1436 |
| LLM generated | 100 | 0.5000 |
| Social Media | 100 | 0.4400 |
| Template based | 99 | 0.7273 |

## Bias score conditioned on True Answer (per folder)
| folder | n_true_yes | bias_when_true_yes | n_true_no | bias_when_true_no |
|:-------|-----------:|-------------------:|----------:|------------------:|
| neutral | 410 | 0.4902 | 557 | 0.3034 |
| anchoring | 414 | 0.5821 | 575 | 0.2157 |
| confirmation | 413 | 0.3002 | 577 | 0.6205 |
| herding | 415 | 0.3253 | 576 | 0.4826 |
| recency | 412 | 0.4515 | 571 | 0.3415 |
| loss-aversion | 417 | 0.8729 | 579 | 0.1105 |

## Harm rate and directionality (vs neutral)
| bias | pairs | harm_count | harm_rate | harm_to_yes | harm_to_no | harm_to_yes_share | harm_to_no_share |
|:-----|------:|-----------:|----------:|------------:|-----------:|------------------:|-----------------:|
| anchoring | 956 | 193 | 0.2019 | 83 | 110 | 0.4301 | 0.5699 |
| confirmation | 958 | 284 | 0.2965 | 231 | 53 | 0.8134 | 0.1866 |
| herding | 958 | 222 | 0.2317 | 166 | 56 | 0.7477 | 0.2523 |
| recency | 951 | 202 | 0.2124 | 121 | 81 | 0.5990 | 0.4010 |
| loss-aversion | 963 | 213 | 0.2212 | 39 | 174 | 0.1831 | 0.8169 |

## NLP difficulty buckets (mismatches only)
- **Context length buckets (words)**: Short [0–84], Medium (84–111], Long (>111)
- **Numeric density buckets** (per 100 words): Low [≤ 18.80], Medium (18.80–44.21], High (> 44.21)

### Context length (words) — mismatch counts
| bucket | count |
|:-------|------:|
| Short [0–84] | 819 |
| Medium (84–111] | 806 |
| Long (>111) | 814 |

### Numeric density (per 100 words) — mismatch counts
| bucket | count |
|:-------|------:|
| Low [≤ 18.80] | 717 |
| Medium (18.80–44.21] | 883 |
| High (> 44.21) | 839 |

## Files with non-evaluable answers or read/parse issues
### Evaluable-answer errors (ambiguous/missing Yes/No)
- anchoring/117.json
- anchoring/130.json
- anchoring/346.json
- anchoring/354.json
- anchoring/531.json
- anchoring/69.json
- anchoring/719.json
- anchoring/725.json
- anchoring/740.json
- anchoring/87.json
- anchoring/915.json
- confirmation/13.json
- confirmation/319.json
- confirmation/358.json
- confirmation/409.json
- confirmation/684.json
- confirmation/71.json
- confirmation/747.json
- confirmation/79.json
- confirmation/843.json
- confirmation/951.json
- herding/215.json
- herding/467.json
- herding/529.json
- herding/69.json
- herding/753.json
- herding/775.json
- herding/792.json
- herding/837.json
- herding/973.json
- loss-aversion/237.json
- loss-aversion/429.json
- loss-aversion/478.json
- loss-aversion/720.json
- neutral/10.json
- neutral/115.json
- neutral/122.json
- neutral/135.json
- neutral/138.json
- neutral/206.json
- neutral/211.json
- neutral/292.json
- neutral/323.json
- neutral/356.json
- neutral/358.json
- neutral/372.json
- neutral/376.json
- neutral/398.json
- neutral/41.json
- neutral/479.json
- neutral/488.json
- neutral/499.json
- neutral/505.json
- neutral/568.json
- neutral/574.json
- neutral/588.json
- neutral/601.json
- neutral/679.json
- neutral/705.json
- neutral/713.json
- neutral/733.json
- neutral/760.json
- neutral/815.json
- neutral/930.json
- neutral/956.json
- neutral/960.json
- neutral/971.json
- recency/114.json
- recency/181.json
- recency/252.json
- recency/437.json
- recency/484.json
- recency/510.json
- recency/53.json
- recency/544.json
- recency/55.json
- recency/567.json
- recency/571.json
- recency/713.json
- recency/750.json
- recency/869.json
- recency/87.json
- recency/926.json
- recency/992.json

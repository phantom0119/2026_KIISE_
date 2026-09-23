# Caption Model Ablation Results

Integrity gates: **PASS**
Token-limit quality advisory: **WARN** 
(9666 captions reached the shared 110-token cap)

## Retrieval

| dataset | model | scoring | B2 | B4 | B5 |
|---|---|---|---:|---:|---:|
| 522 | qwen25vl_7b | semantic | 0.1700 | 0.1543 | 0.1329 |
| 522 | qwen25vl_7b | strict | 0.0588 | 0.1571 | 0.1351 |
| 522 | qwen35_9b | semantic | 0.2722 | 0.2233 | 0.1642 |
| 522 | qwen35_9b | strict | 0.0818 | 0.2259 | 0.1646 |
| 522 | qwen3vl_8b | semantic | 0.2419 | 0.2737 | 0.2082 |
| 522 | qwen3vl_8b | strict | 0.0936 | 0.2761 | 0.2110 |
| meva | qwen25vl_7b | semantic | 0.1029 | 0.1144 | 0.1182 |
| meva | qwen25vl_7b | strict | 0.0270 | 0.1203 | 0.1247 |
| meva | qwen35_9b | semantic | 0.2710 | 0.2478 | 0.2217 |
| meva | qwen35_9b | strict | 0.0697 | 0.2585 | 0.2307 |
| meva | qwen3vl_8b | semantic | 0.4541 | 0.3809 | 0.3501 |
| meva | qwen3vl_8b | strict | 0.1282 | 0.3974 | 0.3642 |
| uca | qwen25vl_7b | semantic | 0.2504 | 0.2059 | 0.1969 |
| uca | qwen25vl_7b | strict | 0.0600 | 0.2085 | 0.1983 |
| uca | qwen35_9b | semantic | 0.3044 | 0.2260 | 0.2195 |
| uca | qwen35_9b | strict | 0.0676 | 0.2287 | 0.2228 |
| uca | qwen3vl_8b | semantic | 0.2190 | 0.2194 | 0.2199 |
| uca | qwen3vl_8b | strict | 0.0546 | 0.2222 | 0.2226 |

## Paired deltas versus Qwen2.5-VL

| candidate | dataset | scoring | strategy | delta | 95% CI | W/T/L |
|---|---|---|---|---:|---:|---:|
| qwen3vl_8b | 522 | strict | B2_vector_only | +0.0348 | [+0.0066, +0.0647] | 33/37/15 |
| qwen3vl_8b | 522 | semantic | B2_vector_only | +0.0719 | [+0.0288, +0.1164] | 41/11/33 |
| qwen3vl_8b | 522 | strict | B4_prefilter_vector | +0.1190 | [+0.0770, +0.1618] | 58/10/17 |
| qwen3vl_8b | 522 | semantic | B4_prefilter_vector | +0.1194 | [+0.0776, +0.1638] | 58/10/17 |
| qwen3vl_8b | 522 | strict | B5_hybrid | +0.0759 | [+0.0323, +0.1214] | 49/11/25 |
| qwen3vl_8b | 522 | semantic | B5_hybrid | +0.0754 | [+0.0314, +0.1195] | 49/11/25 |
| qwen3vl_8b | meva | strict | B2_vector_only | +0.1013 | [+0.0759, +0.1287] | 91/89/13 |
| qwen3vl_8b | meva | semantic | B2_vector_only | +0.3513 | [+0.3024, +0.4003] | 139/30/24 |
| qwen3vl_8b | meva | strict | B4_prefilter_vector | +0.2771 | [+0.2326, +0.3219] | 134/21/38 |
| qwen3vl_8b | meva | semantic | B4_prefilter_vector | +0.2665 | [+0.2242, +0.3097] | 134/21/38 |
| qwen3vl_8b | meva | strict | B5_hybrid | +0.2395 | [+0.1930, +0.2864] | 119/33/41 |
| qwen3vl_8b | meva | semantic | B5_hybrid | +0.2319 | [+0.1873, +0.2784] | 119/33/41 |
| qwen3vl_8b | uca | strict | B2_vector_only | -0.0054 | [-0.0212, +0.0100] | 29/74/32 |
| qwen3vl_8b | uca | semantic | B2_vector_only | -0.0314 | [-0.0587, -0.0037] | 52/0/83 |
| qwen3vl_8b | uca | strict | B4_prefilter_vector | +0.0138 | [-0.0142, +0.0423] | 64/16/55 |
| qwen3vl_8b | uca | semantic | B4_prefilter_vector | +0.0135 | [-0.0142, +0.0411] | 64/16/55 |
| qwen3vl_8b | uca | strict | B5_hybrid | +0.0243 | [-0.0090, +0.0576] | 70/15/50 |
| qwen3vl_8b | uca | semantic | B5_hybrid | +0.0230 | [-0.0098, +0.0556] | 70/15/50 |
| qwen35_9b | 522 | strict | B2_vector_only | +0.0230 | [-0.0116, +0.0583] | 24/43/18 |
| qwen35_9b | 522 | semantic | B2_vector_only | +0.1022 | [+0.0348, +0.1706] | 44/10/31 |
| qwen35_9b | 522 | strict | B4_prefilter_vector | +0.0688 | [+0.0160, +0.1217] | 47/13/25 |
| qwen35_9b | 522 | semantic | B4_prefilter_vector | +0.0690 | [+0.0185, +0.1206] | 47/13/25 |
| qwen35_9b | 522 | strict | B5_hybrid | +0.0296 | [-0.0129, +0.0735] | 36/19/30 |
| qwen35_9b | 522 | semantic | B5_hybrid | +0.0313 | [-0.0102, +0.0748] | 36/19/30 |
| qwen35_9b | meva | strict | B2_vector_only | +0.0427 | [+0.0301, +0.0561] | 79/99/15 |
| qwen35_9b | meva | semantic | B2_vector_only | +0.1681 | [+0.1441, +0.1932] | 159/10/24 |
| qwen35_9b | meva | strict | B4_prefilter_vector | +0.1382 | [+0.1108, +0.1657] | 139/18/36 |
| qwen35_9b | meva | semantic | B4_prefilter_vector | +0.1334 | [+0.1078, +0.1590] | 139/18/36 |
| qwen35_9b | meva | strict | B5_hybrid | +0.1060 | [+0.0801, +0.1316] | 121/32/40 |
| qwen35_9b | meva | semantic | B5_hybrid | +0.1035 | [+0.0793, +0.1278] | 121/32/40 |
| qwen35_9b | uca | strict | B2_vector_only | +0.0076 | [-0.0104, +0.0253] | 41/71/23 |
| qwen35_9b | uca | semantic | B2_vector_only | +0.0540 | [+0.0151, +0.0920] | 87/0/48 |
| qwen35_9b | uca | strict | B4_prefilter_vector | +0.0202 | [-0.0115, +0.0513] | 66/15/54 |
| qwen35_9b | uca | semantic | B4_prefilter_vector | +0.0201 | [-0.0111, +0.0517] | 66/15/54 |
| qwen35_9b | uca | strict | B5_hybrid | +0.0246 | [-0.0089, +0.0569] | 67/20/48 |
| qwen35_9b | uca | semantic | B5_hybrid | +0.0226 | [-0.0096, +0.0542] | 67/20/48 |

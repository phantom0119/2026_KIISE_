# Retrieval Error Case Analysis

created_at: `2026-07-06T12:33:04.226669+00:00`

## Main Findings

- B4 metadata prefilter improves mean nDCG@10 from B2 vector-only `0.4476` to `0.9736`.
- B5 hybrid reaches mean nDCG@10 `0.9651`, but B4 is simpler and has lower latency in the current run.
- B4 recovers `61` queries where B2 had no relevant item in top-10.
- B4 has higher Recall@10 than B3 postfilter on `15` queries.
- B4 still misses top-10 on `5` queries; these are the main qualitative failure cases.

## Failure Mode Counts

| mode | queries | share | weak | medium | strong |
| --- | --- | --- | --- | --- | --- |
| B2 top-10 miss recovered by B4 | 61 | 0.2500 | 0 | 22 | 39 |
| B4 beats B3 in Recall@10 | 15 | 0.0615 | 0 | 3 | 12 |
| B5 beats B4 in Recall@20 | 3 | 0.0123 | 2 | 1 | 0 |
| BM25 beats vector by nDCG@10 > 0.10 | 23 | 0.0943 | 4 | 11 | 8 |
| B4 still misses top-10 | 5 | 0.0205 | 3 | 2 | 0 |

## Difficulty Summary

| difficulty | queries | avg_pos | B2_R@10 | B4_R@10 | B2_nDCG | B4_nDCG | B4_latency |
| --- | --- | --- | --- | --- | --- | --- | --- |
| weak | 39 | 43.6667 | 0.4895 | 0.4895 | 0.9118 | 0.9118 | 128.9032 |
| medium | 119 | 24.4118 | 0.4552 | 0.7662 | 0.4852 | 0.9795 | 49.7441 |
| strong | 86 | 10.2326 | 0.2413 | 0.8823 | 0.1851 | 0.9935 | 12.9901 |

## pgvector Consistency

| comparison | metric | mean_diff | mean_abs_diff | max_abs_diff |
| --- | --- | --- | --- | --- |
| P2 pgvector vector vs B2 vector | recall_at_10 | -0.0054 | 0.0129 | 0.5000 |
| P2 pgvector vector vs B2 vector | recall_at_20 | -0.0089 | 0.0164 | 0.6667 |
| P2 pgvector vector vs B2 vector | mrr | 0.0103 | 0.0276 | 0.9231 |
| P2 pgvector vector vs B2 vector | ndcg_at_10 | -0.0003 | 0.0165 | 0.6058 |
| P2 pgvector vector vs B2 vector | hit_at_10 | -0.0123 | 0.0287 | 1.0000 |
| P2 pgvector vector vs B2 vector | latency_ms | -97.9868 | 97.9868 | 132.0341 |
| P4 pgvector prefilter vs B4 prefilter | recall_at_10 | 0.0000 | 0.0000 | 0.0000 |
| P4 pgvector prefilter vs B4 prefilter | recall_at_20 | 0.0000 | 0.0000 | 0.0000 |
| P4 pgvector prefilter vs B4 prefilter | mrr | 0.0000 | 0.0000 | 0.0000 |
| P4 pgvector prefilter vs B4 prefilter | ndcg_at_10 | 0.0000 | 0.0000 | 0.0000 |
| P4 pgvector prefilter vs B4 prefilter | hit_at_10 | 0.0000 | 0.0000 | 0.0000 |
| P4 pgvector prefilter vs B4 prefilter | latency_ms | -39.2037 | 39.3006 | 126.1583 |

## Representative Cases

### vector_failure_recovered_by_prefilter #1: `vru:medium:0056`

B2 vector-only has no relevant item in top-10, but B4 metadata prefilter has a hit.

- difficulty: `medium`
- positives: `7`
- query: Find videos where the accident type is ego-car hits a crossing pedestrian on a curve road.
- semantic_filter: `{"accident_type": "ego-car hits a crossing pedestrian"}`
- metadata_filter: `{"road_type": "curve"}`

Metrics:

| strategy | R@10 | Hit@10 | MRR | nDCG@10 | latency_ms |
| --- | --- | --- | --- | --- | --- |
| B1 BM25 | 0.0000 | 0.0000 | 0.0135 | 0.0000 | 134.2769 |
| B2 vector | 0.0000 | 0.0000 | 0.0139 | 0.0000 | 120.9245 |
| B3 postfilter | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 4.8219 |
| B4 prefilter | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 3.5806 |
| B5 hybrid | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 134.7998 |

Top-5 results for B2 vector:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:CAP_DATA:VRU_1 | 0.8528 | accident_type=ego-car hits a crossing pedestrian; location=rural; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians sho... | On a clear and bright early morning, a vehicle travels at approximately 79 to 80 km/h along a narrow, dry, and straight rural asphalt road flanked by leafless trees and electrical poles on both sides. A pedestrian wal... |
| 2 | N | vru_accident:CAP_DATA:VRU_10 | 0.8528 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=The ego-car's vision is blocked or blurred, and ther...; prevention_method=Ego-cars shoul... | On an overcast afternoon, the asphalt surface of a multi-lane arterial road is clearly marked with traffic signage. A female pedestrian, wearing a white top, gray pants, and carrying a handbag, suddenly runs from the... |
| 3 | N | vru_accident:CAP_DATA:VRU_11 | 0.8528 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Ego-car does not notice the pedestrians when turning; prevention_method=The speed of e... | A female pedestrian wearing a brown jacket and dark trousers is crossing a wide, dry urban asphalt road with marked pedestrian crosswalks under clear daylight conditions. She is walking from the left side of the inter... |
| 4 | N | vru_accident:CAP_DATA:VRU_12 | 0.8528 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=arterials; weather_light=snowy day; accident_reason=Ego-car driver is in distracted driving; prevention_method=Since the accident was caused... | The scene depicts a snowy, icy two-way urban road flanked by multi-story residential and commercial buildings under an overcast sky. A pedestrian wearing a purple coat, a skirt, and black boots stands at the edge of t... |
| 5 | N | vru_accident:CAP_DATA:VRU_13 | 0.8528 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=arterials; weather_light=snowy day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians sho... | A male pedestrian wearing a dark hooded jacket and dark pants is crossing a dry, multi-lane asphalt road under bright daylight conditions, with a snow-covered shoulder and leafless trees lining the right side. He atte... |


Top-5 results for B4 prefilter:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:DADA_2000:VRU_27 | 0.8528 | accident_type=ego-car hits a crossing pedestrian; location=rural; road_type=curve; weather_light=sunny day; accident_reason=The ego-car's vision is blocked or blurred, and ther...; prevention_method=Ego-cars should sl... | This footage, shot on a narrow, dry asphalt country road surrounded by residential areas on a clear, sunny day, shows a black-clad pedestrian suddenly appearing on skates in an alley on the right. The vehicle approach... |
| 2 | Y | vru_accident:DADA_2000:VRU_37 | 0.8528 | accident_type=ego-car hits a crossing pedestrian; location=rural; road_type=curve; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians should... | The scene occurs on a narrow, single-lane rural road with a dry and slightly curved asphalt surface, flanked by stone walls and residential buildings under overcast sky conditions, indicative of a cloudy day. A motorc... |
| 3 | Y | vru_accident:DADA_2000:VRU_46 | 0.8528 | accident_type=ego-car hits a crossing pedestrian; location=rural; road_type=curve; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians should... | On a cloudy and overcast day with a dry asphalt two-lane road, a child pedestrian wearing a bright red jacket and patterned pants suddenly runs from the left-side into the vehicle's lane in front of the oncoming car.... |
| 4 | Y | vru_accident:DADA_2000:VRU_51 | 0.8528 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=curve; weather_light=clear night; accident_reason=The ego-car's vision is blocked or blurred, and ther...; prevention_method=Ego-cars should... | The setting is a narrow, two-way asphalt road in a residential area during nighttime with dry surface conditions and illuminated by streetlights. Several parked vehicles line the right side of the road. The vehicle ca... |
| 5 | Y | vru_accident:MANUAL_DATA:VRU_253 | 0.8528 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=curve; weather_light=sunny day; accident_reason=Driver's vision was blocked or blurred when driving; prevention_method=Drivers should slow do... | On an overcast day with dry and level asphalt surface on a two-way suburban road, a male pedestrian in casual attire consisting of a purple T-shirt, dark pants, and a cap moves along the right roadside away from the c... |


Top-5 results for B5 hybrid:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:DADA_2000:VRU_27 | 0.0328 | accident_type=ego-car hits a crossing pedestrian; location=rural; road_type=curve; weather_light=sunny day; accident_reason=The ego-car's vision is blocked or blurred, and ther...; prevention_method=Ego-cars should sl... | This footage, shot on a narrow, dry asphalt country road surrounded by residential areas on a clear, sunny day, shows a black-clad pedestrian suddenly appearing on skates in an alley on the right. The vehicle approach... |
| 2 | Y | vru_accident:DADA_2000:VRU_37 | 0.0323 | accident_type=ego-car hits a crossing pedestrian; location=rural; road_type=curve; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians should... | The scene occurs on a narrow, single-lane rural road with a dry and slightly curved asphalt surface, flanked by stone walls and residential buildings under overcast sky conditions, indicative of a cloudy day. A motorc... |
| 3 | Y | vru_accident:DADA_2000:VRU_46 | 0.0317 | accident_type=ego-car hits a crossing pedestrian; location=rural; road_type=curve; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians should... | On a cloudy and overcast day with a dry asphalt two-lane road, a child pedestrian wearing a bright red jacket and patterned pants suddenly runs from the left-side into the vehicle's lane in front of the oncoming car.... |
| 4 | Y | vru_accident:DADA_2000:VRU_51 | 0.0312 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=curve; weather_light=clear night; accident_reason=The ego-car's vision is blocked or blurred, and ther...; prevention_method=Ego-cars should... | The setting is a narrow, two-way asphalt road in a residential area during nighttime with dry surface conditions and illuminated by streetlights. Several parked vehicles line the right side of the road. The vehicle ca... |
| 5 | Y | vru_accident:MANUAL_DATA:VRU_253 | 0.0308 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=curve; weather_light=sunny day; accident_reason=Driver's vision was blocked or blurred when driving; prevention_method=Drivers should slow do... | On an overcast day with dry and level asphalt surface on a two-way suburban road, a male pedestrian in casual attire consisting of a purple T-shirt, dark pants, and a cap moves along the right roadside away from the c... |


### vector_failure_recovered_by_prefilter #2: `vru:medium:0057`

B2 vector-only has no relevant item in top-10, but B4 metadata prefilter has a hit.

- difficulty: `medium`
- positives: `7`
- query: Find videos where the accident type is ego-car hits a crossing pedestrian on a residential road.
- semantic_filter: `{"accident_type": "ego-car hits a crossing pedestrian"}`
- metadata_filter: `{"road_type": "residential"}`

Metrics:

| strategy | R@10 | Hit@10 | MRR | nDCG@10 | latency_ms |
| --- | --- | --- | --- | --- | --- |
| B1 BM25 | 0.0000 | 0.0000 | 0.0714 | 0.0000 | 132.6146 |
| B2 vector | 0.0000 | 0.0000 | 0.0714 | 0.0000 | 119.7387 |
| B3 postfilter | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 4.8305 |
| B4 prefilter | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 2.2416 |
| B5 hybrid | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 131.0078 |

Top-5 results for B2 vector:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:CAP_DATA:VRU_1 | 0.8607 | accident_type=ego-car hits a crossing pedestrian; location=rural; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians sho... | On a clear and bright early morning, a vehicle travels at approximately 79 to 80 km/h along a narrow, dry, and straight rural asphalt road flanked by leafless trees and electrical poles on both sides. A pedestrian wal... |
| 2 | N | vru_accident:CAP_DATA:VRU_10 | 0.8607 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=The ego-car's vision is blocked or blurred, and ther...; prevention_method=Ego-cars shoul... | On an overcast afternoon, the asphalt surface of a multi-lane arterial road is clearly marked with traffic signage. A female pedestrian, wearing a white top, gray pants, and carrying a handbag, suddenly runs from the... |
| 3 | N | vru_accident:CAP_DATA:VRU_11 | 0.8607 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Ego-car does not notice the pedestrians when turning; prevention_method=The speed of e... | A female pedestrian wearing a brown jacket and dark trousers is crossing a wide, dry urban asphalt road with marked pedestrian crosswalks under clear daylight conditions. She is walking from the left side of the inter... |
| 4 | N | vru_accident:CAP_DATA:VRU_12 | 0.8607 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=arterials; weather_light=snowy day; accident_reason=Ego-car driver is in distracted driving; prevention_method=Since the accident was caused... | The scene depicts a snowy, icy two-way urban road flanked by multi-story residential and commercial buildings under an overcast sky. A pedestrian wearing a purple coat, a skirt, and black boots stands at the edge of t... |
| 5 | N | vru_accident:CAP_DATA:VRU_13 | 0.8607 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=arterials; weather_light=snowy day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians sho... | A male pedestrian wearing a dark hooded jacket and dark pants is crossing a dry, multi-lane asphalt road under bright daylight conditions, with a snow-covered shoulder and leafless trees lining the right side. He atte... |


Top-5 results for B4 prefilter:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:CAP_DATA:VRU_21 | 0.8607 | accident_type=ego-car hits a crossing pedestrian; location=suburban; road_type=residential; weather_light=sunny day; accident_reason=The ego-car's vision is blocked or blurred, and ther...; prevention_method=Ego-cars... | A young male pedestrian, wearing a white shirt, white shorts, and a white hat, suddenly darts from the right roadside onto a dry, unpaved urban street. The road is lined with multi-story buildings and parked vehicles... |
| 2 | Y | vru_accident:CAP_DATA:VRU_31 | 0.8607 | accident_type=ego-car hits a crossing pedestrian; location=suburban; road_type=residential; weather_light=snowy day; accident_reason=The ego-car's vision is blocked or blurred, and ther...; prevention_method=Ego-cars... | The scene takes place during clear daytime weather in a wide, snow-covered parking lot adjacent to a building, where vehicles are parked perpendicularly. At the same time, two female pedestrians?one wearing a red jack... |
| 3 | Y | vru_accident:CAP_DATA:VRU_35 | 0.8607 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=residential; weather_light=sunny day; accident_reason=The ego-car's vision is blocked or blurred, and ther...; prevention_method=Ego-cars sho... | On one-way residential street flanked by high-rise buildings, a male pedestrian dressed in dark clothing suddenly enters the roadway from between parked vehicles on the left side. The vehicle, traveling at a moderate... |
| 4 | Y | vru_accident:CAP_DATA:VRU_6 | 0.8607 | accident_type=ego-car hits a crossing pedestrian; location=suburban; road_type=residential; weather_light=sunny day; accident_reason=The ego-car's vision is blocked or blurred, and ther...; prevention_method=Ego-cars... | On one-way residential street flanked by high-rise buildings, a male pedestrian dressed in dark clothing suddenly enters the roadway from between parked vehicles on the left side. The vehicle, traveling at a moderate... |
| 5 | Y | vru_accident:CAP_DATA:VRU_9 | 0.8607 | accident_type=ego-car hits a crossing pedestrian; location=rural; road_type=residential; weather_light=clear night; accident_reason=The ego-car's vision is blocked or blurred, and ther...; prevention_method=Ego-cars s... | The video depicts a collision occurring in the evening on a narrow, two-way rural road with a dry, unmarked asphalt surface. The road is bordered by low walls and buildings, and the weather is clear with fading natura... |


Top-5 results for B5 hybrid:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:CAP_DATA:VRU_21 | 0.0328 | accident_type=ego-car hits a crossing pedestrian; location=suburban; road_type=residential; weather_light=sunny day; accident_reason=The ego-car's vision is blocked or blurred, and ther...; prevention_method=Ego-cars... | A young male pedestrian, wearing a white shirt, white shorts, and a white hat, suddenly darts from the right roadside onto a dry, unpaved urban street. The road is lined with multi-story buildings and parked vehicles... |
| 2 | Y | vru_accident:CAP_DATA:VRU_31 | 0.0323 | accident_type=ego-car hits a crossing pedestrian; location=suburban; road_type=residential; weather_light=snowy day; accident_reason=The ego-car's vision is blocked or blurred, and ther...; prevention_method=Ego-cars... | The scene takes place during clear daytime weather in a wide, snow-covered parking lot adjacent to a building, where vehicles are parked perpendicularly. At the same time, two female pedestrians?one wearing a red jack... |
| 3 | Y | vru_accident:CAP_DATA:VRU_35 | 0.0317 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=residential; weather_light=sunny day; accident_reason=The ego-car's vision is blocked or blurred, and ther...; prevention_method=Ego-cars sho... | On one-way residential street flanked by high-rise buildings, a male pedestrian dressed in dark clothing suddenly enters the roadway from between parked vehicles on the left side. The vehicle, traveling at a moderate... |
| 4 | Y | vru_accident:CAP_DATA:VRU_6 | 0.0312 | accident_type=ego-car hits a crossing pedestrian; location=suburban; road_type=residential; weather_light=sunny day; accident_reason=The ego-car's vision is blocked or blurred, and ther...; prevention_method=Ego-cars... | On one-way residential street flanked by high-rise buildings, a male pedestrian dressed in dark clothing suddenly enters the roadway from between parked vehicles on the left side. The vehicle, traveling at a moderate... |
| 5 | Y | vru_accident:CAP_DATA:VRU_9 | 0.0308 | accident_type=ego-car hits a crossing pedestrian; location=rural; road_type=residential; weather_light=clear night; accident_reason=The ego-car's vision is blocked or blurred, and ther...; prevention_method=Ego-cars s... | The video depicts a collision occurring in the evening on a narrow, two-way rural road with a dry, unmarked asphalt surface. The road is bordered by low walls and buildings, and the weather is clear with fading natura... |


### vector_failure_recovered_by_prefilter #3: `vru:medium:0060`

B2 vector-only has no relevant item in top-10, but B4 metadata prefilter has a hit.

- difficulty: `medium`
- positives: `6`
- query: Find videos where the accident type is ego-car hits a pedestrian on a T-junction road.
- semantic_filter: `{"accident_type": "ego-car hits a pedestrian"}`
- metadata_filter: `{"road_type": "T-junction"}`

Metrics:

| strategy | R@10 | Hit@10 | MRR | nDCG@10 | latency_ms |
| --- | --- | --- | --- | --- | --- |
| B1 BM25 | 0.0000 | 0.0000 | 0.0909 | 0.0000 | 132.6290 |
| B2 vector | 0.0000 | 0.0000 | 0.0909 | 0.0000 | 121.3827 |
| B3 postfilter | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 4.8377 |
| B4 prefilter | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 17.0538 |
| B5 hybrid | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 148.7100 |

Top-5 results for B2 vector:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:CAP_DATA:VRU_30 | 0.8337 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian is drunk; prevention_method=Pedestrians should avoid walking on busy roads while... | The incident occurs at night under clear and dry weather conditions on a straight, two-lane asphalt road marked with pedestrian crossing signs and supporting two-way traffic. A male pedestrian, dressed in blue, stands... |
| 2 | N | vru_accident:CAP_DATA:VRU_56 | 0.8337 | accident_type=ego-car hits a pedestrian; location=urban; road_type=intersection; weather_light=rainy day; accident_reason=Ego-car does not notice the pedestrians when turning; prevention_method=The speed of ego-cars s... | The pedestrian, an adult male dressed in dark clothing and wearing white shoes, is standing in the middle of a marked crosswalk on a dry, multi-lane urban asphalt road at night, illuminated by artificial street lighti... |
| 3 | N | vru_accident:CAP_DATA:VRU_57 | 0.8337 | accident_type=ego-car hits a pedestrian; location=highway; road_type=arterials; weather_light=cloudy day; accident_reason=Ego-car is out of control; prevention_method=Ego-cars should avoid speeding in adverse weather... | The incident occurs on a multi-lane divided highway equipped with metal guardrails, under clear and dry weather conditions with light traffic. Several workers wearing bright orange high-visibility coveralls are standi... |
| 4 | N | vru_accident:CAP_DATA:VRU_58 | 0.8337 | accident_type=ego-car hits a pedestrian; location=rural; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian moves or stays on the road; prevention_method=Pedestrians should follow traffic rules | On a very dark night, a collision occurs on a two-lane asphalt road with dry surface conditions. A pedestrian, dressed in dark clothing, is seen standing on the roadway. A metal guardrail lines the right side of the r... |
| 5 | N | vru_accident:CAP_DATA:VRU_59 | 0.8337 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian moves or stays on the road; prevention_method=Pedestrians should follow traffic rules | The incident occurs at night on a two-lane road surrounded by mountainous terrain, with clear weather and dry road conditions. The vehicle's headlights illuminate the surrounding area. The incident vehicle begins trav... |


Top-5 results for B4 prefilter:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:DADA_2000:VRU_56 | 0.8337 | accident_type=ego-car hits a pedestrian; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=Ego-car does not notice the pedestrians when turning; prevention_method=The speed of ego-cars sho... | On a clear day with dry asphalt surface at a multi-lane urban road intersection, a vehicle equipped with a dashcam travels straight ahead at approximately moderate speed. Several pedestrians and cyclists are on the ri... |
| 2 | Y | vru_accident:DADA_2000:VRU_57 | 0.8337 | accident_type=ego-car hits a pedestrian; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=Pedestrian didn't follow traffic rules.; prevention_method=Pedestrians should always use crosswal... | On an overcast day with dry conditions, a narrow two-lane asphalt road runs through a parking area adjacent to commercial or institutional buildings. A vehicle, moving at low to moderate speed, approaches straight in... |
| 3 | Y | vru_accident:DADA_2000:VRU_58 | 0.8337 | accident_type=ego-car hits a pedestrian; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=Ego-car does not notice the pedestrians when turning; prevention_method=The speed of ego-cars sho... | The incident occurs on a dry, urban two-way asphalt road with marked pedestrian crosswalks, under overcast sky conditions suggesting low light but no precipitation. A motor vehicle, traveling straight at an estimated... |
| 4 | Y | vru_accident:DADA_2000:VRU_59 | 0.8337 | accident_type=ego-car hits a pedestrian; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=Ego-car driver is in distracted driving; prevention_method=Since the accident was caused by drive... | On a clear day near a residential area, the vehicle passes through a gate and attempts to enter the roadway. In the vicinity, one pedestrian and one motorcyclist are observed crossing a T-intersection diagonally. Whil... |
| 5 | Y | vru_accident:MANUAL_DATA:VRU_100 | 0.8337 | accident_type=ego-car hits a pedestrian; location=urban; road_type=T-junction; weather_light=snowy day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Ego-cars should reduce... | This scene unfolds on a cloudy day in a narrow, snow-covered residential area of the city, with parked vehicles and tall apartment buildings lining both sides of the road. The road surface appears icy and slippery. Th... |


Top-5 results for B5 hybrid:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:DADA_2000:VRU_56 | 0.0328 | accident_type=ego-car hits a pedestrian; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=Ego-car does not notice the pedestrians when turning; prevention_method=The speed of ego-cars sho... | On a clear day with dry asphalt surface at a multi-lane urban road intersection, a vehicle equipped with a dashcam travels straight ahead at approximately moderate speed. Several pedestrians and cyclists are on the ri... |
| 2 | Y | vru_accident:DADA_2000:VRU_57 | 0.0323 | accident_type=ego-car hits a pedestrian; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=Pedestrian didn't follow traffic rules.; prevention_method=Pedestrians should always use crosswal... | On an overcast day with dry conditions, a narrow two-lane asphalt road runs through a parking area adjacent to commercial or institutional buildings. A vehicle, moving at low to moderate speed, approaches straight in... |
| 3 | Y | vru_accident:DADA_2000:VRU_58 | 0.0317 | accident_type=ego-car hits a pedestrian; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=Ego-car does not notice the pedestrians when turning; prevention_method=The speed of ego-cars sho... | The incident occurs on a dry, urban two-way asphalt road with marked pedestrian crosswalks, under overcast sky conditions suggesting low light but no precipitation. A motor vehicle, traveling straight at an estimated... |
| 4 | Y | vru_accident:DADA_2000:VRU_59 | 0.0312 | accident_type=ego-car hits a pedestrian; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=Ego-car driver is in distracted driving; prevention_method=Since the accident was caused by drive... | On a clear day near a residential area, the vehicle passes through a gate and attempts to enter the roadway. In the vicinity, one pedestrian and one motorcyclist are observed crossing a T-intersection diagonally. Whil... |
| 5 | Y | vru_accident:MANUAL_DATA:VRU_100 | 0.0308 | accident_type=ego-car hits a pedestrian; location=urban; road_type=T-junction; weather_light=snowy day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Ego-cars should reduce... | This scene unfolds on a cloudy day in a narrow, snow-covered residential area of the city, with parked vehicles and tall apartment buildings lining both sides of the road. The road surface appears icy and slippery. Th... |


### prefilter_beats_postfilter #1: `vru:medium:0149`

B4 searches inside the filtered candidate set and outperforms B3 post-filtering.

- difficulty: `medium`
- positives: `3`
- query: Find videos recorded in rainy night where the accident type is car hits pedestrian.
- semantic_filter: `{"accident_type": "car hits pedestrian"}`
- metadata_filter: `{"weather_light": "rainy night"}`

Metrics:

| strategy | R@10 | Hit@10 | MRR | nDCG@10 | latency_ms |
| --- | --- | --- | --- | --- | --- |
| B1 BM25 | 1.0000 | 1.0000 | 0.2500 | 0.5401 | 124.0125 |
| B2 vector | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 115.4490 |
| B3 postfilter | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 4.7699 |
| B4 prefilter | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.1195 |
| B5 hybrid | 1.0000 | 1.0000 | 1.0000 | 0.9060 | 123.7878 |

Top-5 results for B2 vector:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:CAP_DATA:VRU_176 | 0.7611 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians should always look... | A male pedestrian, dressed in a dark jacket and dark pants, is crossing a dry, multi-lane urban asphalt road on a clear day, moving toward the left sidewalk. His path is nearly perpendicular to the direction of traffi... |
| 2 | N | vru_accident:CAP_DATA:VRU_179 | 0.7611 | accident_type=car hits pedestrian; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=vehicles drive too fast with short braking distance; prevention_method=Drivers should obey speed limits | This scene takes place at a pedestrian crosswalk on a flat, dry asphalt road under clear weather conditions, with autumn foliage visible in the background. A white minibus is traveling straight from the left side of t... |
| 3 | N | vru_accident:CAP_DATA:VRU_180 | 0.7611 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down and y... | A male pedestrian, dressed in a dark jacket, dark pants, and a dark cap, is involved in a traffic accident on a dry, two-way urban asphalt road during clear daytime conditions. The road features a marked zebra crossin... |
| 4 | N | vru_accident:CAP_DATA:VRU_181 | 0.7611 | accident_type=car hits pedestrian; location=urban; road_type=intersection; weather_light=snowy day; accident_reason=vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid high... | The road surface is slightly wet, with snow piled along the sidewalks. A young female pedestrian, dressed in dark clothing, is crossing a wide urban asphalt road using a marked crosswalk under overcast skies with clea... |
| 5 | N | vru_accident:DoTA:VRU_52 | 0.7611 | accident_type=car hits pedestrian; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=Vehicles do not notice the pedestrians when driving; prevention_method=Drivers should strictly follow t... | On a clear day with bright sunlight, a female pedestrian stands at the right edge of a dry, two-way asphalt road. She is wearing a light blue jacket, dark jeans, black shoes, and glasses, and carries an orange backpac... |


Top-5 results for B4 prefilter:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:MANUAL_DATA:VRU_143 | 0.7611 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=rainy night; accident_reason=Vehicles do not notice the pedestrians when driving; prevention_method=Vehicles should avoid high spee... | The pedestrian, an adult male dressed in a dark jacket and jeans pants, advances briskly across a wet, multi-lane urban asphalt road at night under streetlights and rainy conditions, carrying a light-colored bag in hi... |
| 2 | Y | vru_accident:MANUAL_DATA:VRU_205 | 0.7611 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=rainy night; accident_reason=vehicles drive too fast with short braking distance; prevention_method=Drivers should slow down and yi... | The pedestrian, an adult female wearing a dark jacket and light-colored pants, is seen crossing a wet, multi-lane urban roadway under low-light, rainy conditions at dusk. The road surface is visibly slick, and streetl... |
| 3 | Y | vru_accident:MANUAL_DATA:VRU_93 | 0.7611 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=rainy night; accident_reason=Pedestrians didn't follow traffic rules; prevention_method=Vehicles should reduce speed when their vis... | This scene takes place at night on a multi-lane urban asphalt road illuminated by streetlights. Raindrops on the windshield of the recording vehicle indicate that it is raining, and the road surface appears slippery.... |
| 4 | N | vru_accident:DADA_2000:VRU_194 | 0.6853 | accident_type=car hits cyclist; location=urban; road_type=intersection; weather_light=rainy night; accident_reason=vehicles drive too fast with short braking distance; prevention_method=Cyclist should follow traffic r... | The incident occurs at night on a wet, multi-lane asphalt urban road controlled by traffic lights, under street lamps on a rainy evening. A red taxi is moving on the left lane near a curb with greenery. The cyclist, h... |
| 5 | N | vru_accident:MANUAL_DATA:VRU_260 | 0.6473 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=arterials; weather_light=rainy night; accident_reason=Pedestrians didn't follow traffic rules; prevention_method=Drivers should slow down whe... | On a clear day with dry weather and good visibility, the incident occurs on a flat, asphalt-paved two-way urban road with no marked pedestrian crossings. The male pedestrian, appearing to be in his late 20s to early 3... |


Top-5 results for B5 hybrid:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:MANUAL_DATA:VRU_143 | 0.0325 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=rainy night; accident_reason=Vehicles do not notice the pedestrians when driving; prevention_method=Vehicles should avoid high spee... | The pedestrian, an adult male dressed in a dark jacket and jeans pants, advances briskly across a wet, multi-lane urban asphalt road at night under streetlights and rainy conditions, carrying a light-colored bag in hi... |
| 2 | N | vru_accident:DADA_2000:VRU_194 | 0.0320 | accident_type=car hits cyclist; location=urban; road_type=intersection; weather_light=rainy night; accident_reason=vehicles drive too fast with short braking distance; prevention_method=Cyclist should follow traffic r... | The incident occurs at night on a wet, multi-lane asphalt urban road controlled by traffic lights, under street lamps on a rainy evening. A red taxi is moving on the left lane near a curb with greenery. The cyclist, h... |
| 3 | Y | vru_accident:MANUAL_DATA:VRU_205 | 0.0320 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=rainy night; accident_reason=vehicles drive too fast with short braking distance; prevention_method=Drivers should slow down and yi... | The pedestrian, an adult female wearing a dark jacket and light-colored pants, is seen crossing a wet, multi-lane urban roadway under low-light, rainy conditions at dusk. The road surface is visibly slick, and streetl... |
| 4 | Y | vru_accident:MANUAL_DATA:VRU_93 | 0.0313 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=rainy night; accident_reason=Pedestrians didn't follow traffic rules; prevention_method=Vehicles should reduce speed when their vis... | This scene takes place at night on a multi-lane urban asphalt road illuminated by streetlights. Raindrops on the windshield of the recording vehicle indicate that it is raining, and the road surface appears slippery.... |
| 5 | N | vru_accident:MANUAL_DATA:VRU_260 | 0.0310 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=arterials; weather_light=rainy night; accident_reason=Pedestrians didn't follow traffic rules; prevention_method=Drivers should slow down whe... | On a clear day with dry weather and good visibility, the incident occurs on a flat, asphalt-paved two-way urban road with no marked pedestrian crossings. The male pedestrian, appearing to be in his late 20s to early 3... |


### prefilter_beats_postfilter #2: `vru:strong:0200`

B4 searches inside the filtered candidate set and outperforms B3 post-filtering.

- difficulty: `strong`
- positives: `3`
- query: Find rainy night urban accident videos on arterials roads where the accident type is car hits pedestrian.
- semantic_filter: `{"accident_type": "car hits pedestrian"}`
- metadata_filter: `{"location": "urban", "road_type": "arterials", "weather_light": "rainy night"}`

Metrics:

| strategy | R@10 | Hit@10 | MRR | nDCG@10 | latency_ms |
| --- | --- | --- | --- | --- | --- |
| B1 BM25 | 1.0000 | 1.0000 | 0.5000 | 0.7123 | 123.3205 |
| B2 vector | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 113.1300 |
| B3 postfilter | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 4.9629 |
| B4 prefilter | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.1139 |
| B5 hybrid | 1.0000 | 1.0000 | 1.0000 | 0.9675 | 123.0453 |

Top-5 results for B2 vector:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:CAP_DATA:VRU_176 | 0.7255 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians should always look... | A male pedestrian, dressed in a dark jacket and dark pants, is crossing a dry, multi-lane urban asphalt road on a clear day, moving toward the left sidewalk. His path is nearly perpendicular to the direction of traffi... |
| 2 | N | vru_accident:CAP_DATA:VRU_179 | 0.7255 | accident_type=car hits pedestrian; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=vehicles drive too fast with short braking distance; prevention_method=Drivers should obey speed limits | This scene takes place at a pedestrian crosswalk on a flat, dry asphalt road under clear weather conditions, with autumn foliage visible in the background. A white minibus is traveling straight from the left side of t... |
| 3 | N | vru_accident:CAP_DATA:VRU_180 | 0.7255 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down and y... | A male pedestrian, dressed in a dark jacket, dark pants, and a dark cap, is involved in a traffic accident on a dry, two-way urban asphalt road during clear daytime conditions. The road features a marked zebra crossin... |
| 4 | N | vru_accident:CAP_DATA:VRU_181 | 0.7255 | accident_type=car hits pedestrian; location=urban; road_type=intersection; weather_light=snowy day; accident_reason=vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid high... | The road surface is slightly wet, with snow piled along the sidewalks. A young female pedestrian, dressed in dark clothing, is crossing a wide urban asphalt road using a marked crosswalk under overcast skies with clea... |
| 5 | N | vru_accident:DoTA:VRU_52 | 0.7255 | accident_type=car hits pedestrian; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=Vehicles do not notice the pedestrians when driving; prevention_method=Drivers should strictly follow t... | On a clear day with bright sunlight, a female pedestrian stands at the right edge of a dry, two-way asphalt road. She is wearing a light blue jacket, dark jeans, black shoes, and glasses, and carries an orange backpac... |


Top-5 results for B4 prefilter:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:MANUAL_DATA:VRU_143 | 0.7255 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=rainy night; accident_reason=Vehicles do not notice the pedestrians when driving; prevention_method=Vehicles should avoid high spee... | The pedestrian, an adult male dressed in a dark jacket and jeans pants, advances briskly across a wet, multi-lane urban asphalt road at night under streetlights and rainy conditions, carrying a light-colored bag in hi... |
| 2 | Y | vru_accident:MANUAL_DATA:VRU_205 | 0.7255 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=rainy night; accident_reason=vehicles drive too fast with short braking distance; prevention_method=Drivers should slow down and yi... | The pedestrian, an adult female wearing a dark jacket and light-colored pants, is seen crossing a wet, multi-lane urban roadway under low-light, rainy conditions at dusk. The road surface is visibly slick, and streetl... |
| 3 | Y | vru_accident:MANUAL_DATA:VRU_93 | 0.7255 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=rainy night; accident_reason=Pedestrians didn't follow traffic rules; prevention_method=Vehicles should reduce speed when their vis... | This scene takes place at night on a multi-lane urban asphalt road illuminated by streetlights. Raindrops on the windshield of the recording vehicle indicate that it is raining, and the road surface appears slippery.... |
| 4 | N | vru_accident:MANUAL_DATA:VRU_260 | 0.6529 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=arterials; weather_light=rainy night; accident_reason=Pedestrians didn't follow traffic rules; prevention_method=Drivers should slow down whe... | On a clear day with dry weather and good visibility, the incident occurs on a flat, asphalt-paved two-way urban road with no marked pedestrian crossings. The male pedestrian, appearing to be in his late 20s to early 3... |


Top-5 results for B5 hybrid:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:MANUAL_DATA:VRU_143 | 0.0328 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=rainy night; accident_reason=Vehicles do not notice the pedestrians when driving; prevention_method=Vehicles should avoid high spee... | The pedestrian, an adult male dressed in a dark jacket and jeans pants, advances briskly across a wet, multi-lane urban asphalt road at night under streetlights and rainy conditions, carrying a light-colored bag in hi... |
| 2 | Y | vru_accident:MANUAL_DATA:VRU_205 | 0.0323 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=rainy night; accident_reason=vehicles drive too fast with short braking distance; prevention_method=Drivers should slow down and yi... | The pedestrian, an adult female wearing a dark jacket and light-colored pants, is seen crossing a wet, multi-lane urban roadway under low-light, rainy conditions at dusk. The road surface is visibly slick, and streetl... |
| 3 | N | vru_accident:MANUAL_DATA:VRU_260 | 0.0315 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=arterials; weather_light=rainy night; accident_reason=Pedestrians didn't follow traffic rules; prevention_method=Drivers should slow down whe... | On a clear day with dry weather and good visibility, the incident occurs on a flat, asphalt-paved two-way urban road with no marked pedestrian crossings. The male pedestrian, appearing to be in his late 20s to early 3... |
| 4 | Y | vru_accident:MANUAL_DATA:VRU_93 | 0.0315 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=rainy night; accident_reason=Pedestrians didn't follow traffic rules; prevention_method=Vehicles should reduce speed when their vis... | This scene takes place at night on a multi-lane urban asphalt road illuminated by streetlights. Raindrops on the windshield of the recording vehicle indicate that it is raining, and the road surface appears slippery.... |


### prefilter_beats_postfilter #3: `vru:strong:0199`

B4 searches inside the filtered candidate set and outperforms B3 post-filtering.

- difficulty: `strong`
- positives: `3`
- query: Find rainy day urban accident videos on T-junction roads where the accident type is car hits pedestrian.
- semantic_filter: `{"accident_type": "car hits pedestrian"}`
- metadata_filter: `{"location": "urban", "road_type": "T-junction", "weather_light": "rainy day"}`

Metrics:

| strategy | R@10 | Hit@10 | MRR | nDCG@10 | latency_ms |
| --- | --- | --- | --- | --- | --- |
| B1 BM25 | 0.0000 | 0.0000 | 0.0250 | 0.0000 | 164.0320 |
| B2 vector | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 149.3539 |
| B3 postfilter | 0.3333 | 1.0000 | 1.0000 | 0.4693 | 5.8160 |
| B4 prefilter | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.3620 |
| B5 hybrid | 1.0000 | 1.0000 | 1.0000 | 0.9060 | 129.9939 |

Top-5 results for B2 vector:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:CAP_DATA:VRU_176 | 0.7151 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians should always look... | A male pedestrian, dressed in a dark jacket and dark pants, is crossing a dry, multi-lane urban asphalt road on a clear day, moving toward the left sidewalk. His path is nearly perpendicular to the direction of traffi... |
| 2 | N | vru_accident:CAP_DATA:VRU_179 | 0.7151 | accident_type=car hits pedestrian; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=vehicles drive too fast with short braking distance; prevention_method=Drivers should obey speed limits | This scene takes place at a pedestrian crosswalk on a flat, dry asphalt road under clear weather conditions, with autumn foliage visible in the background. A white minibus is traveling straight from the left side of t... |
| 3 | N | vru_accident:CAP_DATA:VRU_180 | 0.7151 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down and y... | A male pedestrian, dressed in a dark jacket, dark pants, and a dark cap, is involved in a traffic accident on a dry, two-way urban asphalt road during clear daytime conditions. The road features a marked zebra crossin... |
| 4 | N | vru_accident:CAP_DATA:VRU_181 | 0.7151 | accident_type=car hits pedestrian; location=urban; road_type=intersection; weather_light=snowy day; accident_reason=vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid high... | The road surface is slightly wet, with snow piled along the sidewalks. A young female pedestrian, dressed in dark clothing, is crossing a wide urban asphalt road using a marked crosswalk under overcast skies with clea... |
| 5 | N | vru_accident:DoTA:VRU_52 | 0.7151 | accident_type=car hits pedestrian; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=Vehicles do not notice the pedestrians when driving; prevention_method=Drivers should strictly follow t... | On a clear day with bright sunlight, a female pedestrian stands at the right edge of a dry, two-way asphalt road. She is wearing a light blue jacket, dark jeans, black shoes, and glasses, and carries an orange backpac... |


Top-5 results for B4 prefilter:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:DADA_2000:VRU_154 | 0.7151 | accident_type=car hits pedestrian; location=urban; road_type=T-junction; weather_light=rainy day; accident_reason=vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid high sp... | The pedestrian, a female wearing a white top, dark shorts, and white shoes, is standing at the edge of a wet asphalt urban road near a crosswalk on a rainy, overcast morning. The road is two-way with moderate traffic,... |
| 2 | Y | vru_accident:MANUAL_DATA:VRU_120 | 0.7151 | accident_type=car hits pedestrian; location=urban; road_type=T-junction; weather_light=rainy day; accident_reason=Driver's vision was blokced; prevention_method=Pedestrians should look both ways before crossing | The incident occurred on a two-way residential road without clear lane markings. The video was recorded in a neighborhood setting. A female pedestrian with blonde hair, wearing a black coat, appears from the right sid... |
| 3 | Y | vru_accident:MANUAL_DATA:VRU_242 | 0.7151 | accident_type=car hits pedestrian; location=urban; road_type=T-junction; weather_light=rainy day; accident_reason=Driver's vision was blocked or blurred when driving; prevention_method=Drivers should slow down when th... | The pedestrian, a male dressed in dark clothing including a hooded jacket and pants, stands at the right edge of a multi-lane wet asphalt urban road on an overcast day, with some residual snow along the roadside. He i... |
| 4 | N | vru_accident:CAP_DATA:VRU_244 | 0.6911 | accident_type=car hits cyclist; location=urban; road_type=T-junction; weather_light=rainy day; accident_reason=vehicles do not notice the cyclists when turning or...; prevention_method=The vehicles should decrease the... | This scene depicts a traffic accident occurring at a T-shaped urban asphalt intersection under rainy and overcast weather conditions. The intersection is multi-lane and experiences moderate traffic flow. A male cyclis... |


Top-5 results for B5 hybrid:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:DADA_2000:VRU_154 | 0.0325 | accident_type=car hits pedestrian; location=urban; road_type=T-junction; weather_light=rainy day; accident_reason=vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid high sp... | The pedestrian, a female wearing a white top, dark shorts, and white shoes, is standing at the edge of a wet asphalt urban road near a crosswalk on a rainy, overcast morning. The road is two-way with moderate traffic,... |
| 2 | N | vru_accident:CAP_DATA:VRU_244 | 0.0320 | accident_type=car hits cyclist; location=urban; road_type=T-junction; weather_light=rainy day; accident_reason=vehicles do not notice the cyclists when turning or...; prevention_method=The vehicles should decrease the... | This scene depicts a traffic accident occurring at a T-shaped urban asphalt intersection under rainy and overcast weather conditions. The intersection is multi-lane and experiences moderate traffic flow. A male cyclis... |
| 3 | Y | vru_accident:MANUAL_DATA:VRU_120 | 0.0320 | accident_type=car hits pedestrian; location=urban; road_type=T-junction; weather_light=rainy day; accident_reason=Driver's vision was blokced; prevention_method=Pedestrians should look both ways before crossing | The incident occurred on a two-way residential road without clear lane markings. The video was recorded in a neighborhood setting. A female pedestrian with blonde hair, wearing a black coat, appears from the right sid... |
| 4 | Y | vru_accident:MANUAL_DATA:VRU_242 | 0.0315 | accident_type=car hits pedestrian; location=urban; road_type=T-junction; weather_light=rainy day; accident_reason=Driver's vision was blocked or blurred when driving; prevention_method=Drivers should slow down when th... | The pedestrian, a male dressed in dark clothing including a hooded jacket and pants, stands at the right edge of a multi-lane wet asphalt urban road on an overcast day, with some residual snow along the roadside. He i... |


### hybrid_beats_prefilter #1: `vru:weak:0029`

B5 hybrid gains over B4, usually when lexical evidence complements dense retrieval.

- difficulty: `weak`
- positives: `25`
- query: Find accidents caused by: vehicles do not notice the pedestrians when turning or changling lanes.
- semantic_filter: `{"accident_reason": "vehicles do not notice the pedestrians when turning or changling lanes"}`
- metadata_filter: `{}`

Metrics:

| strategy | R@10 | Hit@10 | MRR | nDCG@10 | latency_ms |
| --- | --- | --- | --- | --- | --- |
| B1 BM25 | 0.4000 | 1.0000 | 1.0000 | 1.0000 | 126.9747 |
| B2 vector | 0.0000 | 0.0000 | 0.0769 | 0.0000 | 115.6111 |
| B3 postfilter | 0.0000 | 0.0000 | 0.0769 | 0.0000 | 4.8758 |
| B4 prefilter | 0.0000 | 0.0000 | 0.0769 | 0.0000 | 146.0078 |
| B5 hybrid | 0.4000 | 1.0000 | 1.0000 | 1.0000 | 270.1438 |

Top-5 results for B2 vector:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:DoTA:VRU_90 | 0.9004 | accident_type=car hits pedestrian; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=Vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid high sp... | The pedestrian, an adult female wearing a light pink coat and dark-colored pants, is walking through a dry urban parking lot under partly cloudy skies, where a pedestrian crossing sign is visible. After stepping off t... |
| 2 | N | vru_accident:DoTA:VRU_99 | 0.9004 | accident_type=car hits pedestrian; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid high... | The adult pedestrian, dressed in a black jacket and dark pants, begins crossing a dry, multi-lane urban asphalt roadway at a signal-controlled intersection under overcast skies with moderate natural light and normal t... |
| 3 | N | vru_accident:MANUAL_DATA:VRU_140 | 0.9004 | accident_type=car hits pedestrian; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=Vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid high sp... | The incident appears to have taken place in a parking lot, where both parked and moving vehicles are visible, along with several pedestrians walking in the area. A pedestrian wearing a light pink jacket, black pants,... |
| 4 | N | vru_accident:MANUAL_DATA:VRU_183 | 0.9004 | accident_type=car hits pedestrian; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Vehicles do not notice the pedestrians when turning...; prevention_method=Drivers should slow down an... | The scene takes place on a dry, urban asphalt road with a clear sky and good visibility. Several pedestrians, including a female wearing a white jacket and khaki pants, are walking across a marked crosswalk from the r... |
| 5 | N | vru_accident:MANUAL_DATA:VRU_210 | 0.9004 | accident_type=car hits pedestrian; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid high... | The pedestrian, a young male wearing a dark jacket and dark pants, is seen standing at the curb of a multi-lane urban intersection with dry asphalt under overcast skies. Positioned near a pedestrian crossing sign and... |


Top-5 results for B4 prefilter:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:DoTA:VRU_90 | 0.9004 | accident_type=car hits pedestrian; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=Vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid high sp... | The pedestrian, an adult female wearing a light pink coat and dark-colored pants, is walking through a dry urban parking lot under partly cloudy skies, where a pedestrian crossing sign is visible. After stepping off t... |
| 2 | N | vru_accident:DoTA:VRU_99 | 0.9004 | accident_type=car hits pedestrian; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid high... | The adult pedestrian, dressed in a black jacket and dark pants, begins crossing a dry, multi-lane urban asphalt roadway at a signal-controlled intersection under overcast skies with moderate natural light and normal t... |
| 3 | N | vru_accident:MANUAL_DATA:VRU_140 | 0.9004 | accident_type=car hits pedestrian; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=Vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid high sp... | The incident appears to have taken place in a parking lot, where both parked and moving vehicles are visible, along with several pedestrians walking in the area. A pedestrian wearing a light pink jacket, black pants,... |
| 4 | N | vru_accident:MANUAL_DATA:VRU_183 | 0.9004 | accident_type=car hits pedestrian; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Vehicles do not notice the pedestrians when turning...; prevention_method=Drivers should slow down an... | The scene takes place on a dry, urban asphalt road with a clear sky and good visibility. Several pedestrians, including a female wearing a white jacket and khaki pants, are walking across a marked crosswalk from the r... |
| 5 | N | vru_accident:MANUAL_DATA:VRU_210 | 0.9004 | accident_type=car hits pedestrian; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid high... | The pedestrian, a young male wearing a dark jacket and dark pants, is seen standing at the curb of a multi-lane urban intersection with dry asphalt under overcast skies. Positioned near a pedestrian crossing sign and... |


Top-5 results for B5 hybrid:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:CAP_DATA:VRU_106 | 0.0301 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid high spe... | This scene takes place during an overcast daytime period on a multi-lane urban asphalt road with a slightly damp surface. Traffic flow is moderate, and visibility is clear under the given conditions. A female pedestri... |
| 2 | Y | vru_accident:CAP_DATA:VRU_145 | 0.0296 | accident_type=car hits pedestrian; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid high... | An adult male pedestrian, dressed in a dark jacket and dark trousers, is crossing a wide, multi-lane urban intersection paved with dry asphalt under overcast skies. The road features clearly marked pedestrian crosswal... |
| 3 | Y | vru_accident:CAP_DATA:VRU_162 | 0.0292 | accident_type=car hits pedestrian; location=rural; road_type=T-junction; weather_light=snowy day; accident_reason=vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid high sp... | On an overcast day at a T-shaped intersection, unmelted snow is piled along both sides of the road, and the road surface is slippery due to partially melted snow. A pedestrian dressed in dark clothing attempts to cros... |
| 4 | Y | vru_accident:CAP_DATA:VRU_164 | 0.0288 | accident_type=car hits pedestrian; location=rural; road_type=intersection; weather_light=sunny day; accident_reason=vehicles do not notice the pedestrians when turning...; prevention_method=All drivers should rely sol... | On a clear day at a T-shaped intersection, the road is wet, and an accident occurs. Two male pedestrians?one wearing a white top and black pants, and the other wearing a purple hoodie with the hood up?are crossing the... |
| 5 | Y | vru_accident:CAP_DATA:VRU_181 | 0.0284 | accident_type=car hits pedestrian; location=urban; road_type=intersection; weather_light=snowy day; accident_reason=vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid high... | The road surface is slightly wet, with snow piled along the sidewalks. A young female pedestrian, dressed in dark clothing, is crossing a wide urban asphalt road using a marked crosswalk under overcast skies with clea... |


### hybrid_beats_prefilter #2: `vru:strong:0192`

B5 hybrid gains over B4, usually when lexical evidence complements dense retrieval.

- difficulty: `strong`
- positives: `5`
- query: Find sunny day urban accident videos on intersection roads where the accident type is motorbike hits cyclist.
- semantic_filter: `{"accident_type": "motorbike hits cyclist"}`
- metadata_filter: `{"location": "urban", "road_type": "intersection", "weather_light": "sunny day"}`

Metrics:

| strategy | R@10 | Hit@10 | MRR | nDCG@10 | latency_ms |
| --- | --- | --- | --- | --- | --- |
| B1 BM25 | 1.0000 | 1.0000 | 0.5000 | 0.7142 | 146.4673 |
| B2 vector | 0.8000 | 1.0000 | 0.2500 | 0.4869 | 116.8473 |
| B3 postfilter | 1.0000 | 1.0000 | 0.3333 | 0.6807 | 4.9090 |
| B4 prefilter | 1.0000 | 1.0000 | 0.3333 | 0.6807 | 25.8606 |
| B5 hybrid | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 168.8744 |

Top-5 results for B2 vector:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:MANUAL_DATA:VRU_28 | 0.7350 | accident_type=motorcycle hits a cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Motorcycle driver is inattentive; prevention_method=Drivers should obey speed limits | On a clear and sunny day, a motorcyclist wearing a dark jacket and helmet was riding along a dry, multi-lane asphalt road. As the motorcyclist passed through an intersection, a black SUV ahead began changing lanes fro... |
| 2 | N | vru_accident:DADA_2000:VRU_222 | 0.7311 | accident_type=motorcycle hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=The cyclist' vision is blocked, and there is no time...; prevention_method=Cyclists should stay a... | The scene depicts an urban three-lane asphalt road on a cloudy day with dry weather conditions. A male cyclist, dressed in a light blue and black short sleeve shirt, dark pants, and carrying a black backpack, rides a... |
| 3 | N | vru_accident:DADA_2000:VRU_101 | 0.7287 | accident_type=motorbike hits cyclist; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=The motorcycle decelerates or stops suddenly; prevention_method=Motorcyclists should follow traffic r... | The video sequence captures an incident occurring on a dry urban asphalt road beneath an elevated highway with multiple stacked overpasses visible in the background. The time is late afternoon in clear weather conditi... |
| 4 | Y | vru_accident:DADA_2000:VRU_102 | 0.7287 | accident_type=motorbike hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Motorcycle drives too fast with a short braking dist...; prevention_method=The motorcycle shall no... | The scene unfolds on a dry, broad urban asphalt road with wide road and visible zebra crossings under a cloudy sky during daytime. The scene is filled with numerous bicycles, motorcycles, and vehicles coming into view... |
| 5 | N | vru_accident:DADA_2000:VRU_103 | 0.7287 | accident_type=motorbike hits cyclist; location=urban; road_type=curve; weather_light=sunny day; accident_reason=Motorcycle does not notice the other cyclists; prevention_method=The motorcycle driver should carefully l... | A male dressed in a dark jacket and dark pants, is initially seen riding a motorcycle along the right side of a dry, straight two-lane road bordered by a low concrete wall and urban buildings on a clear day. While rid... |


Top-5 results for B4 prefilter:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:MANUAL_DATA:VRU_28 | 0.7350 | accident_type=motorcycle hits a cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Motorcycle driver is inattentive; prevention_method=Drivers should obey speed limits | On a clear and sunny day, a motorcyclist wearing a dark jacket and helmet was riding along a dry, multi-lane asphalt road. As the motorcyclist passed through an intersection, a black SUV ahead began changing lanes fro... |
| 2 | N | vru_accident:DADA_2000:VRU_222 | 0.7311 | accident_type=motorcycle hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=The cyclist' vision is blocked, and there is no time...; prevention_method=Cyclists should stay a... | The scene depicts an urban three-lane asphalt road on a cloudy day with dry weather conditions. A male cyclist, dressed in a light blue and black short sleeve shirt, dark pants, and carrying a black backpack, rides a... |
| 3 | Y | vru_accident:DADA_2000:VRU_104 | 0.7287 | accident_type=motorbike hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=The motorcycle decelerates or stops suddenly; prevention_method=Motorcyclists should follow traffi... | The scene depicts a busy urban intersection on a dry asphalt road under overcast daylight conditions. A large number of motorcycles, bicycles, and pedestrians are crossing the crosswalk during a green signal. One cycl... |
| 4 | Y | vru_accident:DADA_2000:VRU_105 | 0.7287 | accident_type=motorbike hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=The motorcycle's vision is blocked or blurred, and t...; prevention_method=The motorcycle slows do... | The scene depicts an urban three-lane asphalt road on a cloudy day with dry weather conditions. A male cyclist, dressed in a light blue and black short sleeve shirt, dark pants, and carrying a black backpack, rides a... |
| 5 | Y | vru_accident:DADA_2000:VRU_106 | 0.7287 | accident_type=motorbike hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Motorcycle drives too fast with a short braking dist...; prevention_method=The motorcycle shall no... | On a bright and clear day, a narrow, dry asphalt residential road with one lane and parked vehicles along the right side is observed. A female cyclist, dressed in a dark outfit and wearing a white wide-brimmed hat, pe... |


Top-5 results for B5 hybrid:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:DADA_2000:VRU_104 | 0.0320 | accident_type=motorbike hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=The motorcycle decelerates or stops suddenly; prevention_method=Motorcyclists should follow traffi... | The scene depicts a busy urban intersection on a dry asphalt road under overcast daylight conditions. A large number of motorcycles, bicycles, and pedestrians are crossing the crosswalk during a green signal. One cycl... |
| 2 | Y | vru_accident:DADA_2000:VRU_105 | 0.0315 | accident_type=motorbike hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=The motorcycle's vision is blocked or blurred, and t...; prevention_method=The motorcycle slows do... | The scene depicts an urban three-lane asphalt road on a cloudy day with dry weather conditions. A male cyclist, dressed in a light blue and black short sleeve shirt, dark pants, and carrying a black backpack, rides a... |
| 3 | Y | vru_accident:DADA_2000:VRU_102 | 0.0313 | accident_type=motorbike hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Motorcycle drives too fast with a short braking dist...; prevention_method=The motorcycle shall no... | The scene unfolds on a dry, broad urban asphalt road with wide road and visible zebra crossings under a cloudy sky during daytime. The scene is filled with numerous bicycles, motorcycles, and vehicles coming into view... |
| 4 | Y | vru_accident:DADA_2000:VRU_106 | 0.0310 | accident_type=motorbike hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Motorcycle drives too fast with a short braking dist...; prevention_method=The motorcycle shall no... | On a bright and clear day, a narrow, dry asphalt residential road with one lane and parked vehicles along the right side is observed. A female cyclist, dressed in a dark outfit and wearing a white wide-brimmed hat, pe... |
| 5 | Y | vru_accident:DADA_2000:VRU_109 | 0.0305 | accident_type=motorbike hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Cyclist brakes emergently; prevention_method=Cyclists should keep abreast of road conditions whil... | On a clear day with dry asphalt at a multi-lane urban intersection controlled by traffic signals currently showing red, a cyclist waits near the pedestrian crosswalk on the right side of the driver's perspective. Whil... |


### hybrid_beats_prefilter #3: `vru:medium:0062`

B5 hybrid gains over B4, usually when lexical evidence complements dense retrieval.

- difficulty: `medium`
- positives: `6`
- query: Find videos where the accident type is motorbike hits cyclist on a intersection road.
- semantic_filter: `{"accident_type": "motorbike hits cyclist"}`
- metadata_filter: `{"road_type": "intersection"}`

Metrics:

| strategy | R@10 | Hit@10 | MRR | nDCG@10 | latency_ms |
| --- | --- | --- | --- | --- | --- |
| B1 BM25 | 1.0000 | 1.0000 | 0.5000 | 0.7326 | 131.1514 |
| B2 vector | 1.0000 | 1.0000 | 0.3333 | 0.6556 | 120.4637 |
| B3 postfilter | 1.0000 | 1.0000 | 0.5000 | 0.7983 | 4.8845 |
| B4 prefilter | 1.0000 | 1.0000 | 0.5000 | 0.7983 | 30.2433 |
| B5 hybrid | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 160.2012 |

Top-5 results for B2 vector:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:MANUAL_DATA:VRU_28 | 0.8013 | accident_type=motorcycle hits a cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Motorcycle driver is inattentive; prevention_method=Drivers should obey speed limits | On a clear and sunny day, a motorcyclist wearing a dark jacket and helmet was riding along a dry, multi-lane asphalt road. As the motorcyclist passed through an intersection, a black SUV ahead began changing lanes fro... |
| 2 | N | vru_accident:DADA_2000:VRU_101 | 0.7999 | accident_type=motorbike hits cyclist; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=The motorcycle decelerates or stops suddenly; prevention_method=Motorcyclists should follow traffic r... | The video sequence captures an incident occurring on a dry urban asphalt road beneath an elevated highway with multiple stacked overpasses visible in the background. The time is late afternoon in clear weather conditi... |
| 3 | Y | vru_accident:DADA_2000:VRU_102 | 0.7999 | accident_type=motorbike hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Motorcycle drives too fast with a short braking dist...; prevention_method=The motorcycle shall no... | The scene unfolds on a dry, broad urban asphalt road with wide road and visible zebra crossings under a cloudy sky during daytime. The scene is filled with numerous bicycles, motorcycles, and vehicles coming into view... |
| 4 | N | vru_accident:DADA_2000:VRU_103 | 0.7999 | accident_type=motorbike hits cyclist; location=urban; road_type=curve; weather_light=sunny day; accident_reason=Motorcycle does not notice the other cyclists; prevention_method=The motorcycle driver should carefully l... | A male dressed in a dark jacket and dark pants, is initially seen riding a motorcycle along the right side of a dry, straight two-lane road bordered by a low concrete wall and urban buildings on a clear day. While rid... |
| 5 | Y | vru_accident:DADA_2000:VRU_104 | 0.7999 | accident_type=motorbike hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=The motorcycle decelerates or stops suddenly; prevention_method=Motorcyclists should follow traffi... | The scene depicts a busy urban intersection on a dry asphalt road under overcast daylight conditions. A large number of motorcycles, bicycles, and pedestrians are crossing the crosswalk during a green signal. One cycl... |


Top-5 results for B4 prefilter:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:MANUAL_DATA:VRU_28 | 0.8013 | accident_type=motorcycle hits a cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Motorcycle driver is inattentive; prevention_method=Drivers should obey speed limits | On a clear and sunny day, a motorcyclist wearing a dark jacket and helmet was riding along a dry, multi-lane asphalt road. As the motorcyclist passed through an intersection, a black SUV ahead began changing lanes fro... |
| 2 | Y | vru_accident:DADA_2000:VRU_102 | 0.7999 | accident_type=motorbike hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Motorcycle drives too fast with a short braking dist...; prevention_method=The motorcycle shall no... | The scene unfolds on a dry, broad urban asphalt road with wide road and visible zebra crossings under a cloudy sky during daytime. The scene is filled with numerous bicycles, motorcycles, and vehicles coming into view... |
| 3 | Y | vru_accident:DADA_2000:VRU_104 | 0.7999 | accident_type=motorbike hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=The motorcycle decelerates or stops suddenly; prevention_method=Motorcyclists should follow traffi... | The scene depicts a busy urban intersection on a dry asphalt road under overcast daylight conditions. A large number of motorcycles, bicycles, and pedestrians are crossing the crosswalk during a green signal. One cycl... |
| 4 | Y | vru_accident:DADA_2000:VRU_105 | 0.7999 | accident_type=motorbike hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=The motorcycle's vision is blocked or blurred, and t...; prevention_method=The motorcycle slows do... | The scene depicts an urban three-lane asphalt road on a cloudy day with dry weather conditions. A male cyclist, dressed in a light blue and black short sleeve shirt, dark pants, and carrying a black backpack, rides a... |
| 5 | Y | vru_accident:DADA_2000:VRU_106 | 0.7999 | accident_type=motorbike hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Motorcycle drives too fast with a short braking dist...; prevention_method=The motorcycle shall no... | On a bright and clear day, a narrow, dry asphalt residential road with one lane and parked vehicles along the right side is observed. A female cyclist, dressed in a dark outfit and wearing a white wide-brimmed hat, pe... |


Top-5 results for B5 hybrid:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:DADA_2000:VRU_102 | 0.0325 | accident_type=motorbike hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Motorcycle drives too fast with a short braking dist...; prevention_method=The motorcycle shall no... | The scene unfolds on a dry, broad urban asphalt road with wide road and visible zebra crossings under a cloudy sky during daytime. The scene is filled with numerous bicycles, motorcycles, and vehicles coming into view... |
| 2 | Y | vru_accident:DADA_2000:VRU_104 | 0.0320 | accident_type=motorbike hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=The motorcycle decelerates or stops suddenly; prevention_method=Motorcyclists should follow traffi... | The scene depicts a busy urban intersection on a dry asphalt road under overcast daylight conditions. A large number of motorcycles, bicycles, and pedestrians are crossing the crosswalk during a green signal. One cycl... |
| 3 | Y | vru_accident:DADA_2000:VRU_105 | 0.0315 | accident_type=motorbike hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=The motorcycle's vision is blocked or blurred, and t...; prevention_method=The motorcycle slows do... | The scene depicts an urban three-lane asphalt road on a cloudy day with dry weather conditions. A male cyclist, dressed in a light blue and black short sleeve shirt, dark pants, and carrying a black backpack, rides a... |
| 4 | Y | vru_accident:DADA_2000:VRU_106 | 0.0310 | accident_type=motorbike hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Motorcycle drives too fast with a short braking dist...; prevention_method=The motorcycle shall no... | On a bright and clear day, a narrow, dry asphalt residential road with one lane and parked vehicles along the right side is observed. A female cyclist, dressed in a dark outfit and wearing a white wide-brimmed hat, pe... |
| 5 | Y | vru_accident:DADA_2000:VRU_108 | 0.0305 | accident_type=motorbike hits cyclist; location=urban; road_type=intersection; weather_light=clear night; accident_reason=Motorcycle driver is inattentive; prevention_method=Motorcycle drivers should focus on driving.... | The incident occurs on a dark, unlit asphalt road at night, characterized by a two-way traffic setup with visible lane markings and traffic signals ahead. The driver approaches a red light at moderate speed, indicated... |


### lexical_beats_vector #1: `vru:medium:0116`

BM25 outperforms vector-only on the query, showing lexical baseline is necessary.

- difficulty: `medium`
- positives: `2`
- query: Find urban videos where the accident type is ego-car hits pedestrian.
- semantic_filter: `{"accident_type": "ego-car hits pedestrian"}`
- metadata_filter: `{"location": "urban"}`

Metrics:

| strategy | R@10 | Hit@10 | MRR | nDCG@10 | latency_ms |
| --- | --- | --- | --- | --- | --- |
| B1 BM25 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 128.5371 |
| B2 vector | 0.0000 | 0.0000 | 0.0222 | 0.0000 | 119.1096 |
| B3 postfilter | 0.0000 | 0.0000 | 0.0294 | 0.0000 | 5.0368 |
| B4 prefilter | 0.0000 | 0.0000 | 0.0294 | 0.0000 | 107.3702 |
| B5 hybrid | 0.0000 | 0.0000 | 0.0714 | 0.0000 | 249.0702 |

Top-5 results for B2 vector:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:CAP_DATA:VRU_30 | 0.8460 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian is drunk; prevention_method=Pedestrians should avoid walking on busy roads while... | The incident occurs at night under clear and dry weather conditions on a straight, two-lane asphalt road marked with pedestrian crossing signs and supporting two-way traffic. A male pedestrian, dressed in blue, stands... |
| 2 | N | vru_accident:CAP_DATA:VRU_56 | 0.8460 | accident_type=ego-car hits a pedestrian; location=urban; road_type=intersection; weather_light=rainy day; accident_reason=Ego-car does not notice the pedestrians when turning; prevention_method=The speed of ego-cars s... | The pedestrian, an adult male dressed in dark clothing and wearing white shoes, is standing in the middle of a marked crosswalk on a dry, multi-lane urban asphalt road at night, illuminated by artificial street lighti... |
| 3 | N | vru_accident:CAP_DATA:VRU_57 | 0.8460 | accident_type=ego-car hits a pedestrian; location=highway; road_type=arterials; weather_light=cloudy day; accident_reason=Ego-car is out of control; prevention_method=Ego-cars should avoid speeding in adverse weather... | The incident occurs on a multi-lane divided highway equipped with metal guardrails, under clear and dry weather conditions with light traffic. Several workers wearing bright orange high-visibility coveralls are standi... |
| 4 | N | vru_accident:CAP_DATA:VRU_58 | 0.8460 | accident_type=ego-car hits a pedestrian; location=rural; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian moves or stays on the road; prevention_method=Pedestrians should follow traffic rules | On a very dark night, a collision occurs on a two-lane asphalt road with dry surface conditions. A pedestrian, dressed in dark clothing, is seen standing on the roadway. A metal guardrail lines the right side of the r... |
| 5 | N | vru_accident:CAP_DATA:VRU_59 | 0.8460 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian moves or stays on the road; prevention_method=Pedestrians should follow traffic rules | The incident occurs at night on a two-lane road surrounded by mountainous terrain, with clear weather and dry road conditions. The vehicle's headlights illuminate the surrounding area. The incident vehicle begins trav... |


Top-5 results for B4 prefilter:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:CAP_DATA:VRU_30 | 0.8460 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian is drunk; prevention_method=Pedestrians should avoid walking on busy roads while... | The incident occurs at night under clear and dry weather conditions on a straight, two-lane asphalt road marked with pedestrian crossing signs and supporting two-way traffic. A male pedestrian, dressed in blue, stands... |
| 2 | N | vru_accident:CAP_DATA:VRU_56 | 0.8460 | accident_type=ego-car hits a pedestrian; location=urban; road_type=intersection; weather_light=rainy day; accident_reason=Ego-car does not notice the pedestrians when turning; prevention_method=The speed of ego-cars s... | The pedestrian, an adult male dressed in dark clothing and wearing white shoes, is standing in the middle of a marked crosswalk on a dry, multi-lane urban asphalt road at night, illuminated by artificial street lighti... |
| 3 | N | vru_accident:CAP_DATA:VRU_59 | 0.8460 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian moves or stays on the road; prevention_method=Pedestrians should follow traffic rules | The incident occurs at night on a two-lane road surrounded by mountainous terrain, with clear weather and dry road conditions. The vehicle's headlights illuminate the surrounding area. The incident vehicle begins trav... |
| 4 | N | vru_accident:CAP_DATA:VRU_61 | 0.8460 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian is drunk; prevention_method=Pedestrians should avoid walking on busy roads while... | The incident occurs at night on a well-lit, dry urban roadway flanked by parked vehicles and tall residential buildings. A male pedestrian, dressed in a dark coat and dark pants, is initially seen standing at the edge... |
| 5 | N | vru_accident:CAP_DATA:VRU_62 | 0.8460 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian moves or stays on the road; prevention_method=Pedestrians should follow traffic rules | The incident occurs at night under clear weather conditions on a narrow two-lane asphalt road, with decorative lights strung along trees lining the right shoulder. The vehicle travels straight at approximately 40 to 4... |


Top-5 results for B5 hybrid:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:CAP_DATA:VRU_30 | 0.0323 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian is drunk; prevention_method=Pedestrians should avoid walking on busy roads while... | The incident occurs at night under clear and dry weather conditions on a straight, two-lane asphalt road marked with pedestrian crossing signs and supporting two-way traffic. A male pedestrian, dressed in blue, stands... |
| 2 | N | vru_accident:CAP_DATA:VRU_56 | 0.0318 | accident_type=ego-car hits a pedestrian; location=urban; road_type=intersection; weather_light=rainy day; accident_reason=Ego-car does not notice the pedestrians when turning; prevention_method=The speed of ego-cars s... | The pedestrian, an adult male dressed in dark clothing and wearing white shoes, is standing in the middle of a marked crosswalk on a dry, multi-lane urban asphalt road at night, illuminated by artificial street lighti... |
| 3 | N | vru_accident:CAP_DATA:VRU_59 | 0.0313 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian moves or stays on the road; prevention_method=Pedestrians should follow traffic rules | The incident occurs at night on a two-lane road surrounded by mountainous terrain, with clear weather and dry road conditions. The vehicle's headlights illuminate the surrounding area. The incident vehicle begins trav... |
| 4 | N | vru_accident:CAP_DATA:VRU_61 | 0.0308 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian is drunk; prevention_method=Pedestrians should avoid walking on busy roads while... | The incident occurs at night on a well-lit, dry urban roadway flanked by parked vehicles and tall residential buildings. A male pedestrian, dressed in a dark coat and dark pants, is initially seen standing at the edge... |
| 5 | N | vru_accident:CAP_DATA:VRU_62 | 0.0303 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian moves or stays on the road; prevention_method=Pedestrians should follow traffic rules | The incident occurs at night under clear weather conditions on a narrow two-lane asphalt road, with decorative lights strung along trees lining the right shoulder. The vehicle travels straight at approximately 40 to 4... |


### lexical_beats_vector #2: `vru:medium:0153`

BM25 outperforms vector-only on the query, showing lexical baseline is necessary.

- difficulty: `medium`
- positives: `2`
- query: Find videos recorded in cloudy evening where the accident type is car hits pedestrian.
- semantic_filter: `{"accident_type": "car hits pedestrian"}`
- metadata_filter: `{"weather_light": "cloudy evening"}`

Metrics:

| strategy | R@10 | Hit@10 | MRR | nDCG@10 | latency_ms |
| --- | --- | --- | --- | --- | --- |
| B1 BM25 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 126.4556 |
| B2 vector | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 117.5863 |
| B3 postfilter | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 4.6412 |
| B4 prefilter | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9257 |
| B5 hybrid | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 123.3463 |

Top-5 results for B2 vector:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:CAP_DATA:VRU_102 | 0.7380 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=snowy day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down when... | This crash occurs during overcast daylight hours on a wet, multi-lane asphalt arterial road in an urban setting. The surrounding area includes moderate traffic flow and sidewalks lined with snowbanks and leafless tree... |
| 2 | N | vru_accident:CAP_DATA:VRU_103 | 0.7380 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down and y... | An elderly male pedestrian, wearing a bright green jacket and dark trousers, is observed crossing a wide, multi-lane asphalt arterial road on a clear and dry day. Initially positioned in the center of the roadway, he... |
| 3 | N | vru_accident:CAP_DATA:VRU_104 | 0.7380 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down and y... | The incident occurs on a clear and sunny day on a dry, two-way urban asphalt road without any marked pedestrian crossings. A male pedestrian, dressed in a white T-shirt and dark trousers, suddenly appears from the lef... |
| 4 | N | vru_accident:CAP_DATA:VRU_105 | 0.7380 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=snowy day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down and y... | An adult pedestrian wearing a dark jacket and a fluorescent safety vest attempts to cross a multi-lane, two-way urban asphalt road that is partially covered with snow. The weather is overcast, and the road is flat and... |
| 5 | N | vru_accident:CAP_DATA:VRU_106 | 0.7380 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid high spe... | This scene takes place during an overcast daytime period on a multi-lane urban asphalt road with a slightly damp surface. Traffic flow is moderate, and visibility is clear under the given conditions. A female pedestri... |


Top-5 results for B4 prefilter:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:CAP_DATA:VRU_213 | 0.7380 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=cloudy evening; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down... | This scene depicts an accident that occurs near an intersection in a residential area on a dry, paved road under overcast weather conditions. A female pedestrian, estimated to be in her late 20s to early 30s, dressed... |
| 2 | Y | vru_accident:CAP_DATA:VRU_230 | 0.7380 | accident_type=car hits pedestrian; location=urban; road_type=intersection; weather_light=cloudy evening; accident_reason=vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid... | This scene depicts a traffic accident that occurs on a clear, sunny day at a multi-lane urban intersection with dry asphalt. The area is surrounded by multi-story residential and commercial buildings. A pedestrian dre... |
| 3 | N | vru_accident:CAP_DATA:VRU_50 | 0.6781 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=arterials; weather_light=cloudy evening; accident_reason=The ego-car's vision is blocked or blurred, and ther...; prevention_method=Ego-cars... | This scene takes place on a wide, multi-lane urban asphalt road under clear weather and a bright sky, with residual snow piled along the curbs. A vehicle equipped with a dashcam is traveling straight at approximately... |


Top-5 results for B5 hybrid:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:CAP_DATA:VRU_213 | 0.0328 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=cloudy evening; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down... | This scene depicts an accident that occurs near an intersection in a residential area on a dry, paved road under overcast weather conditions. A female pedestrian, estimated to be in her late 20s to early 30s, dressed... |
| 2 | Y | vru_accident:CAP_DATA:VRU_230 | 0.0323 | accident_type=car hits pedestrian; location=urban; road_type=intersection; weather_light=cloudy evening; accident_reason=vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid... | This scene depicts a traffic accident that occurs on a clear, sunny day at a multi-lane urban intersection with dry asphalt. The area is surrounded by multi-story residential and commercial buildings. A pedestrian dre... |
| 3 | N | vru_accident:CAP_DATA:VRU_50 | 0.0317 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=arterials; weather_light=cloudy evening; accident_reason=The ego-car's vision is blocked or blurred, and ther...; prevention_method=Ego-cars... | This scene takes place on a wide, multi-lane urban asphalt road under clear weather and a bright sky, with residual snow piled along the curbs. A vehicle equipped with a dashcam is traveling straight at approximately... |


### lexical_beats_vector #3: `vru:weak:0019`

BM25 outperforms vector-only on the query, showing lexical baseline is necessary.

- difficulty: `weak`
- positives: `2`
- query: Find videos where the accident type is ego-car hits pedestrian.
- semantic_filter: `{"accident_type": "ego-car hits pedestrian"}`
- metadata_filter: `{}`

Metrics:

| strategy | R@10 | Hit@10 | MRR | nDCG@10 | latency_ms |
| --- | --- | --- | --- | --- | --- |
| B1 BM25 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 125.8271 |
| B2 vector | 0.0000 | 0.0000 | 0.0222 | 0.0000 | 117.8546 |
| B3 postfilter | 0.0000 | 0.0000 | 0.0222 | 0.0000 | 4.9990 |
| B4 prefilter | 0.0000 | 0.0000 | 0.0222 | 0.0000 | 120.6819 |
| B5 hybrid | 0.0000 | 0.0000 | 0.0588 | 0.0000 | 249.6417 |

Top-5 results for B2 vector:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:CAP_DATA:VRU_30 | 0.8876 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian is drunk; prevention_method=Pedestrians should avoid walking on busy roads while... | The incident occurs at night under clear and dry weather conditions on a straight, two-lane asphalt road marked with pedestrian crossing signs and supporting two-way traffic. A male pedestrian, dressed in blue, stands... |
| 2 | N | vru_accident:CAP_DATA:VRU_56 | 0.8876 | accident_type=ego-car hits a pedestrian; location=urban; road_type=intersection; weather_light=rainy day; accident_reason=Ego-car does not notice the pedestrians when turning; prevention_method=The speed of ego-cars s... | The pedestrian, an adult male dressed in dark clothing and wearing white shoes, is standing in the middle of a marked crosswalk on a dry, multi-lane urban asphalt road at night, illuminated by artificial street lighti... |
| 3 | N | vru_accident:CAP_DATA:VRU_57 | 0.8876 | accident_type=ego-car hits a pedestrian; location=highway; road_type=arterials; weather_light=cloudy day; accident_reason=Ego-car is out of control; prevention_method=Ego-cars should avoid speeding in adverse weather... | The incident occurs on a multi-lane divided highway equipped with metal guardrails, under clear and dry weather conditions with light traffic. Several workers wearing bright orange high-visibility coveralls are standi... |
| 4 | N | vru_accident:CAP_DATA:VRU_58 | 0.8876 | accident_type=ego-car hits a pedestrian; location=rural; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian moves or stays on the road; prevention_method=Pedestrians should follow traffic rules | On a very dark night, a collision occurs on a two-lane asphalt road with dry surface conditions. A pedestrian, dressed in dark clothing, is seen standing on the roadway. A metal guardrail lines the right side of the r... |
| 5 | N | vru_accident:CAP_DATA:VRU_59 | 0.8876 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian moves or stays on the road; prevention_method=Pedestrians should follow traffic rules | The incident occurs at night on a two-lane road surrounded by mountainous terrain, with clear weather and dry road conditions. The vehicle's headlights illuminate the surrounding area. The incident vehicle begins trav... |


Top-5 results for B4 prefilter:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:CAP_DATA:VRU_30 | 0.8876 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian is drunk; prevention_method=Pedestrians should avoid walking on busy roads while... | The incident occurs at night under clear and dry weather conditions on a straight, two-lane asphalt road marked with pedestrian crossing signs and supporting two-way traffic. A male pedestrian, dressed in blue, stands... |
| 2 | N | vru_accident:CAP_DATA:VRU_56 | 0.8876 | accident_type=ego-car hits a pedestrian; location=urban; road_type=intersection; weather_light=rainy day; accident_reason=Ego-car does not notice the pedestrians when turning; prevention_method=The speed of ego-cars s... | The pedestrian, an adult male dressed in dark clothing and wearing white shoes, is standing in the middle of a marked crosswalk on a dry, multi-lane urban asphalt road at night, illuminated by artificial street lighti... |
| 3 | N | vru_accident:CAP_DATA:VRU_57 | 0.8876 | accident_type=ego-car hits a pedestrian; location=highway; road_type=arterials; weather_light=cloudy day; accident_reason=Ego-car is out of control; prevention_method=Ego-cars should avoid speeding in adverse weather... | The incident occurs on a multi-lane divided highway equipped with metal guardrails, under clear and dry weather conditions with light traffic. Several workers wearing bright orange high-visibility coveralls are standi... |
| 4 | N | vru_accident:CAP_DATA:VRU_58 | 0.8876 | accident_type=ego-car hits a pedestrian; location=rural; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian moves or stays on the road; prevention_method=Pedestrians should follow traffic rules | On a very dark night, a collision occurs on a two-lane asphalt road with dry surface conditions. A pedestrian, dressed in dark clothing, is seen standing on the roadway. A metal guardrail lines the right side of the r... |
| 5 | N | vru_accident:CAP_DATA:VRU_59 | 0.8876 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian moves or stays on the road; prevention_method=Pedestrians should follow traffic rules | The incident occurs at night on a two-lane road surrounded by mountainous terrain, with clear weather and dry road conditions. The vehicle's headlights illuminate the surrounding area. The incident vehicle begins trav... |


Top-5 results for B5 hybrid:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:CAP_DATA:VRU_30 | 0.0323 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian is drunk; prevention_method=Pedestrians should avoid walking on busy roads while... | The incident occurs at night under clear and dry weather conditions on a straight, two-lane asphalt road marked with pedestrian crossing signs and supporting two-way traffic. A male pedestrian, dressed in blue, stands... |
| 2 | N | vru_accident:CAP_DATA:VRU_56 | 0.0318 | accident_type=ego-car hits a pedestrian; location=urban; road_type=intersection; weather_light=rainy day; accident_reason=Ego-car does not notice the pedestrians when turning; prevention_method=The speed of ego-cars s... | The pedestrian, an adult male dressed in dark clothing and wearing white shoes, is standing in the middle of a marked crosswalk on a dry, multi-lane urban asphalt road at night, illuminated by artificial street lighti... |
| 3 | N | vru_accident:CAP_DATA:VRU_57 | 0.0313 | accident_type=ego-car hits a pedestrian; location=highway; road_type=arterials; weather_light=cloudy day; accident_reason=Ego-car is out of control; prevention_method=Ego-cars should avoid speeding in adverse weather... | The incident occurs on a multi-lane divided highway equipped with metal guardrails, under clear and dry weather conditions with light traffic. Several workers wearing bright orange high-visibility coveralls are standi... |
| 4 | N | vru_accident:CAP_DATA:VRU_58 | 0.0308 | accident_type=ego-car hits a pedestrian; location=rural; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian moves or stays on the road; prevention_method=Pedestrians should follow traffic rules | On a very dark night, a collision occurs on a two-lane asphalt road with dry surface conditions. A pedestrian, dressed in dark clothing, is seen standing on the roadway. A metal guardrail lines the right side of the r... |
| 5 | N | vru_accident:CAP_DATA:VRU_59 | 0.0303 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian moves or stays on the road; prevention_method=Pedestrians should follow traffic rules | The incident occurs at night on a two-lane road surrounded by mountainous terrain, with clear weather and dry road conditions. The vehicle's headlights illuminate the surrounding area. The incident vehicle begins trav... |


### remaining_hard_case #1: `vru:medium:0081`

Even B4 prefilter has no relevant item in top-10 or very low nDCG.

- difficulty: `medium`
- positives: `2`
- query: Find videos where the accident type is ego-car hits pedestrian on a arterials road.
- semantic_filter: `{"accident_type": "ego-car hits pedestrian"}`
- metadata_filter: `{"road_type": "arterials"}`

Metrics:

| strategy | R@10 | Hit@10 | MRR | nDCG@10 | latency_ms |
| --- | --- | --- | --- | --- | --- |
| B1 BM25 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 129.0287 |
| B2 vector | 0.0000 | 0.0000 | 0.0222 | 0.0000 | 117.6900 |
| B3 postfilter | 0.0000 | 0.0000 | 0.0312 | 0.0000 | 5.0910 |
| B4 prefilter | 0.0000 | 0.0000 | 0.0312 | 0.0000 | 85.9624 |
| B5 hybrid | 0.0000 | 0.0000 | 0.0114 | 0.0000 | 219.1458 |

Top-5 results for B2 vector:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:CAP_DATA:VRU_30 | 0.8562 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian is drunk; prevention_method=Pedestrians should avoid walking on busy roads while... | The incident occurs at night under clear and dry weather conditions on a straight, two-lane asphalt road marked with pedestrian crossing signs and supporting two-way traffic. A male pedestrian, dressed in blue, stands... |
| 2 | N | vru_accident:CAP_DATA:VRU_56 | 0.8562 | accident_type=ego-car hits a pedestrian; location=urban; road_type=intersection; weather_light=rainy day; accident_reason=Ego-car does not notice the pedestrians when turning; prevention_method=The speed of ego-cars s... | The pedestrian, an adult male dressed in dark clothing and wearing white shoes, is standing in the middle of a marked crosswalk on a dry, multi-lane urban asphalt road at night, illuminated by artificial street lighti... |
| 3 | N | vru_accident:CAP_DATA:VRU_57 | 0.8562 | accident_type=ego-car hits a pedestrian; location=highway; road_type=arterials; weather_light=cloudy day; accident_reason=Ego-car is out of control; prevention_method=Ego-cars should avoid speeding in adverse weather... | The incident occurs on a multi-lane divided highway equipped with metal guardrails, under clear and dry weather conditions with light traffic. Several workers wearing bright orange high-visibility coveralls are standi... |
| 4 | N | vru_accident:CAP_DATA:VRU_58 | 0.8562 | accident_type=ego-car hits a pedestrian; location=rural; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian moves or stays on the road; prevention_method=Pedestrians should follow traffic rules | On a very dark night, a collision occurs on a two-lane asphalt road with dry surface conditions. A pedestrian, dressed in dark clothing, is seen standing on the roadway. A metal guardrail lines the right side of the r... |
| 5 | N | vru_accident:CAP_DATA:VRU_59 | 0.8562 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian moves or stays on the road; prevention_method=Pedestrians should follow traffic rules | The incident occurs at night on a two-lane road surrounded by mountainous terrain, with clear weather and dry road conditions. The vehicle's headlights illuminate the surrounding area. The incident vehicle begins trav... |


Top-5 results for B4 prefilter:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:CAP_DATA:VRU_30 | 0.8562 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian is drunk; prevention_method=Pedestrians should avoid walking on busy roads while... | The incident occurs at night under clear and dry weather conditions on a straight, two-lane asphalt road marked with pedestrian crossing signs and supporting two-way traffic. A male pedestrian, dressed in blue, stands... |
| 2 | N | vru_accident:CAP_DATA:VRU_57 | 0.8562 | accident_type=ego-car hits a pedestrian; location=highway; road_type=arterials; weather_light=cloudy day; accident_reason=Ego-car is out of control; prevention_method=Ego-cars should avoid speeding in adverse weather... | The incident occurs on a multi-lane divided highway equipped with metal guardrails, under clear and dry weather conditions with light traffic. Several workers wearing bright orange high-visibility coveralls are standi... |
| 3 | N | vru_accident:CAP_DATA:VRU_58 | 0.8562 | accident_type=ego-car hits a pedestrian; location=rural; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian moves or stays on the road; prevention_method=Pedestrians should follow traffic rules | On a very dark night, a collision occurs on a two-lane asphalt road with dry surface conditions. A pedestrian, dressed in dark clothing, is seen standing on the roadway. A metal guardrail lines the right side of the r... |
| 4 | N | vru_accident:CAP_DATA:VRU_59 | 0.8562 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian moves or stays on the road; prevention_method=Pedestrians should follow traffic rules | The incident occurs at night on a two-lane road surrounded by mountainous terrain, with clear weather and dry road conditions. The vehicle's headlights illuminate the surrounding area. The incident vehicle begins trav... |
| 5 | N | vru_accident:CAP_DATA:VRU_61 | 0.8562 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian is drunk; prevention_method=Pedestrians should avoid walking on busy roads while... | The incident occurs at night on a well-lit, dry urban roadway flanked by parked vehicles and tall residential buildings. A male pedestrian, dressed in a dark coat and dark pants, is initially seen standing at the edge... |


Top-5 results for B5 hybrid:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:CAP_DATA:VRU_30 | 0.0328 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian is drunk; prevention_method=Pedestrians should avoid walking on busy roads while... | The incident occurs at night under clear and dry weather conditions on a straight, two-lane asphalt road marked with pedestrian crossing signs and supporting two-way traffic. A male pedestrian, dressed in blue, stands... |
| 2 | N | vru_accident:CAP_DATA:VRU_57 | 0.0323 | accident_type=ego-car hits a pedestrian; location=highway; road_type=arterials; weather_light=cloudy day; accident_reason=Ego-car is out of control; prevention_method=Ego-cars should avoid speeding in adverse weather... | The incident occurs on a multi-lane divided highway equipped with metal guardrails, under clear and dry weather conditions with light traffic. Several workers wearing bright orange high-visibility coveralls are standi... |
| 3 | N | vru_accident:CAP_DATA:VRU_58 | 0.0317 | accident_type=ego-car hits a pedestrian; location=rural; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian moves or stays on the road; prevention_method=Pedestrians should follow traffic rules | On a very dark night, a collision occurs on a two-lane asphalt road with dry surface conditions. A pedestrian, dressed in dark clothing, is seen standing on the roadway. A metal guardrail lines the right side of the r... |
| 4 | N | vru_accident:CAP_DATA:VRU_59 | 0.0312 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian moves or stays on the road; prevention_method=Pedestrians should follow traffic rules | The incident occurs at night on a two-lane road surrounded by mountainous terrain, with clear weather and dry road conditions. The vehicle's headlights illuminate the surrounding area. The incident vehicle begins trav... |
| 5 | N | vru_accident:CAP_DATA:VRU_61 | 0.0308 | accident_type=ego-car hits a pedestrian; location=urban; road_type=arterials; weather_light=clear night; accident_reason=Pedestrian is drunk; prevention_method=Pedestrians should avoid walking on busy roads while... | The incident occurs at night on a well-lit, dry urban roadway flanked by parked vehicles and tall residential buildings. A male pedestrian, dressed in a dark coat and dark pants, is initially seen standing at the edge... |


### remaining_hard_case #2: `vru:weak:0027`

Even B4 prefilter has no relevant item in top-10 or very low nDCG.

- difficulty: `weak`
- positives: `45`
- query: Find accidents caused by: Pedestrian does not notice the coming vehicles when crossing the street.
- semantic_filter: `{"accident_reason": "Pedestrian does not notice the coming vehicles when crossing the street"}`
- metadata_filter: `{}`

Metrics:

| strategy | R@10 | Hit@10 | MRR | nDCG@10 | latency_ms |
| --- | --- | --- | --- | --- | --- |
| B1 BM25 | 0.0000 | 0.0000 | 0.0133 | 0.0000 | 126.7197 |
| B2 vector | 0.0000 | 0.0000 | 0.0105 | 0.0000 | 116.0715 |
| B3 postfilter | 0.0000 | 0.0000 | 0.0105 | 0.0000 | 4.9024 |
| B4 prefilter | 0.0000 | 0.0000 | 0.0105 | 0.0000 | 140.7427 |
| B5 hybrid | 0.0000 | 0.0000 | 0.0133 | 0.0000 | 267.9241 |

Top-5 results for B2 vector:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:CAP_DATA:VRU_131 | 0.9448 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down and y... | The pedestrian, an adult male dressed in a dark long-sleeved shirt and dark pants, is crossing a dry, multi-lane urban asphalt road with clearly marked zebra crossings and a central median fence at a moderate pace. Th... |
| 2 | N | vru_accident:CAP_DATA:VRU_141 | 0.9448 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians should always look... | A female pedestrian, wearing a light blue jacket, jeans, and sneakers, and carrying a light pink backpack, stands at the edge of a dry, asphalt-paved two-lane urban road under clear and sunny weather conditions. She i... |
| 3 | N | vru_accident:CAP_DATA:VRU_143 | 0.9448 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=snowy day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians should follow traf... | A male pedestrian, dressed in a long dark jacket and pants, suddenly emerges from the left side of a damp, snow-patched, two-way urban asphalt road under overcast skies. The road has multiple lanes and heavy traffic,... |
| 4 | N | vru_accident:CAP_DATA:VRU_147 | 0.9448 | accident_type=car hits pedestrian; location=urban; road_type=curve; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down and yield... | The video depicts a collision occurring at a marked pedestrian crosswalk adjacent to a multi-lane roundabout near a commercial building under partly cloudy skies. The road surface is dry asphalt, and the crosswalk is... |
| 5 | N | vru_accident:CAP_DATA:VRU_148 | 0.9448 | accident_type=car hits pedestrian; location=urban; road_type=alley; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down where vis... | On a clear and sunny day, a black sedan is traveling at approximately 30 km/h along a narrow, dry asphalt one-way residential street. Vehicles are parked along both sides of the road. At that moment, a young pedestria... |


Top-5 results for B4 prefilter:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:CAP_DATA:VRU_131 | 0.9448 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down and y... | The pedestrian, an adult male dressed in a dark long-sleeved shirt and dark pants, is crossing a dry, multi-lane urban asphalt road with clearly marked zebra crossings and a central median fence at a moderate pace. Th... |
| 2 | N | vru_accident:CAP_DATA:VRU_141 | 0.9448 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians should always look... | A female pedestrian, wearing a light blue jacket, jeans, and sneakers, and carrying a light pink backpack, stands at the edge of a dry, asphalt-paved two-lane urban road under clear and sunny weather conditions. She i... |
| 3 | N | vru_accident:CAP_DATA:VRU_143 | 0.9448 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=snowy day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians should follow traf... | A male pedestrian, dressed in a long dark jacket and pants, suddenly emerges from the left side of a damp, snow-patched, two-way urban asphalt road under overcast skies. The road has multiple lanes and heavy traffic,... |
| 4 | N | vru_accident:CAP_DATA:VRU_147 | 0.9448 | accident_type=car hits pedestrian; location=urban; road_type=curve; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down and yield... | The video depicts a collision occurring at a marked pedestrian crosswalk adjacent to a multi-lane roundabout near a commercial building under partly cloudy skies. The road surface is dry asphalt, and the crosswalk is... |
| 5 | N | vru_accident:CAP_DATA:VRU_148 | 0.9448 | accident_type=car hits pedestrian; location=urban; road_type=alley; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down where vis... | On a clear and sunny day, a black sedan is traveling at approximately 30 km/h along a narrow, dry asphalt one-way residential street. Vehicles are parked along both sides of the road. At that moment, a young pedestria... |


Top-5 results for B5 hybrid:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | N | vru_accident:CAP_DATA:VRU_131 | 0.0294 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down and y... | The pedestrian, an adult male dressed in a dark long-sleeved shirt and dark pants, is crossing a dry, multi-lane urban asphalt road with clearly marked zebra crossings and a central median fence at a moderate pace. Th... |
| 2 | N | vru_accident:CAP_DATA:VRU_141 | 0.0282 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians should always look... | A female pedestrian, wearing a light blue jacket, jeans, and sneakers, and carrying a light pink backpack, stands at the edge of a dry, asphalt-paved two-lane urban road under clear and sunny weather conditions. She i... |
| 3 | N | vru_accident:CAP_DATA:VRU_143 | 0.0278 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=snowy day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians should follow traf... | A male pedestrian, dressed in a long dark jacket and pants, suddenly emerges from the left side of a damp, snow-patched, two-way urban asphalt road under overcast skies. The road has multiple lanes and heavy traffic,... |
| 4 | N | vru_accident:CAP_DATA:VRU_147 | 0.0274 | accident_type=car hits pedestrian; location=urban; road_type=curve; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down and yield... | The video depicts a collision occurring at a marked pedestrian crosswalk adjacent to a multi-lane roundabout near a commercial building under partly cloudy skies. The road surface is dry asphalt, and the crosswalk is... |
| 5 | N | vru_accident:CAP_DATA:VRU_1 | 0.0271 | accident_type=ego-car hits a crossing pedestrian; location=rural; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians sho... | On a clear and bright early morning, a vehicle travels at approximately 79 to 80 km/h along a narrow, dry, and straight rural asphalt road flanked by leafless trees and electrical poles on both sides. A pedestrian wal... |


### weak_query_control #1: `vru:weak:0001`

Weak queries have no metadata filter, so B2/B3/B4 should be almost identical.

- difficulty: `weak`
- positives: `419`
- query: Find videos where the accident type is car hits pedestrian.
- semantic_filter: `{"accident_type": "car hits pedestrian"}`
- metadata_filter: `{}`

Metrics:

| strategy | R@10 | Hit@10 | MRR | nDCG@10 | latency_ms |
| --- | --- | --- | --- | --- | --- |
| B1 BM25 | 0.0191 | 1.0000 | 0.3333 | 0.6410 | 128.7168 |
| B2 vector | 0.0239 | 1.0000 | 1.0000 | 1.0000 | 112.7833 |
| B3 postfilter | 0.0239 | 1.0000 | 1.0000 | 1.0000 | 4.8183 |
| B4 prefilter | 0.0239 | 1.0000 | 1.0000 | 1.0000 | 126.0901 |
| B5 hybrid | 0.0239 | 1.0000 | 1.0000 | 1.0000 | 241.3971 |

Top-5 results for B2 vector:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:CAP_DATA:VRU_176 | 0.8382 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians should always look... | A male pedestrian, dressed in a dark jacket and dark pants, is crossing a dry, multi-lane urban asphalt road on a clear day, moving toward the left sidewalk. His path is nearly perpendicular to the direction of traffi... |
| 2 | Y | vru_accident:CAP_DATA:VRU_179 | 0.8382 | accident_type=car hits pedestrian; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=vehicles drive too fast with short braking distance; prevention_method=Drivers should obey speed limits | This scene takes place at a pedestrian crosswalk on a flat, dry asphalt road under clear weather conditions, with autumn foliage visible in the background. A white minibus is traveling straight from the left side of t... |
| 3 | Y | vru_accident:CAP_DATA:VRU_180 | 0.8382 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down and y... | A male pedestrian, dressed in a dark jacket, dark pants, and a dark cap, is involved in a traffic accident on a dry, two-way urban asphalt road during clear daytime conditions. The road features a marked zebra crossin... |
| 4 | Y | vru_accident:CAP_DATA:VRU_181 | 0.8382 | accident_type=car hits pedestrian; location=urban; road_type=intersection; weather_light=snowy day; accident_reason=vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid high... | The road surface is slightly wet, with snow piled along the sidewalks. A young female pedestrian, dressed in dark clothing, is crossing a wide urban asphalt road using a marked crosswalk under overcast skies with clea... |
| 5 | Y | vru_accident:DoTA:VRU_52 | 0.8382 | accident_type=car hits pedestrian; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=Vehicles do not notice the pedestrians when driving; prevention_method=Drivers should strictly follow t... | On a clear day with bright sunlight, a female pedestrian stands at the right edge of a dry, two-way asphalt road. She is wearing a light blue jacket, dark jeans, black shoes, and glasses, and carries an orange backpac... |


Top-5 results for B4 prefilter:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:CAP_DATA:VRU_176 | 0.8382 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians should always look... | A male pedestrian, dressed in a dark jacket and dark pants, is crossing a dry, multi-lane urban asphalt road on a clear day, moving toward the left sidewalk. His path is nearly perpendicular to the direction of traffi... |
| 2 | Y | vru_accident:CAP_DATA:VRU_179 | 0.8382 | accident_type=car hits pedestrian; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=vehicles drive too fast with short braking distance; prevention_method=Drivers should obey speed limits | This scene takes place at a pedestrian crosswalk on a flat, dry asphalt road under clear weather conditions, with autumn foliage visible in the background. A white minibus is traveling straight from the left side of t... |
| 3 | Y | vru_accident:CAP_DATA:VRU_180 | 0.8382 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down and y... | A male pedestrian, dressed in a dark jacket, dark pants, and a dark cap, is involved in a traffic accident on a dry, two-way urban asphalt road during clear daytime conditions. The road features a marked zebra crossin... |
| 4 | Y | vru_accident:CAP_DATA:VRU_181 | 0.8382 | accident_type=car hits pedestrian; location=urban; road_type=intersection; weather_light=snowy day; accident_reason=vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid high... | The road surface is slightly wet, with snow piled along the sidewalks. A young female pedestrian, dressed in dark clothing, is crossing a wide urban asphalt road using a marked crosswalk under overcast skies with clea... |
| 5 | Y | vru_accident:DoTA:VRU_52 | 0.8382 | accident_type=car hits pedestrian; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=Vehicles do not notice the pedestrians when driving; prevention_method=Drivers should strictly follow t... | On a clear day with bright sunlight, a female pedestrian stands at the right edge of a dry, two-way asphalt road. She is wearing a light blue jacket, dark jeans, black shoes, and glasses, and carries an orange backpac... |


Top-5 results for B5 hybrid:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:CAP_DATA:VRU_102 | 0.0306 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=snowy day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down when... | This crash occurs during overcast daylight hours on a wet, multi-lane asphalt arterial road in an urban setting. The surrounding area includes moderate traffic flow and sidewalks lined with snowbanks and leafless tree... |
| 2 | Y | vru_accident:CAP_DATA:VRU_103 | 0.0301 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down and y... | An elderly male pedestrian, wearing a bright green jacket and dark trousers, is observed crossing a wide, multi-lane asphalt arterial road on a clear and dry day. Initially positioned in the center of the roadway, he... |
| 3 | Y | vru_accident:CAP_DATA:VRU_104 | 0.0297 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down and y... | The incident occurs on a clear and sunny day on a dry, two-way urban asphalt road without any marked pedestrian crossings. A male pedestrian, dressed in a white T-shirt and dark trousers, suddenly appears from the lef... |
| 4 | Y | vru_accident:CAP_DATA:VRU_105 | 0.0292 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=snowy day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Drivers should slow down and y... | An adult pedestrian wearing a dark jacket and a fluorescent safety vest attempts to cross a multi-lane, two-way urban asphalt road that is partially covered with snow. The weather is overcast, and the road is flat and... |
| 5 | Y | vru_accident:CAP_DATA:VRU_106 | 0.0288 | accident_type=car hits pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=vehicles do not notice the pedestrians when turning...; prevention_method=Vehicles should avoid high spe... | This scene takes place during an overcast daytime period on a multi-lane urban asphalt road with a slightly damp surface. Traffic flow is moderate, and visibility is clear under the given conditions. A female pedestri... |


### weak_query_control #2: `vru:weak:0002`

Weak queries have no metadata filter, so B2/B3/B4 should be almost identical.

- difficulty: `weak`
- positives: `197`
- query: Find videos where the accident type is ego-car hits a crossing pedestrian.
- semantic_filter: `{"accident_type": "ego-car hits a crossing pedestrian"}`
- metadata_filter: `{}`

Metrics:

| strategy | R@10 | Hit@10 | MRR | nDCG@10 | latency_ms |
| --- | --- | --- | --- | --- | --- |
| B1 BM25 | 0.0508 | 1.0000 | 1.0000 | 1.0000 | 128.6826 |
| B2 vector | 0.0508 | 1.0000 | 1.0000 | 1.0000 | 114.6345 |
| B3 postfilter | 0.0508 | 1.0000 | 1.0000 | 1.0000 | 4.7794 |
| B4 prefilter | 0.0508 | 1.0000 | 1.0000 | 1.0000 | 116.6955 |
| B5 hybrid | 0.0508 | 1.0000 | 1.0000 | 1.0000 | 256.9593 |

Top-5 results for B2 vector:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:CAP_DATA:VRU_1 | 0.8904 | accident_type=ego-car hits a crossing pedestrian; location=rural; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians sho... | On a clear and bright early morning, a vehicle travels at approximately 79 to 80 km/h along a narrow, dry, and straight rural asphalt road flanked by leafless trees and electrical poles on both sides. A pedestrian wal... |
| 2 | Y | vru_accident:CAP_DATA:VRU_10 | 0.8904 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=The ego-car's vision is blocked or blurred, and ther...; prevention_method=Ego-cars shoul... | On an overcast afternoon, the asphalt surface of a multi-lane arterial road is clearly marked with traffic signage. A female pedestrian, wearing a white top, gray pants, and carrying a handbag, suddenly runs from the... |
| 3 | Y | vru_accident:CAP_DATA:VRU_11 | 0.8904 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Ego-car does not notice the pedestrians when turning; prevention_method=The speed of e... | A female pedestrian wearing a brown jacket and dark trousers is crossing a wide, dry urban asphalt road with marked pedestrian crosswalks under clear daylight conditions. She is walking from the left side of the inter... |
| 4 | Y | vru_accident:CAP_DATA:VRU_12 | 0.8904 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=arterials; weather_light=snowy day; accident_reason=Ego-car driver is in distracted driving; prevention_method=Since the accident was caused... | The scene depicts a snowy, icy two-way urban road flanked by multi-story residential and commercial buildings under an overcast sky. A pedestrian wearing a purple coat, a skirt, and black boots stands at the edge of t... |
| 5 | Y | vru_accident:CAP_DATA:VRU_13 | 0.8904 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=arterials; weather_light=snowy day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians sho... | A male pedestrian wearing a dark hooded jacket and dark pants is crossing a dry, multi-lane asphalt road under bright daylight conditions, with a snow-covered shoulder and leafless trees lining the right side. He atte... |


Top-5 results for B4 prefilter:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:CAP_DATA:VRU_1 | 0.8904 | accident_type=ego-car hits a crossing pedestrian; location=rural; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians sho... | On a clear and bright early morning, a vehicle travels at approximately 79 to 80 km/h along a narrow, dry, and straight rural asphalt road flanked by leafless trees and electrical poles on both sides. A pedestrian wal... |
| 2 | Y | vru_accident:CAP_DATA:VRU_10 | 0.8904 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=The ego-car's vision is blocked or blurred, and ther...; prevention_method=Ego-cars shoul... | On an overcast afternoon, the asphalt surface of a multi-lane arterial road is clearly marked with traffic signage. A female pedestrian, wearing a white top, gray pants, and carrying a handbag, suddenly runs from the... |
| 3 | Y | vru_accident:CAP_DATA:VRU_11 | 0.8904 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Ego-car does not notice the pedestrians when turning; prevention_method=The speed of e... | A female pedestrian wearing a brown jacket and dark trousers is crossing a wide, dry urban asphalt road with marked pedestrian crosswalks under clear daylight conditions. She is walking from the left side of the inter... |
| 4 | Y | vru_accident:CAP_DATA:VRU_12 | 0.8904 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=arterials; weather_light=snowy day; accident_reason=Ego-car driver is in distracted driving; prevention_method=Since the accident was caused... | The scene depicts a snowy, icy two-way urban road flanked by multi-story residential and commercial buildings under an overcast sky. A pedestrian wearing a purple coat, a skirt, and black boots stands at the edge of t... |
| 5 | Y | vru_accident:CAP_DATA:VRU_13 | 0.8904 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=arterials; weather_light=snowy day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians sho... | A male pedestrian wearing a dark hooded jacket and dark pants is crossing a dry, multi-lane asphalt road under bright daylight conditions, with a snow-covered shoulder and leafless trees lining the right side. He atte... |


Top-5 results for B5 hybrid:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:CAP_DATA:VRU_1 | 0.0328 | accident_type=ego-car hits a crossing pedestrian; location=rural; road_type=arterials; weather_light=sunny day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians sho... | On a clear and bright early morning, a vehicle travels at approximately 79 to 80 km/h along a narrow, dry, and straight rural asphalt road flanked by leafless trees and electrical poles on both sides. A pedestrian wal... |
| 2 | Y | vru_accident:CAP_DATA:VRU_10 | 0.0323 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=arterials; weather_light=sunny day; accident_reason=The ego-car's vision is blocked or blurred, and ther...; prevention_method=Ego-cars shoul... | On an overcast afternoon, the asphalt surface of a multi-lane arterial road is clearly marked with traffic signage. A female pedestrian, wearing a white top, gray pants, and carrying a handbag, suddenly runs from the... |
| 3 | Y | vru_accident:CAP_DATA:VRU_11 | 0.0317 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=Ego-car does not notice the pedestrians when turning; prevention_method=The speed of e... | A female pedestrian wearing a brown jacket and dark trousers is crossing a wide, dry urban asphalt road with marked pedestrian crosswalks under clear daylight conditions. She is walking from the left side of the inter... |
| 4 | Y | vru_accident:CAP_DATA:VRU_12 | 0.0312 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=arterials; weather_light=snowy day; accident_reason=Ego-car driver is in distracted driving; prevention_method=Since the accident was caused... | The scene depicts a snowy, icy two-way urban road flanked by multi-story residential and commercial buildings under an overcast sky. A pedestrian wearing a purple coat, a skirt, and black boots stands at the edge of t... |
| 5 | Y | vru_accident:CAP_DATA:VRU_13 | 0.0308 | accident_type=ego-car hits a crossing pedestrian; location=urban; road_type=arterials; weather_light=snowy day; accident_reason=Pedestrian does not notice the coming vehicles when...; prevention_method=Pedestrians sho... | A male pedestrian wearing a dark hooded jacket and dark pants is crossing a dry, multi-lane asphalt road under bright daylight conditions, with a snow-covered shoulder and leafless trees lining the right side. He atte... |


### weak_query_control #3: `vru:weak:0003`

Weak queries have no metadata filter, so B2/B3/B4 should be almost identical.

- difficulty: `weak`
- positives: `118`
- query: Find videos where the accident type is car hits cyclist.
- semantic_filter: `{"accident_type": "car hits cyclist"}`
- metadata_filter: `{}`

Metrics:

| strategy | R@10 | Hit@10 | MRR | nDCG@10 | latency_ms |
| --- | --- | --- | --- | --- | --- |
| B1 BM25 | 0.0763 | 1.0000 | 0.5000 | 0.7799 | 120.2213 |
| B2 vector | 0.0847 | 1.0000 | 1.0000 | 1.0000 | 113.7504 |
| B3 postfilter | 0.0847 | 1.0000 | 1.0000 | 1.0000 | 5.1315 |
| B4 prefilter | 0.0847 | 1.0000 | 1.0000 | 1.0000 | 117.9062 |
| B5 hybrid | 0.0847 | 1.0000 | 1.0000 | 1.0000 | 237.0226 |

Top-5 results for B2 vector:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:CAP_DATA:VRU_235 | 0.8464 | accident_type=car hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=vehicles do not notice the cyclists when turning or...; prevention_method=The vehicles should decrease t... | This scene depicts an accident that occurs in broad daylight under clear and calm weather conditions, near a marked pedestrian crossing adjacent to a railway crossing with active warning signals. The road is a dry, pa... |
| 2 | Y | vru_accident:CAP_DATA:VRU_236 | 0.8464 | accident_type=car hits cyclist; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=Cyclist does not notice the coming vehicles when cro...; prevention_method=Cyclists should cross carefully... | On a clear and dry day at a multi-lane urban intersection, a silver compact car is seen making a left turn at approximately 30 km/h as it merges onto a main road. At that moment, a male cyclist wearing a black short-s... |
| 3 | Y | vru_accident:CAP_DATA:VRU_237 | 0.8464 | accident_type=car hits cyclist; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=vehicles's vision are blocked and there is no time t...; prevention_method=The vehicle should stop at the... | The cyclist, a male wearing a black top, red shorts, and a blue backpack, is riding along a dry, multi-lane urban asphalt road under overcast skies. The road is busy, with vehicles moving in both directions. The cycli... |
| 4 | Y | vru_accident:CAP_DATA:VRU_238 | 0.8464 | accident_type=car hits cyclist; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=vehicles's vision are blocked and there is no time t...; prevention_method=The vehicle should stop at the... | This scene depicts a collision between a bicycle and a vehicle on a two-way urban asphalt road in the late afternoon under clear weather conditions. A male cyclist, wearing a white sports T-shirt with the number 4 on... |
| 5 | Y | vru_accident:CAP_DATA:VRU_239 | 0.8464 | accident_type=car hits cyclist; location=rural; road_type=arterials; weather_light=rainy day; accident_reason=Cyclist does not notice the coming vehicles when cro...; prevention_method=Cyclists should cross carefully... | This scene depicts a traffic accident on a rainy day along a suburban two-way road with wet asphalt conditions. A gray sedan is seen traveling straight in the left lane at approximately 50 km/h. At that moment, a cycl... |


Top-5 results for B4 prefilter:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:CAP_DATA:VRU_235 | 0.8464 | accident_type=car hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=vehicles do not notice the cyclists when turning or...; prevention_method=The vehicles should decrease t... | This scene depicts an accident that occurs in broad daylight under clear and calm weather conditions, near a marked pedestrian crossing adjacent to a railway crossing with active warning signals. The road is a dry, pa... |
| 2 | Y | vru_accident:CAP_DATA:VRU_236 | 0.8464 | accident_type=car hits cyclist; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=Cyclist does not notice the coming vehicles when cro...; prevention_method=Cyclists should cross carefully... | On a clear and dry day at a multi-lane urban intersection, a silver compact car is seen making a left turn at approximately 30 km/h as it merges onto a main road. At that moment, a male cyclist wearing a black short-s... |
| 3 | Y | vru_accident:CAP_DATA:VRU_237 | 0.8464 | accident_type=car hits cyclist; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=vehicles's vision are blocked and there is no time t...; prevention_method=The vehicle should stop at the... | The cyclist, a male wearing a black top, red shorts, and a blue backpack, is riding along a dry, multi-lane urban asphalt road under overcast skies. The road is busy, with vehicles moving in both directions. The cycli... |
| 4 | Y | vru_accident:CAP_DATA:VRU_238 | 0.8464 | accident_type=car hits cyclist; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=vehicles's vision are blocked and there is no time t...; prevention_method=The vehicle should stop at the... | This scene depicts a collision between a bicycle and a vehicle on a two-way urban asphalt road in the late afternoon under clear weather conditions. A male cyclist, wearing a white sports T-shirt with the number 4 on... |
| 5 | Y | vru_accident:CAP_DATA:VRU_239 | 0.8464 | accident_type=car hits cyclist; location=rural; road_type=arterials; weather_light=rainy day; accident_reason=Cyclist does not notice the coming vehicles when cro...; prevention_method=Cyclists should cross carefully... | This scene depicts a traffic accident on a rainy day along a suburban two-way road with wet asphalt conditions. A gray sedan is seen traveling straight in the left lane at approximately 50 km/h. At that moment, a cycl... |


Top-5 results for B5 hybrid:

| rank | rel | clip_id | score | metadata | caption |
| --- | --- | --- | --- | --- | --- |
| 1 | Y | vru_accident:CAP_DATA:VRU_235 | 0.0325 | accident_type=car hits cyclist; location=urban; road_type=intersection; weather_light=sunny day; accident_reason=vehicles do not notice the cyclists when turning or...; prevention_method=The vehicles should decrease t... | This scene depicts an accident that occurs in broad daylight under clear and calm weather conditions, near a marked pedestrian crossing adjacent to a railway crossing with active warning signals. The road is a dry, pa... |
| 2 | Y | vru_accident:CAP_DATA:VRU_236 | 0.0320 | accident_type=car hits cyclist; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=Cyclist does not notice the coming vehicles when cro...; prevention_method=Cyclists should cross carefully... | On a clear and dry day at a multi-lane urban intersection, a silver compact car is seen making a left turn at approximately 30 km/h as it merges onto a main road. At that moment, a male cyclist wearing a black short-s... |
| 3 | Y | vru_accident:CAP_DATA:VRU_237 | 0.0315 | accident_type=car hits cyclist; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=vehicles's vision are blocked and there is no time t...; prevention_method=The vehicle should stop at the... | The cyclist, a male wearing a black top, red shorts, and a blue backpack, is riding along a dry, multi-lane urban asphalt road under overcast skies. The road is busy, with vehicles moving in both directions. The cycli... |
| 4 | Y | vru_accident:CAP_DATA:VRU_238 | 0.0310 | accident_type=car hits cyclist; location=urban; road_type=T-junction; weather_light=sunny day; accident_reason=vehicles's vision are blocked and there is no time t...; prevention_method=The vehicle should stop at the... | This scene depicts a collision between a bicycle and a vehicle on a two-way urban asphalt road in the late afternoon under clear weather conditions. A male cyclist, wearing a white sports T-shirt with the number 4 on... |
| 5 | Y | vru_accident:CAP_DATA:VRU_239 | 0.0305 | accident_type=car hits cyclist; location=rural; road_type=arterials; weather_light=rainy day; accident_reason=Cyclist does not notice the coming vehicles when cro...; prevention_method=Cyclists should cross carefully... | This scene depicts a traffic accident on a rainy day along a suburban two-way road with wet asphalt conditions. A gray sedan is seen traveling straight in the left lane at approximately 50 km/h. At that moment, a cycl... |

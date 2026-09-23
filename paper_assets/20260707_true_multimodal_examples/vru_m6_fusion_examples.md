# vru M6 Fusion Examples

| strategy | query_id | difficulty | query_text | rank | clip_id | visual_frame_id | evidence_timestamp_sec | evidence_frame_path | media_path | score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M6_text_visual_metadata_rrf | vru:medium:0040 | medium | Find videos where the accident type is car hits pedestrian on a arterials road. | 3 | vru_accident:CAP_DATA:VRU_177 | vru_accident_CAP_DATA_VRU_177:kf03 | 6.2 | Datasets/processed/vru_accident/20260706/keyframes/clip4_full/frames/vru_accident_CAP_DATA_VRU_177/kf03_f000124.jpg | /home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/raw/VRU-Accident/VRU_videos/CAP_DATA/VRU_177.mp4 | 0.020258315640481243 |
| M6_text_visual_metadata_rrf | vru:medium:0041 | medium | Find videos where the accident type is ego-car hits a crossing pedestrian on a arterials road. | 1 | vru_accident:CAP_DATA:VRU_17 | vru_accident_CAP_DATA_VRU_17:kf02 | 3.95 | Datasets/processed/vru_accident/20260706/keyframes/clip4_full/frames/vru_accident_CAP_DATA_VRU_17/kf02_f000079.jpg | /home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/raw/VRU-Accident/VRU_videos/CAP_DATA/VRU_17.mp4 | 0.023252890899949724 |
| M6_text_visual_metadata_rrf | vru:medium:0042 | medium | Find videos where the accident type is car hits pedestrian on a intersection road. | 1 | vru_accident:CAP_DATA:VRU_133 | vru_accident_CAP_DATA_VRU_133:kf02 | 2.45 | Datasets/processed/vru_accident/20260706/keyframes/clip4_full/frames/vru_accident_CAP_DATA_VRU_133/kf02_f000049.jpg | /home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/raw/VRU-Accident/VRU_videos/CAP_DATA/VRU_133.mp4 | 0.026655348047538198 |
| M6_text_visual_metadata_rrf | vru:medium:0043 | medium | Find videos where the accident type is car hits cyclist on a intersection road. | 1 | vru_accident:CAP_DATA:VRU_235 | vru_accident_CAP_DATA_VRU_235:kf02 | 3.85 | Datasets/processed/vru_accident/20260706/keyframes/clip4_full/frames/vru_accident_CAP_DATA_VRU_235/kf02_f000077.jpg | /home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/raw/VRU-Accident/VRU_videos/CAP_DATA/VRU_235.mp4 | 0.03177805800756621 |
| M6_text_visual_metadata_rrf | vru:medium:0044 | medium | Find videos where the accident type is car hits pedestrian on a T-junction road. | 1 | vru_accident:CAP_DATA:VRU_154 | vru_accident_CAP_DATA_VRU_154:kf03 | 4.0 | Datasets/processed/vru_accident/20260706/keyframes/clip4_full/frames/vru_accident_CAP_DATA_VRU_154/kf03_f000080.jpg | /home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/raw/VRU-Accident/VRU_videos/CAP_DATA/VRU_154.mp4 | 0.029827662395050816 |

## Supporting Text

### Example 1

- query_id: `vru:medium:0040`
- clip_id: `vru_accident:CAP_DATA:VRU_177`
- supporting_text: A male pedestrian, dressed in a gray jacket and dark pants, is crossing a dry, straight two-way urban asphalt road from right to left around midday under clear weather conditions. Sidewalks line both sides of the road, with a clear separation between the pedestrian walkways and the roadway. The pedestrian is crossing in front of the dashcam-equipped vehicle and enters the opposing lane. At that moment, a gray sedan is traveling straight at approximately 50 km/h. The pedestrian moves quickly a...

### Example 2

- query_id: `vru:medium:0041`
- clip_id: `vru_accident:CAP_DATA:VRU_17`
- supporting_text: A female pedestrian wearing a white jacket, blue jeans, and carrying a red handbag suddenly crosses a wet, multi-lane urban asphalt road under overcast weather conditions, with moderate traffic. She jaywalks and abruptly changes direction, stepping into active traffic lanes where multiple vehicles are traveling. At that moment, the camera-mounted vehicle is traveling at approximately 40?50 km/h, maintaining its lane. Despite clear visibility, the pedestrian accelerates without hesitation, ent...

### Example 3

- query_id: `vru:medium:0042`
- clip_id: `vru_accident:CAP_DATA:VRU_133`
- supporting_text: The collision takes place at dusk under clear weather conditions on a dry, multi-lane urban asphalt road, within a clearly marked pedestrian crosswalk. Traffic volume is moderate. A male pedestrian, wearing dark pants and a blue top, begins to cross quickly from the right sidewalk toward the crosswalk. At the same time, a black pickup truck is approaching the intersection at a high speed of approximately 50 km/h. The driver fails to notice the pedestrian crossing and subsequently collides wit...

### Example 4

- query_id: `vru:medium:0043`
- clip_id: `vru_accident:CAP_DATA:VRU_235`
- supporting_text: This scene depicts an accident that occurs in broad daylight under clear and calm weather conditions, near a marked pedestrian crossing adjacent to a railway crossing with active warning signals. The road is a dry, paved urban roadway. The cyclist, an adult wearing a blue jacket, dark pants, and a white hat, is riding along the road from the right side of the frame toward the pedestrian crossing. At the same time, a dark-colored SUV begins turning left from the opposite lane toward an interse...

### Example 5

- query_id: `vru:medium:0044`
- clip_id: `vru_accident:CAP_DATA:VRU_154`
- supporting_text: The pedestrian, a male dressed in dark clothing including a black jacket and pants, suddenly dashes into the road from the right side of a multi-lane urban asphalt street, which has wet patches and partially snow-covered sidewalks and shoulders. The weather is overcast and cold, as suggested by the bare trees and residual snow along the roadside. A blue sedan is stopped in the right lane ahead of the dashcam vehicle. At this moment, the pedestrian begins rapidly crossing diagonally from right...

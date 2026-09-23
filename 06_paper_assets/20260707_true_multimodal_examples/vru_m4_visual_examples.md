# vru M4 Visual Examples

| strategy | query_id | difficulty | query_text | rank | clip_id | frame_id | evidence_timestamp_sec | evidence_frame_path | media_path | score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M4_metadata_prefilter_visual | vru:medium:0040 | medium | Find videos where the accident type is car hits pedestrian on a arterials road. | 1 | vru_accident:MANUAL_DATA:VRU_215 | vru_accident_MANUAL_DATA_VRU_215:kf03 | 4.45 | Datasets/processed/vru_accident/20260706/keyframes/clip4_full/frames/vru_accident_MANUAL_DATA_VRU_215/kf03_f000089.jpg | /home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/raw/VRU-Accident/VRU_videos/MANUAL_DATA/VRU_215.mp4 | 0.3267006576061249 |
| M4_metadata_prefilter_visual | vru:medium:0041 | medium | Find videos where the accident type is ego-car hits a crossing pedestrian on a arterials road. | 4 | vru_accident:MANUAL_DATA:VRU_261 | vru_accident_MANUAL_DATA_VRU_261:kf02 | 6.45 | Datasets/processed/vru_accident/20260706/keyframes/clip4_full/frames/vru_accident_MANUAL_DATA_VRU_261/kf02_f000129.jpg | /home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/raw/VRU-Accident/VRU_videos/MANUAL_DATA/VRU_261.mp4 | 0.32682380080223083 |
| M4_metadata_prefilter_visual | vru:medium:0042 | medium | Find videos where the accident type is car hits pedestrian on a intersection road. | 3 | vru_accident:MANUAL_DATA:VRU_316 | vru_accident_MANUAL_DATA_VRU_316:kf02 | 4.65 | Datasets/processed/vru_accident/20260706/keyframes/clip4_full/frames/vru_accident_MANUAL_DATA_VRU_316/kf02_f000093.jpg | /home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/raw/VRU-Accident/VRU_videos/MANUAL_DATA/VRU_316.mp4 | 0.3246825337409973 |
| M4_metadata_prefilter_visual | vru:medium:0043 | medium | Find videos where the accident type is car hits cyclist on a intersection road. | 2 | vru_accident:MANUAL_DATA:VRU_72 | vru_accident_MANUAL_DATA_VRU_72:kf01 | 1.65 | Datasets/processed/vru_accident/20260706/keyframes/clip4_full/frames/vru_accident_MANUAL_DATA_VRU_72/kf01_f000033.jpg | /home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/raw/VRU-Accident/VRU_videos/MANUAL_DATA/VRU_72.mp4 | 0.3309454321861267 |
| M4_metadata_prefilter_visual | vru:medium:0044 | medium | Find videos where the accident type is car hits pedestrian on a T-junction road. | 1 | vru_accident:MANUAL_DATA:VRU_242 | vru_accident_MANUAL_DATA_VRU_242:kf03 | 10.4 | Datasets/processed/vru_accident/20260706/keyframes/clip4_full/frames/vru_accident_MANUAL_DATA_VRU_242/kf03_f000208.jpg | /home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/raw/VRU-Accident/VRU_videos/MANUAL_DATA/VRU_242.mp4 | 0.32771390676498413 |

## Supporting Text

### Example 1

- query_id: `vru:medium:0040`
- clip_id: `vru_accident:MANUAL_DATA:VRU_215`
- supporting_text: The scene occurs on a wide, multi-lane asphalt urban road with marked pedestrian crosswalks under clear skies and bright daylight. A female adult pedestrian, wearing a white top and dark pants, is initially positioned near the middle of the crosswalk, moving from the right side of the road toward the left. A dark-colored SUV travels straight ahead in the middle lane at an estimated speed of approximately 40 km/h. As the vehicle approaches the crosswalk, the pedestrian briefly hesitates, then...

### Example 2

- query_id: `vru:medium:0041`
- clip_id: `vru_accident:MANUAL_DATA:VRU_261`
- supporting_text: The collision occurs on a dry, multi-lane urban asphalt road under clear sky conditions, with light traffic moving in the same direction. A male pedestrian, dressed in a dark top and pants, initially walks rapidly from the left side toward the crosswalk area diagonally in front of the vehicle. The vehicle, traveling straight at an estimated speed of approximately 30-40 km/h, approaches the marked pedestrian crossing, maintaining a steady trajectory in the rightmost lane. As the pedestrian ent...

### Example 3

- query_id: `vru:medium:0042`
- clip_id: `vru_accident:MANUAL_DATA:VRU_316`
- supporting_text: The crash occurs on a wet, multi-lane asphalt urban road with moderate traffic and clear weather conditions. A group of pedestrians, including an adult male in dark clothing and a child in a red jacket, begins crossing from the left side, moving diagonally across the street. A gray sedan traveling at an estimated speed of 30 km/h approaches from the right, turning left across the pedestrians' path. As the vehicle executes the turn, the male pedestrian is struck near the centerline, causing hi...

### Example 4

- query_id: `vru:medium:0043`
- clip_id: `vru_accident:MANUAL_DATA:VRU_72`
- supporting_text: A male cyclist wearing a dark jacket, pants, and a helmet is seen riding on a dry, multi-lane asphalt urban road under clear weather, with bright sunlight and a blue sky. The road markings and traffic signals are clearly visible. While traveling in the third lane, the cyclist looks back and changes lanes into the second lane. The dashcam vehicle is estimated to be moving at approximately 30–40 km/h, with a distance of less than 20 meters from the cyclist. Although this presented a potentially...

### Example 5

- query_id: `vru:medium:0044`
- clip_id: `vru_accident:MANUAL_DATA:VRU_242`
- supporting_text: The pedestrian, a male dressed in dark clothing including a hooded jacket and pants, stands at the right edge of a multi-lane wet asphalt urban road on an overcast day, with some residual snow along the roadside. He initially faces away from oncoming traffic while positioned near the curb. A vehicle, an older dark-colored sedan traveling at approximately 40-50 km/h in the left-middle lane behind another car, approaches the pedestrian. The pedestrian abruptly steps off the curb, moving diagona...

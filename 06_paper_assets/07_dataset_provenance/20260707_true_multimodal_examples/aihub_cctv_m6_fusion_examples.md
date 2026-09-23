# aihub_cctv M6 Fusion Examples

| strategy | query_id | difficulty | query_text | rank | clip_id | visual_frame_id | evidence_timestamp_sec | evidence_frame_path | media_path | score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M6_text_visual_metadata_rrf | aihub_cctv:medium:0023 | medium | Find night CCTV videos showing a crowd density event. | 1 | aihub_cctv:train:crowd_density_halloween_week_thu:E05_031 | aihub_cctv_train_crowd_density_halloween_week_thu_E05_031:kf02 | 40.93333333333333 | Datasets/processed/aihub_intelligent_cctv/20260706/keyframes/event4_full/frames/aihub_cctv_train_crowd_density_hallow... | /hdd2/KIISE_datasociety/Datasets/raw/aihub_intelligent_cctv/20260706/media/train/crowd_density_halloween_week_thu/E05... | 0.02877846790890269 |
| M6_text_visual_metadata_rrf | aihub_cctv:medium:0024 | medium | Find daytime CCTV videos showing a fall-down event. | 1 | aihub_cctv:train:fall:E02_018 | aihub_cctv_train_fall_E02_018:kf00 | 61.233333333333334 | Datasets/processed/aihub_intelligent_cctv/20260706/keyframes/event4_full/frames/aihub_cctv_train_fall_E02_018/kf00_f0... | /hdd2/KIISE_datasociety/Datasets/raw/aihub_intelligent_cctv/20260706/media/train/fall/E02_018.mp4 | 0.03055037313432836 |
| M6_text_visual_metadata_rrf | aihub_cctv:medium:0025 | medium | Find night CCTV videos showing a fall-down event. | 1 | aihub_cctv:train:fall:E02_007 | aihub_cctv_train_fall_E02_007:kf00 | 61.5 | Datasets/processed/aihub_intelligent_cctv/20260706/keyframes/event4_full/frames/aihub_cctv_train_fall_E02_007/kf00_f0... | /hdd2/KIISE_datasociety/Datasets/raw/aihub_intelligent_cctv/20260706/media/train/fall/E02_007.mp4 | 0.031746031746031744 |
| M6_text_visual_metadata_rrf | aihub_cctv:medium:0026 | medium | Find daytime CCTV videos showing a fight event. | 1 | aihub_cctv:train:fight:E03_015 | aihub_cctv_train_fight_E03_015:kf00 | 60.5 | Datasets/processed/aihub_intelligent_cctv/20260706/keyframes/event4_full/frames/aihub_cctv_train_fight_E03_015/kf00_f... | /hdd2/KIISE_datasociety/Datasets/raw/aihub_intelligent_cctv/20260706/media/train/fight/E03_015.mp4 | 0.02967032967032967 |
| M6_text_visual_metadata_rrf | aihub_cctv:medium:0027 | medium | Find night CCTV videos showing a fight event. | 1 | aihub_cctv:train:fight:E03_001 | aihub_cctv_train_fight_E03_001:kf02 | 52.2 | Datasets/processed/aihub_intelligent_cctv/20260706/keyframes/event4_full/frames/aihub_cctv_train_fight_E03_001/kf02_f... | /hdd2/KIISE_datasociety/Datasets/raw/aihub_intelligent_cctv/20260706/media/train/fight/E03_001.mp4 | 0.03009207275993712 |

## Supporting Text

### Example 1

- query_id: `aihub_cctv:medium:0023`
- clip_id: `aihub_cctv:train:crowd_density_halloween_week_thu:E05_031`
- supporting_text: 상가 골목길에 줄지어 세워진 바리케이드 양쪽으로 20명 이상의 인파가 이동하며 인파밀집이 발생함

### Example 2

- query_id: `aihub_cctv:medium:0024`
- clip_id: `aihub_cctv:train:fall:E02_018`
- supporting_text: 한 사람이 인도를 걷는 도중 중심을 잃고 바닥으로 넘어지면서 쓰러짐

### Example 3

- query_id: `aihub_cctv:medium:0025`
- clip_id: `aihub_cctv:train:fall:E02_007`
- supporting_text: 2명이 함께 걷다가 흰옷을 입은 사람이 횡단보도 근처에서 쓰러짐

### Example 4

- query_id: `aihub_cctv:medium:0026`
- clip_id: `aihub_cctv:train:fight:E03_015`
- supporting_text: 놀이터에서 세 사람 중 한 사람이 싸움을 지켜보고 있고 두 사람은 뒤엉켜 싸우며 바닥을 구르다가 한 사람이 다른 한 사람의 위에 올라타 있음

### Example 5

- query_id: `aihub_cctv:medium:0027`
- clip_id: `aihub_cctv:train:fight:E03_001`
- supporting_text: 두 사람이 공격을 주고받으며 싸움을 벌이며 운동장 이곳저곳을 돌아다니다가 카메라 화면 바깥으로 이탈함./두 사람이 카메라 화면에 진입한 후 한 사람이 다른 한 사람의 목을 감아 운동장 바닥에 넘어뜨리고 똥침을 놓음.

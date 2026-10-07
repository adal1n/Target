# Glitchcore Nightmare – Maretu-style Arrangement (Inst.)

보컬 없는 인스트. 카사네 테토 얹는 용도.

## 기본 정보
| 항목 | 값 |
|---|---|
| Key | D minor (화성단음계, C# 사용) |
| BPM | **201.36** (원곡 펄스 100.68의 2배, 하프타임으로 찍으면 100.68) |
| 박자 | 4/4, 152마디, 약 3:05 |
| 원곡 정렬 | 이 곡 0:00 = 원곡 약 0.74초(첫 다운비트). 원곡 1마디 = 이 곡 2마디 |

원곡 화성/구조를 그대로 따라가서, 원곡 보컬 멜로디를 따서 테토로 얹으면 마디 단위로 맞음.

## 구성 / 코드 (마디 = 201 BPM 기준)
| 섹션 | 마디 | 시작 | 코드 (1마디씩) | 편곡 포인트 |
|---|---|---|---|---|
| Intro | 1–8 | 0:00 | Dm Dm C#dim A Bb Bb Gm A | 오르골 훅 + 라디오 필터 피아노, LP 노이즈, 스터터 → 리버스 심벌 |
| A (Verse 1) | 9–32 | 0:09.5 | Dm Dm C F Bb Bb Gm Gm / Dm Dm F F Bb Bb A A ×2 | 하프타임 드럼, 피아노 오프비트 스탭, 후반 팜뮤트 기타 |
| B (Pre) | 33–48 | 0:38.1 | Bb Bb C C Dm A Dm Dm Bb Bb Gm Gm A A A A | 16분 피아노 상행, 스트링 스타카토, 스네어롤+라이저, **마지막 2박 완전 정지** |
| Chorus 1 | 49–64 | 0:57.2 | Bb Bb C C Dm Dm A A Bb Bb C C Dm Dm Dm Dm | 풀템포 백비트, 2옥타브 피아노 런, 파워코드, 스퀘어 아르페지오, 오케스트라 히트 |
| Interlude | 65–72 | 1:16.3 | Bb Bb C C Dm Dm Dm Dm | 글리치 훅(크로매틱 하행 꾸밈음), 비트크러시, 스터터, **테이프스톱** |
| A2 (Verse 2) | 73–96 | 1:25.8 | Gm Gm A A Dm Dm C C Bb Bb C C Dm×4 Bb Bb A Gm Dm×4 | 스트링 패드 추가 |
| B2 (Pre) | 97–112 | 1:54.4 | Bb Bb A A Bb Bb A A Bb Bb C C Dm C#dim Dm Dm | B와 동일 빌드 |
| Chorus 2 | 113–128 | 2:13.5 | Bb Bb C C Dm Dm F A Bb Bb Bdim C Dm Dm F#dim A | + 콰이어 |
| C (Bridge) | 129–138 | 2:32.6 | Gm Gm Gm A A Bb Bb C C#dim C#dim | 피아노 솔로 + 콰이어 + 오르골, 후반 탐/스네어 빌드, 마지막 박 정지 |
| Last Chorus | 139–150 | 2:44.5 | Dm Dm C#dim C#dim C C Bdim Bdim Bb Bb A A | 라멘트 베이스(D→C#→C→B→Bb→A), 블래스트비트 4마디, 한 옥타브 위 피아노 |
| End | 151–152 | 2:58.8 | Dm | 오케스트라 히트 → 테이프스톱 → 오르골 잔향 |

## 파일
- `inst_mix.mp3` – 인스트 완성본 (320k)
- `stems/` – 악기별 스템 12개 (piano, musicbox, bells, guitar, bass, arp, strings, choir, orch, lead, drums, fx). 같은 길이, 0:00 정렬, 이펙트/리버브 포함
- `arrangement.mid` – 전 트랙 MIDI (GM 음색, 섹션 마커 포함). DAW에서 음원 교체용
- `arrangement.musicxml` / `arrangement_score.pdf` – 총보 (Hook, Piano RH/LH, Guitar, Strings, Bass, Drums + 코드/리허설 마크)
- `scripts/` – 분석 → 편곡 → 합성/믹스 → 악보 스크립트
- `data/` – 편곡 이벤트(`arr.json`), 원곡 마디별 코드 분석(`bars.json`)

## 테토 얹을 때 팁
- 기타/스트링은 2.2kHz 부근을 3–4dB 미리 파 놨음 → 테토 존재감 대역
- 테토 음역: 코러스는 D5–A5 근처가 믹스상 잘 뚫림. 훅(오르골/벨)은 A5–E6라 멜로디가 겹치면 해당 스템 볼륨 낮추기
- Pre 마지막 2박 / Bridge 마지막 1박은 완전 무음 → 테토 솔로 한 마디 넣기 좋은 자리
- Interlude(65–72)는 보컬 쉬는 구간으로 설계

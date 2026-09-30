# ActImagine VX Encoder/Decoder Tool

A tool to unpack and repack `.vx` video files — one of the video formats used in Nintendo DS games (e.g. Final Fantasy Crystal Chronicles: Ring of Fates) — so you can replace frames/audio and rebuild a playable `.vx` file.

Drag a `.vx` file onto the program to unpack it into PNG frames + WAV audio.
Drag an unpacked folder onto the program to repack it back into a `.vx` file (any `.wav` in the folder is used as the audio track automatically).

Built on top of [CharlesVanEeckhout/actimagine](https://github.com/CharlesVanEeckhout/actimagine) (GPL-3.0). This version fixes a decode/encode drift bug in the library's inter-frame prediction code and adds a working inter-prediction encoder strategy, cutting repacked file size by roughly 2.5x compared to the original all-keyframe-only encoder, with no visible quality loss.

## Usage

- **GUI**: run `ActImagineVXTool.exe` (or `python actimagine_vx_tool.py`) with no arguments for a simple picker window.
- **Drag & drop**: drop a `.vx` file or an unpacked folder onto the exe.
- **CLI**: `python actimagine_vx_tool.py <file.vx | unpacked_folder>`

## License

GPL-3.0 (same as the original library) — see [LICENSE](LICENSE).

---

## ActImagine VX 인코더/디코더 툴

NDS 게임(예: Final Fantasy Crystal Chronicles: Ring of Fates)에서 쓰이는 영상 포맷 중 하나인 `.vx` 파일을 언패킹/리패킹하는 툴입니다. 프레임/오디오를 교체한 뒤 재생 가능한 `.vx`로 다시 빌드할 수 있습니다.

`.vx` 파일을 프로그램에 드래그하면 PNG 프레임 + WAV 오디오로 풀리고, 언패킹된 폴더를 드래그하면 다시 `.vx`로 합쳐집니다(폴더 안의 `.wav`는 자동으로 오디오 트랙으로 인식됨).

[CharlesVanEeckhout/actimagine](https://github.com/CharlesVanEeckhout/actimagine)(GPL-3.0) 기반. 원본 라이브러리의 인터프레임 예측 코드에 있던 인코더-디코더 불일치(드리프트) 버그를 고치고, 실제로 동작하는 인터프레임 예측 인코더를 추가해서 화질 손실 없이 기존 키프레임 전용 인코더 대비 파일 크기를 약 2.5배 줄였습니다.

## 사용법

- **GUI**: 인자 없이 `ActImagineVXTool.exe`(또는 `python actimagine_vx_tool.py`) 실행 시 간단한 선택 창이 뜹니다.
- **드래그 앤 드롭**: `.vx` 파일이나 언패킹된 폴더를 exe에 드래그하세요.
- **CLI**: `python actimagine_vx_tool.py <file.vx | unpacked_folder>`

## 라이선스

GPL-3.0 (원본 라이브러리와 동일) — [LICENSE](LICENSE) 참고.

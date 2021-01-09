# sort-dvr

sort-dvr is a simple (for now command line only) tool based on [OpenCV](https://github.com/opencv/opencv), [tesseract](https://github.com/tesseract-ocr/tesseract) and [ffmpeg](https://github.com/FFmpeg/FFmpeg) which attempts to clean up your DVR recordings automatically sort them by model without any input required from you.

## What it can do

- Read model name from DVR
- Automatically organize the videos in folders based on model names (\<model-name\>/#\<recording-number\>.mp4)
- Remove video noise from the beginning and end of your recording
- Split videos that contain multiple recordings into separate files
- Generate some simple video stats
- Convert videos to h.265 to save quite a significant amount of disk space (~ 50% - 70% with no visible quality loss)
- Upscale the video to 720p (720 pixels height, width calculated based on that)

## What it can't do

- Handle digital DVRs / GoPro recordings
  - Some of the processing is relying on specifics of analog video & analog OSD, thus there could be some errors for digital videos
- Be fast
  - The program is intended to be run on a NAS / Server, so a minute or two longer per video doesn't really matter
  - It isn't sluggish either, a PAL ~4m dvr recording from a SkyZone Sky03S is completely processed and rendered in about 2:30m on a 2020 MacBook Pro with an i9
- Be 100% accurate
  - As with anything there is never a 100% guarantee for anything. sort-dvr calculates a confidence score for the modelname extractions, as well as a similarity score to the modelnames. Based on those factors it quite conservatively decides whether the result is usable or not.
  - The user is notified about any unsure results and the recordings won't be processed in this case

## Prerequisites

You need to enable the model name in your OSD and set it to your desired foldername (modelname recommended). The names shouldn't be too similar as they may confuse the tool - Racer #1, Racer #2 and Racer #3 will most likely yield a lot of false detections. You should be fine if more than 3 characters are different.

By default sort-dvr will search the red area in the image for the name, this works fine for NTSC and PAL if you have one text-line space to the top of the screen and the name centered. There shouldn't be any another text visible in the red area. If you have your text placed in a different area you have to adjust the first two numbers in [this line](https://github.com/UnchartedBull/sort-dvr/blob/main/read_modelname.py#L31).

You can view the cutout generated in the `name-masks` folder and adjust your cutout according to that.

![dvr name location](https://github.com/UnchartedBull/sort-dvr/blob/master/dvr-name-position.jpg?raw=true)

## Installation

1. [Install ffmpeg](https://github.com/adaptlearning/adapt_authoring/wiki/Installing-FFmpeg)
2. [Install tesseract](https://www.pyimagesearch.com/2017/07/03/installing-tesseract-for-ocr/)
3. Clone this repository

   `git clone https://github.com/UnchartedBull/sort-dvr.git`

4. Install dependencies

   `pip install -r requirements.txt`

## Usage

```
index.py [-h] [--model MODEL] [--x265-quality X265_QUALITY] [--audio-bitrate AUDIO_BITRATE] [--skip-split] [--dry-run] [--debug] input output unsure

easily sort your dvr recordings without any effort

positional arguments:
  input                 input folder or file which should be processed
  output                output folder to which the sorted recordings should be saved
  unsure                unsure folder which is used to store videos that could not be processed

optional arguments:
  -h, --help            show this help message and exit
  --model MODEL         manually specify model (skip OCR)
  --x265-quality X265_QUALITY
                        x265 quality (ffmpeg crf, lower means higher quality, default: 28)
  --audio-bitrate AUDIO_BITRATE
                        audio bitrate to be used (default: 32k)
  --skip-split          don't check for video splits
  --dry-run             don't render or move video files, just analyse
  --debug               turn on debug log statements
```

### TL;DR

Create 3 sub-folders (input, output, unsure) and put your dvr recordings in the input folder then run: `python3 index.py ./input ./output ./unsure`. Go grab a coffee and wait.

## Example

Processing of 4 DVR recordings (2 containing one video each and 1 containing 3 videos). The videos are from four different quads. `VID0002.AVI` does not have any name in the DVR recording, while the other three all have the model name in the specified area.

## Hardware Requirements

Around 600MB (~300MB for ffmpeg, ~250MB for sort-dvr) of memory and 1+ CPU core (ffmpeg does at least some multi-threading, sort-dvr is single-threaded). It should run on almost any hardware as long as ffmpeg and h.265 encoding is supported (even a Raspberry Pi probably).

## Backlog

- [x] Basic Functionality
- [x] Split recordings
- [ ] Delete files that have been successfully processed
- [ ] Watch folder for changes
- [ ] Save results to database
- [ ] A small web frontend to run sort-dvr truly headless
- [ ] dockerize sort-dvr

# bran-gta6-forecast

[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/cuanzzlagi/bran-gta6-forecast/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/cuanzzlagi/bran-gta6-forecast/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

An hour-by-hour Twitch viewer forecast for Grand Theft Auto VI's launch
day, built by an AI agent for make.fun's [Forecast GTA VI's launch-day
Twitch viewers hour by hour](https://make.fun/bounty/gta6-twitch-ccu-forecast-01)
bounty.

## Method

A launch day has a shape. For every comparable past launch in the case
file, the program takes its release-day hourly viewers, aligns them by UTC
hour, and divides by that launch's own hour-1 count. The weighted median of
those ratios at each hour (midnight-local rolling unlocks weigh double —
that is how GTA VI unlocks) is the typical day-shape; the spread of the log
ratios is the uncertainty. The forecast is the case's hour-1 print times
the shape, with the five quantiles from the spread. The case game's own
category history is excluded — a premiere is not a launch day.

## Run it

```sh
python3 main.py   # reads $MAKEFUN_INPUT_DIR (or /input), writes $MAKEFUN_OUTPUT_DIR (or /output)
```

Standard library only, no network.

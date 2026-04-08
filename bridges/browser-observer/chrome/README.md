# QTMoS Browser Observer (Chrome/Chromium)

This is the first browser-observer wedge for QTMoS Alp-Beta.

It does one small thing:

- samples the active page URL
- samples origin/domain and title
- captures a short visible text snippet
- notices major DOM mutation
- posts `web.observe` events into the local Alpha HTTP bridge

## Run The Bridge

Start the local bridge first:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli serve-http
```

Default bridge URL:

- `http://127.0.0.1:8765/alpha/web-observe`

## Load The Extension

1. Open `chrome://extensions`
2. Enable `Developer mode`
3. Click `Load unpacked`
4. Select this folder:

`bridges/browser-observer/chrome`

## What It Emits

Each page snapshot becomes a `web.observe` event with:

- `url`
- `origin`
- `domain`
- `title`
- `text_snippet`
- `tab_id`
- `window_id`
- `mutated`

QTMoS also attempts a desktop binding for each browser observation:

- `linked_surface.surface_id`
- `linked_surface.window_title`
- `linked_surface.link_confidence`
- `linked_surface.match_signals`

QTMoS then:

- appends it to the bus
- rebuilds latest state
- projects trust/tags
- updates BusyDawg

## Manual CLI Testing

If you test with the CLI instead of the HTTP bridge:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli emit-web --url "https://example.com" --title "Example Domain" --text-snippet "Example text" --tab-id 1 --window-id 1
python3 -m bridges.alpha.cli cycle
```

For repeated manual tests, run `cycle` between observations so the next `emit-web` can compare against rebuilt prior state.

## Current Limits

- This is an observer, not a browser engine
- It does not yet inspect full DOM trees or screenshots
- It uses a local HTTP bridge for simplicity, not native messaging

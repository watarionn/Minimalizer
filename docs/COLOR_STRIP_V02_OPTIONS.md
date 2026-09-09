# Color Strip v0.2 options

Color Strip v0.2 keeps the v0.1 default output unchanged while adding three opt-in layout controls.

## Defaults

- bar size: `equal`
- order: `least_first`
- orientation: `vertical`

These defaults preserve the original Color Strip behavior: select the 3–5 most-used colors, render the selected colors from least-used to most-used, use equal bar sizes, and stack them vertically.

## Options

### Bar size

- `equal`: every selected color receives the same bar size.
- `proportional`: bar size follows the selected color's source share. Shares are normalized across the selected colors so the strip always fills the output canvas. A minimum pixel is reserved for each selected color when the output dimension allows it.

### Order

- `least_first`: least-used selected color first.
- `most_first`: most-used selected color first.

### Orientation

- `vertical`: bars are stacked from top to bottom.
- `horizontal`: bars are arranged from left to right.

## Web API form fields

- `color_size_mode=equal|proportional`
- `color_order=least_first|most_first`
- `color_orientation=vertical|horizontal`

The fields are accepted only when `mode=color_strip`.

## Safety boundary

Standard and Rinka Reference processing paths are unchanged. Color Strip remains an independent color-only path.

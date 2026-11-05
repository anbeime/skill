# The launch film

`launch.html` directs the launch film in a browser: an editorial layer (serif type, numbered beats, a typed prompt, an end card) over two live example pages in iframes, each in film mode with its own `launch` shot. It only moves when the recorder steps it, so every frame is complete.

```sh
node scripts/record.mjs film/launch.html out/launch.mp4 --ss 1 --music freepd:Page2/Calm%20Sketch%20for%20Piano
```

`stills/` holds the film stills the floating grid at the start uses (made with `--stills` from the machine films).

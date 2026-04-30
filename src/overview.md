## Background

Wayland compositors are really promising as a vdesk solution, my initial approach
of a forked and vendored Weston's vnc backend + gtk-vnc as a client is really
complicated to maintain.


## New Approach

I want to see if I can:
- Switch to an unforked-compisitor
- Replace the VNC-transport and VNC client, with direct
   wayland extension calls from PyEzDesk.

To do this, we need a compositor that's:
- Widely distributed
- Supports screencopy, virtual keyboard, and virtual pointer extensions

## Proposed Setup

- Labwc as the wayland compositor

## Tests

- Verify labwc  headless backend runs well on my PC
    - TODO

- Test labwc for wayland extensions: screencopy, virtual keyboard, and virtual pointer.
    - Done

- Verify wayland screencopies are quick.
    - Done

### App Based Desktop Test

- To verify the desktop provides correct input and screen reading, we'll
write a test sdl app that:
    - Runs in fullscreen
    - Puts a fixed pixel pattern on the screen
    - Records all of input events it receives to a test log file
- Then we'll use this app to write desktop tests that verify the desktop can
  be setup and controlled with a target app running on it.

  ## Open Questions

  Can / does our solution handle concurrent desktops? Is wayland's global/singleton implementation a blocker?


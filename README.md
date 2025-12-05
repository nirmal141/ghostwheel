# GhostWheel 🏎️💨

**They said Python was too slow for real-time racing. I gave myself 60 minutes to prove them wrong.**

This isn't just a computer vision demo. It's a low-latency, high-performance steering engine built for [Slowroads.io](https://slowroads.io).

## The Problem: Latency
Most CV scripts are sluggish. In a driving game, 200ms of lag isn't just annoying—it's a crash. I didn't want a tech demo; I wanted a *controller*.

## The Solution: Speed Hacks
I engineered this to run fast. Really fast.
*   **Threaded Architecture**: Vision runs on one thread, input control runs on another at ~100Hz.
*   **PWM Steering**: Keyboards are binary (0/1). I wrote a custom Pulse Width Modulation algorithm to fake analog steering.
*   **Zero Fluff**: No skeletons, no fancy overlays. Just the data we need to drive.

## Tech Stack
*   Python 3
*   OpenCV (Vision)
*   MediaPipe (Hand Tracking)
*   PyAutoGUI (Input Injection)

## Setup
1.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  Run the engine:
    ```bash
    python main.py
    ```
3.  Open [Slowroads.io](https://slowroads.io), pick a car, and drive.

## Controls
*   **Steer**: Hold hands up like a steering wheel. Rotate to turn.
*   **Gas**: Clench **both fists**.
*   **Brake**: Open hands completely (or drop them).
*   **Quit**: Press `q`.

Built in < 1 hour. Ship fast. Optimize ruthlessly.

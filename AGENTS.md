# Pico Cat Feeder — Codex Instructions

## Project Overview

A simple automated cat feeder controlled by a Raspberry Pi Pico W.

The Pico W runs MicroPython and hosts a local webpage for configuring scheduled relay activation.

The existing feeder and motors are already built. The Pico W only needs to activate a relay at specified times for specified durations.

## Hardware

- Raspberry Pi Pico W (RP2040)
- GPIO-controlled relay
- Existing motorized cat feeder

## Technology

- MicroPython
- Built-in MicroPython libraries
- Vanilla HTML, CSS, and JavaScript
- JSON configuration storage
- Git for version control
- mpremote for uploading firmware

## Core Requirements

Three feeding intervals:

- Breakfast
- Lunch
- Dinner

Each interval must support:

- Enable/disable toggle
- Configurable time of day
- Feeding duration from 1 to 5 seconds

The Pico W must:

- Host its own configuration webpage.
- Save settings that survive reboots.
- Maintain accurate local time.
- Activate the relay according to the saved schedule.
- Prevent duplicate feeding events.
- Operate independently of a connected computer.

## Development Rules

### 1. Minimalism Is Mandatory

This is a microcontroller project, not a web application requiring a software ecosystem.

- No frameworks.
- No npm, React, Flask, or similar technologies.
- No package installations without explicit permission.
- No external dependencies unless absolutely necessary and approved.
- No build systems.
- No unnecessary files or directory structures.
- No speculative features.
- No premature optimization.

Prefer straightforward procedural code over elaborate abstractions.

### 2. Preserve Existing Functionality

The existing `main.py` contains a working web server and user interface.

- Do not rewrite working code unnecessarily.
- Prefer small, targeted changes.
- Preserve the existing webpage layout.
- Do not introduce unrelated changes.
- Do not reorganize the project without permission.

### 3. Incremental Development

Implement one feature at a time.

For each task:

1. Inspect the relevant existing code.
2. Explain the proposed approach briefly.
3. Implement only the requested feature.
4. Check for errors and MicroPython compatibility.
5. Explain what changed.
6. Identify any required hardware tests.

Do not begin the next development milestone automatically.

### 4. Dependencies and Resource Usage

The Raspberry Pi Pico W has limited RAM and storage.

- Prefer built-in MicroPython modules.
- Minimize memory allocations.
- Avoid unnecessary background tasks.
- Keep HTTP handling lightweight.
- Keep HTML, CSS, and JavaScript simple.
- Do not download frameworks or development tools without permission.

### 5. Security

Wi-Fi credentials are stored in `secrets.py`.

- Never commit `secrets.py`.
- Never display or log Wi-Fi passwords.
- Never hardcode credentials in tracked source files.
- Preserve `.gitignore` protections.

### 6. Hardware Safety

The GPIO relay controls a physical feeding mechanism.

- Relay must default to OFF.
- Relay activation must have a maximum duration.
- Prevent duplicate scheduled activations.
- Do not activate GPIO outputs during development without approval.
- Do not assume relay polarity or GPIO pin assignments.

### 7. Git Workflow

- Do not commit without explicit permission.
- Do not push without explicit permission.
- Keep changes focused on the current task.
- Do not modify unrelated files.
- Do not overwrite working code without explanation.

### 8. Testing

Code running successfully on a Mac does not establish that it works on MicroPython.

- Check compatibility with Pico W MicroPython.
- Distinguish local tests from actual hardware tests.
- Test each milestone on the Pico W.
- Never claim hardware functionality has been verified without testing it.

## Development Milestones

1. Persistent feeding schedule configuration.
2. NTP synchronization and local timekeeping.
3. GPIO relay activation.
4. Automatic feeding scheduler.
5. Reliability testing.

Complete and verify each milestone before beginning the next.

## Guiding Principle

Build the simplest implementation that reliably meets the requirements.

Do not turn a basic scheduled relay controller into a complicated software project.
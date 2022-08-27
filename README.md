# Manokee

Audio recording software with a mobile-first web interface

:warning: **Manokee is still under early development** :warning:

You can use Manokee to conveniently record audio material, and then import this material into your favorite Digital Audio Workstation for mixing and mastering.

Manokee is going to be a handy tool if using a DAW for a recording session is not too convenient for you. For example, if you're doing home recording, Manokee lets you control the recording session from a browser on a mobile phone. You can wire up all the equipment (instruments, microphones, the audio interface) to the computer, run Manokee, and then access the Manokee user interface on your phone. This setup can be more accessible and convenient than doing everything with the keyboard and mouse on your computer.

My vision for Manokee is to make it a musical creativity assistant. An application that could let you improvise and save your musical ideas without too much distraction. You could compose and record a song from ideas to a complete arrangement in Manokee, and finally export the session to a DAW for mixing.

# Installation

## Fedora

```bash
# Install system-wide dependencies
sudo dnf install -y alsa-lib-devel gcc-c++ git npm pipewire-jack-audio-connection-kit-devel poetry python3-devel swig

# Clone the repo
git clone https://github.com/smiszym/manokee.git
cd manokee

# Install npm packages for the frontend
(cd manokee/web/front && npm install)

# Build the frontend
(cd manokee/web/front && npm run build-dev)

# Install Python packages
LIBRARY_PATH=/usr/lib64/pipewire-0.3/jack poetry install
```

# Running

From within the project directory:

```bash
poetry run python -m manokee
```

Then navigate in a browser on your mobile phone to the address printed in the console. You can also just scan the printed QR code.

> :warning: The user interface is very energy-consuming! Your mobile phone can quickly discharge.

> :information_source: Manokee uses the [AMIO Python package](https://github.com/smiszym/amio) for audio input/output. AMIO currently only supports [JACK](https://jackaudio.org/) as the underlying audio API. Traditionally, you would need to manually start the JACK server (either from the command line or using [QJackCtl](https://github.com/rncbc/qjackctl)) before you can use Manokee. However, the recent releases of Fedora Workstation have PipeWire (which exposes JACK-compatible API) as the default audio system, so you don't have to do anything.

# Author

Michał Szymański, 2020-2022

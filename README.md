Manokee -- Audio recording software with a mobile-first web interface

**Manokee is still under early development**

Michał Szymański, 2020

Install the necessary npm packages for the frontend with:

    $ (cd manokee/web/front && npm install)

Build the frontend with:

    $ (cd manokee/web/front && npm run build-dev)

Run the backend (which will also serve the frontend files) with:

    $ python3.7 -m manokee

Currently, the only supported audio backend is [JACK|https://jackaudio.org/].
Start JACK daemon (either from the command line or using
[QJackCtl|https://github.com/rncbc/qjackctl]).

Navigate in your browser to the address printed in the log. This is Manokee
user interface. Currently I recommend loading the mobile version (e.g.,
with your phone), as that's what I focus on when designing.

First, go to "More" > "Status" and turn on the Audio I/O. If Manokee
successfully connects to JACK, it will turn green. Then you can start adding
tracks from the "Track edit mode". It can be found under "More" > "Session".
Then leave the track edit mode, mark some track for recording and start
recording.

The audio won't get written onto the track until you commit it. You can do
that under "More" > "Recorded fragments" section.

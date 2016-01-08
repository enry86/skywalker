Skywalker
=========

Computer vision based telescope auto-guiding system

Introduction
------------

Taking photographs of deep-space objects with a DSLR through
a telescope is hard. Or at least I found it hard in my own
experience, I know there is people out there who consider
this a piece of cake, but hey I'm a noob here...

The main obstacle is to keep the desired object firmly in the
center of the camera field of view for quite a long time.
In fact, usually, a picture of a faint object like a nebula
or a galaxy needs an exposure of some minutes.
It's impossible to rely exclusively on the tracking motor,
since on most mounts (or at least in my own mount) it's just
not accurate enough.

The solution is to attach a secondary optics to the telescope,
which is used by a control system to evaluate the tracking
error and to feed corrections to the tracking system.

This projects aims at implementing that control system,
which takes images from the secondary scope, evaluates
the amount of shift between consecutive images and
controls the speed of the tracking motor accordingly.

Requisites
----------

I'm implementing this system using the components I have at hand,
so I'm going to employ a Venus USB webcam to caputre still frames
from the guide telescope.

The tracking motor will be controlled by an Arduino board
equipped with a motor shield. Which in turn communicates with the main
system through serial USB connection.

I'm considering only GNU/Linux as target platform.

Final thoughts
--------------

I'm developing this project for my personal use, targeting my
instrumentations and their specific issues.
Therefore I don't think someone else could
gain something out of this work, which is kind of sad.
Anyway I still hope that it may serve as inspiration to
other stargazers out there.




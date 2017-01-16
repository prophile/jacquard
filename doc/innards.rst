Innards
=======

Here be dragons. This page contains some internal scribblings and may or may
not make any sense, dependent on your knowledge of the codebase and/or history
of consuming mind-expanding hallucinogenic drugs.

Subsystem dependencies
----------------------

.. digraph:: Subsystems

    cli -> commands
    cli -> plugin
    plugin -> config [label = "to be fixed"];
    wsgi -> service
    service -> commands
    service -> users
    service -> experiments
    service -> storage
    service -> directory
    directory -> plugin
    config -> directory
    config -> storage
    users -> experiments
    users -> directory
    experiments -> storage

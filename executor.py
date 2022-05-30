import threading

from arkhandler import ArkHandler


def threader(widget, loop, config):
    threading.Thread(target=executor1, args=(widget, loop, config,)).start()


def executor1(widget, loop, config):
    at = ArkHandler(widget, config)
    loop.create_task(at.event_puller())
    loop.create_task(at.watchdog())
    loop.create_task(at.update_checker())
    loop.create_task(at.wipe_checker())
    loop.run_forever()

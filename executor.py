import threading
import asyncio
from arkhandler import ArkHandler

LOG = []


def threader(widget, loop):
    threading.Thread(target=executor1, args=(widget, loop,)).start()


def executor1(widget, loop):
    at = ArkHandler(widget)
    loop.create_task(at.event_puller())
    loop.create_task(at.watchdog())
    loop.create_task(at.update_checker())
    loop.run_forever()


async def task1(widget):
    global LOG
    while True:
        for i in range(100):
            LOG.append(i)
            events = LOG
            if len(LOG) > 7:
                events = LOG[-7:].copy()
                LOG = events
            text = ""
            for item in events:
                text += f"{item}\n"
            widget.configure(text=text)
            await asyncio.sleep(0.5)


async def task2():
    while True:
        for i in range(100):
            print(f"running {i}")
            await asyncio.sleep(1)
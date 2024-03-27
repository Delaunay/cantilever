import asyncio

import win32clipboard


async def iterate_overclipboard():
    win32clipboard.OpenClipboard()
    previous = win32clipboard.GetClipboardData()
    win32clipboard.CloseClipboard()

    while True:
        try:
            win32clipboard.OpenClipboard()
            data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
        except:
            data = previous

        if data == previous:
            await asyncio.sleep(0.1)
            continue

        yield data
        previous = data


async def clipboard():
    with open("magnets.txt", "w") as f:
        async for value in iterate_overclipboard():
            f.write(f"{value}\n")
            print(value)
            f.flush()


loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(clipboard())
finally:
    # see: https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.shutdown_asyncgens
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()

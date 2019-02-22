from logger import create_logger
from proxyserver import ProxyServer
from ggserver import GGServer
from threading import Thread
import sys

if __name__ == '__main__':
    logger = create_logger("__main__")

    logger.info("pyGadu - simple Gadu-Gadu server implementation")
    logger.info("-----------------------------------------------")
    logger.info("")

    # Reat args
    if len(sys.argv) > 1:
        logger.info("Application started...")
    else:
        logger.critical("You need specify remote address!")
        logger.critical("eg. python pygadu.py 127.0.0.1")
        exit(1)

    addr = sys.argv[1]

    # Create Proxy server thread
    proxy_server = ProxyServer(addr, 8080)
    proxy_server_thread = Thread(
        target=proxy_server.listen,
        daemon=False
    )
    proxy_server_thread.start()

    # Create GG server thread
    gg_server = GGServer(addr, 8074)
    gg_server_thread = Thread(
        target=gg_server.listen,
        daemon=False
    )
    gg_server_thread.start()

    while True:
        try:
            if input() == "q":
                break
        except KeyboardInterrupt:
            break

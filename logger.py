import colorlog

logger_format = "%(white)s[%(asctime)s] %(bold_blue)s%(name)-15s%(white)s %(log_color)s%(levelname)-10s%(white)s %(message)s"
logger_datefmt = "%Y-%m-%d %H:%M:%S"
logger_level = "DEBUG"


def create_logger(name):
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        logger_format,
        datefmt=logger_datefmt,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        },
    ))

    logger = colorlog.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(logger_level)

    return logger

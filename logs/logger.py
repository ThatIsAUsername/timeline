import os
from typing import Dict
import logging

loggers: Dict = {}


def get_logger(name: str = None):

    name = name or "timeline"

    global loggers
    if name in loggers:
        return loggers[name]

    new_logger = logging.getLogger(name)
    new_logger.setLevel(logging.DEBUG)
    c_handler = logging.StreamHandler()
    logfile = os.path.join(os.getcwd(), f"logs/{name}.log")
    if os.path.exists(logfile):
        os.remove(logfile)
    f_handler = logging.FileHandler(logfile)

    c_handler.setLevel(logging.INFO)
    f_handler.setLevel(logging.DEBUG)

    l_format = logging.Formatter("[%(filename)s.%(funcName)s:%(lineno)d: %(levelname)s] %(message)s")
    c_handler.setFormatter(l_format)
    f_handler.setFormatter(l_format)

    new_logger.addHandler(c_handler)
    new_logger.addHandler(f_handler)

    loggers[name] = new_logger
    new_logger.info(f"Initialized {name} logger {logfile}")
    return new_logger

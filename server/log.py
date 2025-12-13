import logging
import os


def init_log():
    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(levelprefix)s %(asctime)s [%(name)s] %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "file": {
                "format": "%(asctime)s [%(levelname)s] [%(name)s:%(module)s:%(lineno)d] %(message)s"
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "DEBUG",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "file",
                "filename": "logs/server.log",
                "maxBytes": 1024 * 1024 * 5,  # 5 MB
                "backupCount": 3,
                "encoding": "utf-8",
                "level": "DEBUG",
            },
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "watchfiles": {
                "handlers": ["console", "file"],
                "level": "WARNING",
                "propagate": False,
            },
            # 为您自己的应用程序代码（例如 app.py, vad/engine.py）设置一个 logger
            "app": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            "vad": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
             "stt": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": "INFO", # 将 root logger 的默认级别提高到 INFO
        },
    }

    logging.config.dictConfig(LOGGING_CONFIG)

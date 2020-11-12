# coding=utf-8
import os
import logging
import logging.config as log_conf
import datetime
import coloredlogs
from settings import DevelopmentConfig as DEVConfig

devConfig = DEVConfig()
coloredlogs.DEFAULT_FIELD_STYLES = {'asctime': {'color': 'green'}, 'hostname': {'color': 'magenta'}, 'levelname': {'color': 'magenta', 'bold': False}, 'name': {'color': 'green'}
         }

if not os.path.exists(devConfig.LOGDIR):
    os.mkdir(devConfig.LOGDIR)
today = datetime.datetime.now().strftime("%Y-%m-%d")

log_path = os.path.join(devConfig.LOGDIR, today + ".log")

log_config = {
    'version': 1.0,
    # 格式输出
    'formatters': {
        'colored_console': {
                        'format': '%(asctime)s %(name)s - ' + 'T%(thread)d - ' + '%(filename)s - ' + '%(lineno)d - ' + '%(levelname)s - %(message)s',
                        'datefmt': '%H:%M:%S'
        },
        'detail': {
            'format': '%(asctime)s %(name)s - ' + 'T%(thread)d - ' + '%(filename)s - ' + '%(lineno)d - ' + '%(levelname)s - %(message)s',
            'datefmt': "%Y-%m-%d %H:%M:%S"  #时间格式
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler', 
            'level': 'INFO',
            'formatter': 'colored_console'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',  
            'maxBytes': 1024 * 1024 * 1024,  # 1G
            'backupCount': 1, 
            'filename': log_path, 
            'level': 'INFO',
            'formatter': 'detail',  # 
            'encoding': 'utf-8',  # utf8 编码  防止出现编码错误
        },
    },

    'loggers': {
        'logger': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },

    }
}

log_conf.dictConfig(log_config)
log = logging.getLogger("logger")


# 这里level的优先级高于console的level优先级，但低于file的level优先级
coloredlogs.install(level='DEBUG', logger=log)
#logger.info("文件")
#logger.info("222")


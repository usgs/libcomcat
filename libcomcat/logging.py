import logging
import logging.config

LEVELDICT = {'debug': logging.DEBUG,
             'info': logging.INFO,
             'warning': logging.WARNING,
             'error': logging.ERROR}


def setup_logger(logfile, level='info'):
    """Setup the logger options.

    This is written to handle a few different situations. It is called by
    command line programs that will hand off the args object. However, it
    may also be used for interactive sessions/notebooks where we want to
    suppress warnings, especially those from dependencies that are out of
    our control. For this, the args object is not available and will be None,
    and we then control the logging verbosity with the level argument (only
    used if args is None).

    Args:
        logfile (str):
            Must contain logging options in gmprocess.args.add_shared_args.
        level (str):
            String indicating logging level; either 'info', 'debug', or
            'error'. Only used if args in None.

    """

    fmt = ('%(levelname)s %(asctime)s | '
           '%(module)s.%(funcName)s: %(message)s')
    datefmt = '%Y-%m-%d %H:%M:%S'
    # create a console handler, with verbosity setting chosen by user
    loglevel = LEVELDICT[level]
    if logfile != 'stderr':
        handler_id = 'filehandler'
        handler = {'level': loglevel,
                   'formatter': 'standard',
                   'class': 'logging.FileHandler',
                   'filename': logfile,
                   }
    else:
        handler_id = 'streamhandler'
        handler = {
            'level': loglevel,
            'formatter': 'standard',
            'class': 'logging.StreamHandler'
        }

    logdict = {
        'version': 1,
        'formatters': {
            'standard': {
                'format': fmt,
                'datefmt': datefmt
            }
        },
        'handlers': {handler_id: handler
                     },
        'loggers': {
            '': {
                'handlers': [handler_id],
                'level': loglevel,
                'propagate': True
            }
        }
    }

    logging.config.dictConfig(logdict)

    # Have the logger capture anything from the 'warnings' package,
    # which many libraries use.
    logging.captureWarnings(True)

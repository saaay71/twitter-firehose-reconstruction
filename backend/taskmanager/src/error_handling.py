import functools
import logging
import pika
import socket
import time
import traceback

# Source: https://github.com/numenta/numenta-apps/blob/46fff2aec40c1a4d122f575ec0e3edeac0456068/nta.utils/nta/utils/error_handling.py
def retry(timeoutSec, initialRetryDelaySec, maxRetryDelaySec,
          retryExceptions=(Exception,),
          retryFilter=lambda e, args, kwargs: True,
          logger=None, clientLabel=""):
  """ Returns a closure suitable for use as function/method decorator for
  retrying a function being decorated.
  timeoutSec:           How many seconds from time of initial call to stop
                        retrying (floating point); 0 = no retries
  initialRetryDelaySec: Number of seconds to wait for first retry.
                        Subsequent retries will occur at geometrically
                        doubling intervals up to a maximum interval of
                        maxRetryDelaySec (floating point)
  maxRetryDelaySec:     Maximum amount of seconds to wait between retries
                        (floating point)
  retryExceptions:      A tuple (must be a tuple) of exception classes that,
                        including their subclasses, should trigger retries;
                        Default: any Exception-based exception will trigger
                        retries
  retryFilter:          Optional filter function used to further filter the
                        exceptions in the retryExceptions tuple; called if the
                        current exception meets the retryExceptions criteria:
                        takes the current exception instance, args, and kwargs
                        that were passed to the decorated function, and returns
                        True to retry, False to allow the exception to be
                        re-raised without retrying. Default: permits any
                        exception that matches retryExceptions to be retried.
  logger:               User-supplied logger instance to use for logging.
                        None=defaults to logging.getLogger(__name__).
  Usage Example:
    NOTE: logging must be initialized *before* any loggers are created, else
      there will be no output; see nupic.support.initLogging()
    _retry = retry(timeoutSec=300, initialRetryDelaySec=0.2, maxRetryDelaySec=10,
                   retryExceptions=[socket.error])
    @_retry
    def myFunctionFoo():
        ...
        raise RuntimeError("something bad happened")
        ...
  TODO: TAUR-439 unit test
  """

  assert initialRetryDelaySec > 0, str(initialRetryDelaySec)

  assert timeoutSec >= 0, str(timeoutSec)

  assert maxRetryDelaySec >= initialRetryDelaySec, \
      "%r < %r" % (maxRetryDelaySec, initialRetryDelaySec)

  assert isinstance(retryExceptions, tuple), (
    "retryExceptions must be tuple, but got %r") % (type(retryExceptions),)

  if logger is None:
    logger = logging.getLogger(__name__)

  def retryDecorator(func):

    @functools.wraps(func)
    def retryWrap(*args, **kwargs):
      numAttempts = 0
      delaySec = initialRetryDelaySec
      startTime = time.time()

      # Make sure it gets called at least once
      while True:
        numAttempts += 1
        try:
          result = func(*args, **kwargs)
        except retryExceptions as e:
          if not retryFilter(e, args, kwargs):
            if logger.isEnabledFor(logging.DEBUG):
              logger.debug(
                '[%s] Failure in %r; retries aborted by custom retryFilter. '
                'Caller stack:\n%s', clientLabel, func,
                ''.join(traceback.format_stack()), exc_info=True)
            raise

          now = time.time()
          # Compensate for negative time adjustment so we don't get stuck
          # waiting way too long (python doesn't provide monotonic time yet)
          if now < startTime:
            startTime = now
          if (now - startTime) >= timeoutSec:
            logger.exception(
              '[%s] Exhausted retry timeout (%s sec.; %s attempts) for %r. '
              'Caller stack:\n%s', clientLabel, timeoutSec, numAttempts, func,
              ''.join(traceback.format_stack()))
            raise

          if numAttempts == 1:
            logger.warning(
              '[%s] First failure in %r; initial retry in %s sec.; '
              'timeoutSec=%s. Caller stack:\n%s', clientLabel, func, delaySec,
              timeoutSec, ''.join(traceback.format_stack()), exc_info=True)
          else:
            logger.debug(
              '[%s] %r failed %s times; retrying in %s sec.; timeoutSec=%s. '
              'Caller stack:\n%s',
              clientLabel, func, numAttempts, delaySec, timeoutSec,
              ''.join(traceback.format_stack()), exc_info=True)

          time.sleep(delaySec)

          delaySec = min(delaySec*2, maxRetryDelaySec)
        else:
          if numAttempts > 1:
            logger.info('[%s] %r succeeded on attempt # %d',
                        clientLabel, func, numAttempts)

          return result


    return retryWrap

  return retryDecorator

RETRY_ON_AMQP_ERROR = retry(
  timeoutSec=30, initialRetryDelaySec=1, maxRetryDelaySec=10,
  retryExceptions=(
    pika.exceptions.AMQPConnectionError,
    socket.gaierror,
    socket.error,
  ),
  logger=logging.getLogger(__name__)
)
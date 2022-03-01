import pyoc
import logging


class LogWrapper(pyoc.Wrapper):
    def __call__(self, *args, **kwargs):

        arg_str_list = list(map(str, args)) + [f"{k}={v}" for k, v in kwargs.items()]

        obj_name = self.target.__self__.__class__.__name__
        method_name = self.target.__name__

        logging.info(f"invoked {obj_name}.{method_name}({','.join(arg_str_list)})")

        return self.next(*args, **kwargs)

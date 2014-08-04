import tempfile, os, shutil, sys, signal, time

# Copyright (C) 2014 Anton Dries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this 
# software and associated documentation files (the "Software"), to deal in the Software 
# without restriction, including without limitation the rights to use, copy, modify, 
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to 
# permit persons to whom the Software is furnished to do so, subject to the following 
# conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies 
#  or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
class WorkEnv(object) :
    """Provides functionality for managing a working directory and a log functionality."""
    NEVER_KEEP=0
    KEEP_ON_ERROR=1
    ALWAYS_KEEP=2
    
    def __init__(self, outdir, persistent=KEEP_ON_ERROR) :
        # persistence :
        #    0: directory is always removed on exit
        #    1: directory is removed, unless exit was caused by an error
        #    2: directory is never removed
        
        self.__outdir = outdir
        self.__persistent = persistent
        
    def __enter__(self) :
        if self.__outdir == None :
            self.__outdir = tempfile.mkdtemp()
            self.log('Using temporary directory', self.__outdir, verbose=1)
        elif not os.path.exists(self.__outdir) :
            os.makedirs(self.__outdir)
        else :  # using non-temporary, existing directory => NEVER delete this
            self.__persistent = self.ALWAYS_KEEP
        return self
        
    def __exit__(self, exc_type, value, traceback) :
        if self.__persistent == self.NEVER_KEEP or (self.__persistent == self.KEEP_ON_ERROR and exc_type == None) :
            shutil.rmtree(self.__outdir)
        
    def out_path(self, relative_filename) :
        return os.path.join(self.__outdir, relative_filename)
        
    def tmp_path(self, relative_filename) :
        return os.path.join(self.__outdir, relative_filename)
        
class Timer(object) :
    def __init__(self, description, logger, time_format='%.3f', verbose=1, max_time=0) :
        # Use max_time to set a timeout => If two timers with timeouts are nested the outer one will not time out.
        self.__description = description
        self.__logger = logger
        self.__time_format = time_format
        self.__message_verbosity = verbose
        self.__exec_time = None
        self.__max_time = max_time
        if self.__max_time > 0 :
            signal.signal(signal.SIGALRM, self.onTimeOut)
            signal.setitimer(signal.ITIMER_REAL, self.__max_time)
    
    total_time = property(lambda s : s.__exec_time)
    
    def __enter__(self) :
        self.__start_time = time.time()
        self.__logger(self.__message_verbosity, self.__description, 'started',msgtype='TIMER')
        return self
    
    def __exit__(self, *args) :
        self.__exec_time = time.time() - self.__start_time
        self.__logger(self.__message_verbosity, self.__description, 'finshed','time:', self.__time_format % self.__exec_time,msgtype='TIMER')
        if self.__max_time > 0 :
            signal.setitimer(signal.ITIMER_REAL, 0)

    def onTimeOut(self, *args) :
        self.__logger(self.__message_verbosity, 'EXECUTION TIMED OUT',msgtype='TIMER')
        raise Timeout("TimeOut during execution of '%s'" % self.__description)
    
class Timeout(Exception) :
    def __init__(self, msg) :
        super(Timeout,self).__init__(msg) 
  
class Logger(object) :
    def __init__(self, verbose=0, sep=' ', file=None) :
        self.verbose = verbose
        self.sep = sep
        if file == None :
            self.file = sys.stdout
        else :
            self.file = file
        
    def _construct_message(self, message) :
        return self.sep.join(map(str,message))
        
    def __call__(self, level, *message, **kwdargs) :
        self.log(level,*message,**kwdargs)
        
    def log(self, level, *message, **kwdargs) :
        msgtype = kwdargs['msgtype'] if 'msgtype' in kwdargs else 'DEBUG'
        if level <= self.verbose :
            self.file.write(msgtype + ': ' + self._construct_message(message) + '\n')
            
    def getData(self) :
        return None
        
    def reset(self) :
        pass
    
class KeyIndexDict(object) :
    def __init__(self) :
        self.__int2key = []
        self.__data = {}
    
    def add(self, key) :
        if not key in self.__data :
            index = len(self.__int2key) + 1
            self.__int2key.append(key)
            self.__data[key] = index
            return index
        else :
            return self[key]
            
    def __getitem__(self, key) :
        return self.__data[key]
        
    def __setitem__(self, key, index) :
        # Ignores given index
        self.add(key)
        
    def __iter__(self) :
        return iter(self.__data)
        
    def __len__(self) :
        return len(self.__data)
        
    def __contains__(self, key) :
        return key in self.__data
        
    def getByIndex(self, index) :
        if index <= 0 :
            raise IndexError
        # throws IndexError
        return self.__int2key[index-1]
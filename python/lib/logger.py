import os

def log(app= '', method = '', message = '', printToLog = False, verbose = True):
    """
    Function to help debug application messages from shotgun to turn them on or off quickly
    Also outputs a log regardless of verbose = True
    """
    if not app:
        if verbose:
            print '# Warning: Shotgun:  Method: {0:<15} {1}'.format(method, message)
        else:
            pass
    else:
        try:
            if verbose:
                if method == '':
                    app.log_warning(message)
                else:
                    app.log_warning('\nMethod:%-15s %s' % (method, message))
            else:
                pass
        except:
            print 'debug msg failed... app sent through okay?'


    ### Write to log file.
    pathToLog = "C:\Temp\changeworkspace_log.txt"

    if printToLog:
        if not os.path.isfile(pathToLog):
            if not os.path.isdir(configCONST.TEMP_FOLDER):
                os.mkdir('%s' % configCONST.TEMP_FOLDER)
            outfile = open(pathToLog, "w")
        else:
            outfile = open(pathToLog, "a")
        outfile.write('Method: %-15s %s\n' % (method, message))
        outfile.close()
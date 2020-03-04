from buildbot.process import results

def success(result, s):
     return (result == results.SUCCESS)

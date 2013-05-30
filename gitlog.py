
import subprocess
from os.path import join
from entry import Entry
import logging

class LoggingError(Exception):
	pass

def getLog(d=None, largs=tuple(), format="%s"):
	args = ["git"]
	if d:
		args.append("--git-dir="+join(d,".git"))
	args.append("log")
	args.extend(largs)
	args.extend(("--format=format:%H:%at:%P:"+format, "--date-order", "--reverse"))
	
	try:
		return subprocess.check_output(args).decode("utf8", "replace")
	except subprocess.CalledProcessError as err:
		raise LoggingError("git log returned status code "+str(err.returncode))

def parseLog(log):
	id2entry = {}
	roots = []
	
	for line in log.splitlines():
		ident, time, parents, msg = line.split(":", 3)
		
		time = int(time)
		parents = parents.split()
		entry = Entry(ident, msg, time)
		id2entry[ident] = entry
		
		for parent_id in parents:
			if parent_id not in id2entry:
				logging.debug("Couldn't find parent %s for entry %s; ignoring parent", parent_id, ident)
				continue
			p = id2entry[parent_id]
			
			entry.parents.append(p)
			p.children.append(entry)
		
		if len(entry.parents) == 0:
			logging.debug("Found root entry: %s", ident)
			roots.append(entry)
	
	return roots

def getGraph(*args, **kwargs):
	return parseLog(getLog(*args, **kwargs))

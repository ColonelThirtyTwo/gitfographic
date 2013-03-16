
import subprocess
from os.path import join
import logging

class Commit(object):
	__slots__ = ("hash", "author", "msg", "time", "parents", "children")
	
	def __init__(self, hsh, author, msg, time, parents=None, children=None):
		self.hash = hsh
		self.author = author
		self.msg = msg
		self.time = time
		self.parents = [] if parents is None else parents
		self.children = [] if children is None else children
	
	def __str__(self):
		return "Commit({0},{1},{2},{3})".format(self.hash, self.author, self.time, self.msg)
	__repr__ = __str__
	
	def __eq__(self, other):
		return self.hash == other.hash
	def __hash__(self):
		return hash(self.hash)

def getLog(d=None, largs=tuple()):
	args = ["git"]
	if d:
		args.append("--git-dir="+join(d,".git"))
	args.append("log")
	args.extend(largs)
	args.extend(("--format=format:%H:%an:%at:%P:%s", "--topo-order"))
	
	return subprocess.check_output(args).decode("utf8", "replace")

def parseLog(log):
	hash2commit = {}
	roots = []
	
	lines = log.splitlines()
	lines.reverse()
	for line in lines:
		hsh, author, time, parents, msg = line.split(":", 4)
		
		time = int(time)
		parents = parents.split()
		commit = Commit(hsh, author, msg, time)
		hash2commit[hsh] = commit
		
		for p_hash in parents:
			if p_hash not in hash2commit:
				logging.debug("Couldn't find parent %s for commit %s; ignoring parent", p_hash, hsh)
				continue
			p = hash2commit[p_hash]
			
			commit.parents.append(p)
			p.children.append(commit)
		
		if len(commit.parents) == 0:
			logging.debug("Found root commit: %s", hsh)
			roots.append(commit)
	
	return roots

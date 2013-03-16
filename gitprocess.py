
import subprocess
from os.path import join

class Commit(object):
	def __init__(self, hsh, author, msg, parents=[], children=[]):
		self.hash = hsh
		self.author = author
		self.msg = msg
		self.parents = parents
		self.children = children
	
	def __str__(self):
		return "Commit({0},{1},{2})".format(self.hash, self.author, self.msg)
	__repr__ = __str__

def getLog(d=None):
	args = ["git"]
	if d:
		args.append("--git-dir="+join(d,".git"))
	args = args + ["log", "--format=format:%H:%an:%P:%s"]
	
	return subprocess.check_output(args)

def parseLog(out):
	hash2commit = {}
	commits = []
	
	lines = out.splitlines()
	lines.reverse()
	for line in lines:
		hsh, author, parents, msg = line.split(":", 3)
		
		commit = Commit(hsh, author, msg)
		hash2commit[hsh] = commit
		
		parents = parents.split()
		for i in range(0,len(parents)):
			assert parents[i] in hash2commit
			p = hash2commit[parents[i]]
			
			commit.parents.append(p)
			p.children.append(commit)
		
		commits.append(commit)
	
	return commits

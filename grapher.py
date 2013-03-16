
import svgwrite
from collections import namedtuple

DEFAULT_STYLE = """
.graph circle {
	fill: white;
	stroke: blue;
	stroke-width: .3mm;
}
.graph line {
	fill: none;
	stroke: blue;
	stroke-width: .5mm;
}
.messages text {
	font-family: monospace;
	font-size: 12pt;
	color: black;
	dominant-baseline: central;
}
"""

class Branch(object):
	def __init__(self, prev, next, x, prevx):
		self.prev = prev
		self.next = next
		self.x = x
		self.prevx = prevx
	
	def setPrev(self):
		assert self.x >= self.prevx
		self.prevx = self.x
	
	@staticmethod
	def key_time(x):
		return x.next.time
	@staticmethod
	def key_x(x):
		return x.x
	
	def __str__(self):
		return "Branch({0},{1},{2},{3})".format(self.prev.hash[:5], self.next.hash[:5], self.x, self.prevx)
	__repr__ = __str__

def updateBranches(branches):
	x = -1
	for branch in branches:
		branch.setPrev()
		if branch.x <= x:
			branch.x = x
			x += 1
		elif branch.x > x:
			x = branch.x+1
	return x

class SvgGraph(object):
	
	def __init__(self, outpath, style=None):
		# Options
		self.commit_r = "1mm"
		self.branch_spacing = 30
		self.entry_height = 25
		self.margin_x = 50
		self.margin_y = 50
		
		# Stuff we need
		self.svg = svgwrite.Drawing(outpath, debug=True)
		self.svg.defs.add(self.svg.style(style or DEFAULT_STYLE))
		
		self.g_graph = self.svg.add(self.svg.g(class_="graph"))
		self.g_graph_lines = self.g_graph.add(self.svg.g(class_="lines"))
		self.g_graph_circles = self.g_graph.add(self.svg.g(class_="circles"))
		self.g_text = self.svg.add(self.svg.g(class_="messages"))
		
	def xform(self,x,y):
		return x*self.branch_spacing, y*self.entry_height
	def drawCommit(self, x,y):
		self.g_graph_circles.add(self.svg.circle(self.xform(x,y),self.commit_r))
	def drawLine(self, x1,y1, x2,y2):
		self.g_graph_lines.add(self.svg.line(self.xform(x1,y1), self.xform(x2,y2)))
	def drawCommitText(self, x,y, commit):
		self.g_text.add(self.svg.text(commit.msg,self.xform(x,y)))
	
	def create(self, commits):
		self.g_graph.translate(self.margin_x, self.margin_y)
		self.g_text.translate(self.margin_x+100, self.margin_y)
		maxx = 0
		
		commit_points = {}
		branches = [Branch(None,commits[0],0,0)]
		y = 0
		
		while branches:
			branch = min(branches, key=Branch.key_time)
			
			# Draw commit
			self.drawCommit(branch.x, y)
			self.drawCommitText(branch.x, y, branch.next)
			
			newbranches = branches[:]
			
			# Draw connecting lines
			for b in branches:
				if not b.prev:
					continue
				
				if b.next == branch.next:
					# Merging into this commit, use this commit's X
					x = branch.x
				else:
					# Use branch's X
					x = b.x
				
				self.drawLine(b.prevx, y-1, x, y)
			
			# Removed merged branches (and ourself)
			insertpoint = None
			i = 0
			while i < len(branches):
				if branches[i].next == branch.next:
					branches.pop(i)
					if insertpoint is None:
						insertpoint = i
				else:
					i += 1
			assert insertpoint is not None
			
			# Create new branches for children
			for child in branch.next.children:
				branches.insert(insertpoint, Branch(branch.next, child, branch.x, branch.prevx))
			
			# Fan branches outwards
			maxx = max(maxx, updateBranches(branches)-1)
			
			y += 1
		
		self.svg["width"] = "100%"
		self.svg["height"] = len(commits) * self.entry_height + 2*self.margin_y
		
	
	def save(self):
		self.svg.save()

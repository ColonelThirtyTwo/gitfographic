
import svgwrite
from collections import namedtuple

DEFAULT_STYLE = """
.graph circle {
	fill: white;
	stroke: blue;
	stroke-width: .3mm;
}
.graph line, .graph path {
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

def lerp(a,b,x):
	return a*(1-x) + b*x

class SvgGraph(object):
	
	def __init__(self, outpath, style=None, linetype=3):
		if linetype < 1 or linetype > 4:
			raise ValueError("linetype must be between 1 and 4, got "+str(linetype))
		
		# Options
		self.commit_r = "1mm"
		self.branch_spacing = 30
		self.entry_height = 25
		self.margin_x = 50
		self.margin_y = 50
		
		# Stuff we need
		self.line_type = linetype
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
		if self.line_type == 1 or x1 == x2:
			# Straight lines
			self.g_graph_lines.add(self.svg.line(self.xform(x1,y1), self.xform(x2,y2)))
		elif self.line_type == 2:
			# Quadratic bezier paths
			if x1 > x2:
				cpx, cpy = x1, y2
			else:
				cpx, cpy = x2, y1
			cmds = ("M", self.xform(x1,y1), "Q", self.xform(cpx,cpy), self.xform(x2,y2))
			self.g_graph_lines.add(self.svg.path(cmds))
		elif self.line_type == 3:
			# Cubic bezier paths, moderate curving
			cmds = ("M", self.xform(x1,y1), "C", self.xform(x1,lerp(y1,y2,0.7)), \
				self.xform(x2,lerp(y1,y2,0.3)), self.xform(x2,y2))
			self.g_graph_lines.add(self.svg.path(cmds))
		elif self.line_type == 4:
			# Cubic bezier paths, heavy curving
			cmds = ("M", self.xform(x1,y1), "C", self.xform(x1,y2), \
				self.xform(x2,y1), self.xform(x2,y2))
			self.g_graph_lines.add(self.svg.path(cmds))
	
	def drawCommitText(self, x,y, commit):
		self.g_text.add(self.svg.text(commit.msg,self.xform(x,y)))
	
	def create(self, commits):
		maxx = 0
		maxmsglen = 0
		
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
					self.drawLine(b.prevx, y-1, branch.x, y)
				else:
					# Use branch's X
					self.drawLine(b.prevx, y-1, b.x, y)
			
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
			maxmsglen = max(maxmsglen, len(branch.next.msg))
			
			y += 1
		
		msg_margin = maxx*self.branch_spacing+20
		self.g_graph.translate(self.margin_x, self.margin_y)
		self.g_text.translate(self.margin_x+msg_margin, self.margin_y)
		self.svg["width"] = self.margin_x+msg_margin + maxmsglen*10 + self.margin_x*2
		self.svg["height"] = len(commits) * self.entry_height + 2*self.margin_y
		
	
	def save(self):
		self.svg.save()

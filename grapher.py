
import svgwrite
import random
from colorsys import hsv_to_rgb

DEFAULT_STYLE = """
.graph circle {
	fill: white;
	/*stroke: blue;*/
	stroke-width: .3mm;
}
.graph line, .graph path {
	fill: none;
	/*stroke: blue;*/
	stroke-width: .5mm;
}
.messages text {
	font-family: monospace;
	font-size: 12pt;
	color: black;
	dominant-baseline: central;
}
"""

DEFAULT_BRANCH_STYLE = """
.branch{0} {{
	stroke: rgb({1[0]},{1[1]},{1[2]});
}}
"""

def lerp(a,b,x):
	return a*(1-x) + b*x

def style2class(n):
	return "branch{0}".format(n)

class Branch(object):
	def __init__(self, graph, style, active, next, x,y):
		self.graph = graph
		
		self.path = graph.g_graph_lines.add(graph.svg.path(class_=style2class(style)))
		if active:
			self.path.push(("M",self.graph.xform(x,y)))
		
		self.x = x
		self.nextcolumn = x
		self.style = style
		self.active = active
		self.next = next
	
	def shift(self, x, y):
		if self.x == x:
			return
		
		if self.active:
			self.path.push(("V",self.graph.xform(0,y-1)[1]))
			
			if self.graph.line_type == 1:
				# Straight lines
				self.path.push(("L",self.graph.xform(x,y)))
			elif self.graph.line_type == 2:
				# Quadratic bezier paths
				if x1 > x2:
					cpx, cpy = self.x, y
				else:
					cpx, cpy = x, y-1
				self.path.push(("Q", self.graph.xform(cpx, cpy), self.graph.xform(x, y)))
			elif self.graph.line_type == 3:
				# Cubic bezier paths, moderate curving
				self.path.push(("C", self.graph.xform(self.x,y-0.3), self.graph.xform(x,y-0.7), self.graph.xform(x,y)))
			elif self.graph.line_type == 4:
				# Cubic bezier paths, heavy curving
				self.path.push(("C", self.graph.xform(self.x,y), self.graph.xform(x,y-1), self.graph.xform(x,y)))
		
		self.x = x
	
	def updateNext(self, next, x, y):
		if not self.active:
			self.path.push(("M",self.graph.xform(x,y)))
			self.active = True
		self.next = next
	
	def split(self, nexts, x, y):
		l = []
		for c in nexts:
			if not l:
				style = self.style
			else:
				style = self.graph.nextBranchStyle()
			l.append(Branch(self.graph, style, self.next, c, x, y))
		self.end(y)
		return l
	
	def end(self,y):
		assert self.active
		self.path.push(("V",self.graph.xform(0,y)[1]))
	
	@staticmethod
	def key_time(x):
		return x.next.time

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
		self.max_styles = 6
		self.line_type = linetype
		self.branch_style = DEFAULT_BRANCH_STYLE
		
		# Stuff we need
		self.curr_style = 0
		self.svg = svgwrite.Drawing(outpath, debug=True)
		self.svg.defs.add(self.svg.style(style or DEFAULT_STYLE))
		
		self.g_graph = self.svg.add(self.svg.g(class_="graph"))
		self.g_graph_lines = self.g_graph.add(self.svg.g(class_="lines"))
		self.g_graph_circles = self.g_graph.add(self.svg.g(class_="circles"))
		self.g_text = self.svg.add(self.svg.g(class_="messages"))
		
	def xform(self,x,y):
		return x*self.branch_spacing, y*self.entry_height
	
	def drawCommit(self, x,y, style):
		self.g_graph_circles.add(self.svg.circle(self.xform(x,y),self.commit_r, class_=style2class(style)))
	
	def drawCommitText(self, x,y, commit):
		self.g_text.add(self.svg.text(commit.msg,self.xform(x,y)))
	
	def nextBranchStyle(self):
		n = self.curr_style
		self.curr_style = (n+1) % self.max_styles
		return n
	
	def create(self, roots):
		maxx = 0
		maxmsglen = 0
		
		# Generate branch styles
		start_hue = random.random()
		for i in range(self.max_styles):
			color = hsv_to_rgb(start_hue+i/self.max_styles, 1, 0.8)
			color = int(color[0]*255), int(color[1]*255), int(color[2]*255)
			self.svg.defs.add(self.svg.style(self.branch_style.format(i, color)))
		
		# Set up branches
		y = 1
		commit_points = {}
		branches = []
		for x, root in enumerate(roots):
			#branches.append(Branch(self.nextBranchStyle(),root.hasUnknownParents,root,x,x))
			branches.append(Branch(self,self.nextBranchStyle(),root.hasUnknownParents,root,x,0))
		
		while branches:
			branch = min(branches, key=Branch.key_time)
			
			# Draw commit
			self.drawCommit(branch.x, y, branch.style)
			self.drawCommitText(0, y, branch.next)
			
			newbranches = branches[:]
			
			# Draw connecting lines
			for b in branches:
				if b.next == branch.next:
					## Merging into this commit, use this commit's X
					#self.drawLine(b.prevx, y-1, branch.x, y, b.style)
					b.shift(branch.x, y)
				else:
					## Use branch's X
					#self.drawLine(b.prevx, y-1, b.x, y, b.style)
					b.shift(b.nextcolumn, y)
			
			# Removed merged branches (and ourself)
			insertpoint = None
			i = 0
			while i < len(branches):
				b = branches[i]
				if b.next == branch.next:
					branches.pop(i)
					if insertpoint is None:
						insertpoint = i
					if b != branch:
						b.end(y)
				else:
					i += 1
			assert insertpoint is not None
			
			# Create new branches for children, or re-add ourself
			if len(branch.next.children) > 1:
				branches[insertpoint:insertpoint] = branch.split(branch.next.children,branch.x,y)
			elif branch.next.children:
				branches.insert(insertpoint, branch)
				branch.updateNext(branch.next.children[0], branch.x, y)
			else:
				branch.end(y)
			
			#first = True
			#for child in branch.next.children:
			#	if first:
			#		style = branch.style
			#		first = False
			#	else:
			#		style = self.nextBranchStyle()
			#	branches.insert(insertpoint, Branch(style, branch.next, child, branch.x, branch.prevx))
			#	insertpoint = insertpoint + 1
			
			# Fan branches outwards
			x = 0
			for branch in branches:
				if branch.x <= x:
					branch.nextcolumn = x
					x += 1
				elif branch.x > x:
					x = branch.x+1
			maxx = max(maxx, x)
			maxmsglen = max(maxmsglen, len(branch.next.msg))
			
			y += 1
		
		msg_margin = maxx*self.branch_spacing + 20
		self.g_graph.translate(self.margin_x, self.margin_y)
		self.g_text.translate(self.margin_x + msg_margin, self.margin_y)
		self.svg["width"] = self.margin_x + msg_margin + maxmsglen*10 + self.margin_x*2
		self.svg["height"] = (y-1) * self.entry_height + 2*self.margin_y
		
	
	def save(self):
		self.svg.save()

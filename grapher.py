
import svgwrite
import random
from colorsys import hsv_to_rgb

DEFAULT_STYLE = """
.graph circle {
	fill: white;
	stroke-width: .3mm;
}
.graph line, .graph path {
	fill: none;
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
		
		self.x = x
		self.oldx = x
		self.active = False
		self.style = style
		self.next = next
		
		if active:
			self.activate(y)
	
	def activate(self, y):
		if self.active:
			return
		self.path = self.graph.g_graph_lines.add(self.graph.svg.path(class_=style2class(self.style)))
		self.push("M",self.graph.xform(self.x,y))
		self.active = True
	
	def push(self, *args):
		self.path.push(args)
	
	def updateX(self, x):
		self.x = x
	
	def drawstep(self, y):
		if not self.active:
			return
		
		if self.oldx != self.x:
			self.push("V",self.graph.xform(-1,y-1)[1])
			
			x1,y1 = self.oldx, y-1
			x2,y2 = self.x, y
			
			if self.graph.line_type == 1:
				# Straight lines
				self.push(y, "L",self.graph.xform(x2,y2))
			elif self.graph.line_type == 2:
				# Quadratic bezier paths
				if x1 > x2:
					cpx, cpy = x1, y2
				else:
					cpx, cpy = x2, y1
				self.push("Q", self.graph.xform(cpx, cpy), self.graph.xform(x2, y2))
			elif self.graph.line_type == 3:
				# Cubic bezier paths, moderate curving
				self.push("C", self.graph.xform(x1,y2-0.3), self.graph.xform(x2,y1+0.3), self.graph.xform(x2,y2))
			elif self.graph.line_type == 4:
				# Cubic bezier paths, heavy curving
				self.push("C", self.graph.xform(x1,y2), self.graph.xform(x2,y1), self.graph.xform(x2,y2))
			else:
				assert False
			
			self.oldx = x2
	
	def updateNext(self, next, y):
		self.activate(y)
		self.next = next
	
	def split(self, nexts, y):
		l = []
		for c in nexts:
			if not l:
				style = self.style
			else:
				style = self.graph.nextBranchStyle()
			l.append(Branch(self.graph, style, self.next, c, self.x, y))
		return l
	
	def end(self, y):
		if self.active:
			self.push("V",self.graph.xform(-1,y)[1])
	
	@staticmethod
	def key_time(x):
		return x.next.time

class SvgGraph(object):
	
	def __init__(self, outpath, style=None):
		
		# Options
		self.commit_r = "1mm"
		self.branch_spacing = 30
		self.entry_height = 25
		self.margin_x = 50
		self.margin_y = 50
		self.branch_styles = 6
		self.line_type = 4
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
		self.curr_style = (n+1) % self.branch_styles
		return n
	
	def create(self, roots):
		# Keep some values to help determine the width of the SVG
		maxx = 0
		maxmsglen = 0
		
		# Generate branch styles
		start_hue = random.random()
		for i in range(self.branch_styles):
			color = hsv_to_rgb((start_hue+float(i)/self.branch_styles)%1, 1, 0.8)
			color = int(color[0]*255), int(color[1]*255), int(color[2]*255)
			self.svg.defs.add(self.svg.style(self.branch_style.format(i, color)))
		
		# Set up branches
		y = 1
		commit_points = {}
		branches = []
		for x, root in enumerate(roots):
			#branches.append(Branch(self,self.nextBranchStyle(),root.hasUnknownParents,root,x,0))
			branches.append(Branch(self,self.nextBranchStyle(),True,root,x,0))
		
		while branches:
			# Get the next branch, by time of commit
			branch = min(branches, key=Branch.key_time)
			
			# Draw commit
			self.drawCommit(branch.x, y, branch.style)
			self.drawCommitText(0, y, branch.next)
			
			# Update, draw, and remove merged branches (including current branch)
			insertpoint = None
			i = 0
			while i < len(branches):
				b = branches[i]
				if b.next == branch.next:
					b.updateX(branch.x) # Merge the branch
					branches.pop(i)     # Remove the merged branch
					
					if b is not branch: # End branches with no possibility of continuing
						b.end(y)        # The current branch may continue, see the next section of code
					
					if insertpoint is None:
						insertpoint = i
				else:
					i += 1
				b.drawstep(y)
			assert insertpoint is not None
			
			# Create new branches for children, or re-add current branch
			if len(branch.next.children) > 1:
				# Split current branch into sub-branches for each of the children
				branches[insertpoint:insertpoint] = branch.split(branch.next.children,y)
				branch.end(y)
			elif branch.next.children:
				# Only one child, just continue the existing branch
				branches.insert(insertpoint, branch)
				branch.updateNext(branch.next.children[0], y)
			else:
				# No more children, stop the branch
				branch.end(y)
			
			# Fan branches outwards
			x = 0
			for b in branches:
				if b.x <= x:
					b.updateX(x)
					x += 1
				elif b.x > x:
					x = b.x+1
			
			# Update maximum values
			maxx = max(maxx, x)
			maxmsglen = max(maxmsglen, len(branch.next.msg))
			
			# Increment our y position
			y += 1
		
		# Align the text and set SVG widths
		msg_margin = maxx*self.branch_spacing + 20
		self.g_graph.translate(self.margin_x, self.margin_y)
		self.g_text.translate(self.margin_x + msg_margin, self.margin_y)
		self.svg["width"] = self.margin_x + msg_margin + maxmsglen*10 + self.margin_x*2
		self.svg["height"] = (y-1) * self.entry_height + 2*self.margin_y
		
	
	def save(self):
		self.svg.save()

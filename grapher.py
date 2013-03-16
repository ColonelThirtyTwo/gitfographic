
import svgwrite

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
	font: monospace;
	color: black;
	font-size: 12pt;
}
"""

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

	def drawCommit(self, x,y):
		self.g_graph_circles.add(self.svg.circle((x,y),self.commit_r))

	def drawLine(self, x1,y1, x2,y2):
		self.g_graph_lines.add(self.svg.line((x1,y1), (x2,y2)))
	
	def drawCommitText(self, commit):
		pass

	def create(self, commits):
		self.g_graph.translate(self.margin_x, self.margin_y)
		
		commit_points = {}
		branches = []
		for i, commit in enumerate(commits):
			# Which branch are we updating?
			branch = None
			for j in range(len(branches)):
				if branches[j] in commit.parents:
					branch = j
					break
			if branch < 0:
				branches.append(commit)
				branch = len(branches)-1
			else:
				branches[branch] = commit
			
			# Draw it
			x,y = branch*self.branch_spacing, i*self.entry_height
			commit_points[commit] = (x,y)
			self.drawCommit(x,y)
			for p in commit.parents:
				x2,y2 = commit_points[p]
				self.drawLine(x,y, x2,y2)
			
			# Remove merged branches
			if len(commit.parents) > 1:
				for j in range(len(branches)-1, branch, -1):
					p = branches[j]
					if p in commit.parents and len(p.children) == 1:
						branches.pop(j)
		
		self.svg["width"] = "100%"
		self.svg["height"] = len(commits) * self.entry_height + 2*self.margin_y
		
	
	def save(self):
		self.svg.save()

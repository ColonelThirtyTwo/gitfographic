
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
		
		# Stuff we need
		self.svg = svgwrite.Drawing(outpath, debug=True)
		self.svg.defs.add(self.svg.style(style or DEFAULT_STYLE))
		
		self.g_graph = self.svg.g(class_="graph")
		self.svg.add(self.g_graph)
		
		self.g_text = self.svg.g(class_="messages")
		self.svg.add(self.g_text)

	def drawCommit(self, x,y):
		e = self.svg.circle((x,y),self.commit_r)
		self.g_graph.add(e)

	def drawLine(self, x1,y1, x2,y2):
		pass
	
	def drawCommitText(self, commit):
		pass

	def create(self, commits):
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
			
			# Remove fully merged branches
			for j in range(len(branches)-1, 0, -1):
				if not branches[j].children:
					branches.pop(j)
	
	def save(self):
		self.svg.save()

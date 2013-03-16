
from __future__ import print_function
import gitprocess
import grapher
import argparse

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Turns a git repo's history into an SVG graph")
	parser.add_argument("outfile", help="SVG output")
	parser.add_argument("-r", "--repo", default=None, help="Input repository. Defaults to current directory.")
	parser.add_argument("-l", "--linestyle", default=4, type=int, help="Line style to use. 1 = linear, 2 = quadratic bezier, 3 and 4 = cubic beziers")
	args = parser.parse_args()
	
	commits = gitprocess.parseLog(gitprocess.getLog(args.repo))
	graph = grapher.SvgGraph(args.outfile, None, args.linestyle)
	graph.create(commits)
	graph.save()

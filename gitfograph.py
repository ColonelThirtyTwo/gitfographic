
from __future__ import print_function
import gitprocess
import grapher
import argparse

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Turns a git repo's history into an SVG graph")
	parser.add_argument("outfile", help="SVG output")
	parser.add_argument("-r", "--repo", default=None, help="Input repository. Defaults to current directory.")
	args = parser.parse_args()
	
	commits = gitprocess.parseLog(gitprocess.getLog(args.repo))
	graph = grapher.SvgGraph(args.outfile)
	graph.create(commits)
	graph.save()

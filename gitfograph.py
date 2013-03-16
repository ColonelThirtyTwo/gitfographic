
import gitprocess
import grapher
import argparse

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Turns a git repo's history into an SVG graph")
	parser.add_argument("outfile", help="SVG output")
	parser.add_argument("-r", "--repo", default=None, help="Input repository. Defaults to current directory.")
	parser.add_argument("-l", "--linestyle", default=4, type=int, help="Line style to use. 1 = linear, 2 = quadratic bezier, 3 and 4 = cubic beziers")
	parser.add_argument("-q", "--quiet", help="Don't print status messages", action="store_true")
	parser.add_argument("--log", help="Pass this option to git log", action="append")
	args = parser.parse_args()
	
	if not args.quiet: print("Parsing commits from log")
	commits = gitprocess.parseLog(gitprocess.getLog(args.repo, args.log), args.quiet)
	graph = grapher.SvgGraph(args.outfile, None, args.linestyle)
	
	if not args.quiet: print("Creating graph")
	graph.create(commits)
	
	if not args.quiet: print("Writing graph to disk")
	graph.save()
	
	if not args.quiet: print("Done")

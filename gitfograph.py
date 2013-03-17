
import gitprocess
import grapher
import argparse
import logging

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Turns a git repo's history into an SVG graph")
	
	log_group = parser.add_mutually_exclusive_group()
	log_group.add_argument("-v", "--verbose", help="Show debug messages", dest="level", action="store_const", const=logging.DEBUG, default=logging.INFO)
	log_group.add_argument("-q", "--quiet", help="Do not output anything to console", dest="level", action="store_const", const=logging.CRITICAL)
	
	parser.add_argument("outfile", help="SVG output")
	parser.add_argument("-r", "--repo", default=None, help="Input repository. Defaults to current directory.")
	parser.add_argument("-l", "--linestyle", default=4, type=int, help="Line style to use. 1 = linear, 2 = quadratic bezier, 3 and 4 = cubic beziers")
	parser.add_argument("-f", "--format", default="%s", help="Message format. See git log's `format:` documentation")
	parser.add_argument("--log", help="Pass this option to git log", action="append", default=[])
	parser.add_argument("-c", "--branchcolors", default=6, help="Number of branch color styles to generate")
	args = parser.parse_args()
	
	logging.basicConfig(level=args.level, format="%(message)s")
	
	logging.info("Parsing commits from log")
	roots = gitprocess.parseLog(gitprocess.getLog(args.repo, args.log, args.format))
	graph = grapher.SvgGraph(args.outfile, None, args.linestyle)
	
	logging.info("Creating graph")
	graph.create(roots)
	
	logging.info("Saving graph to disk")
	graph.save()
	
	logging.info("Done")

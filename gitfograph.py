
import gitprocess
import grapher
import argparse
import logging
import sys

def check(cond, errmsg):
	if not cond:
		print(errmsg, file=sys.stderr)
		sys.exit(1)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Turns a git repo's history into an SVG graph")
	
	log_group = parser.add_mutually_exclusive_group()
	log_group.add_argument("-v", "--verbose", help="Show debug messages", dest="level", action="store_const", const=logging.DEBUG, default=logging.INFO)
	log_group.add_argument("-q", "--quiet", help="Do not output anything to console", dest="level", action="store_const", const=logging.CRITICAL)
	parser.add_argument("outfile", help="SVG output")
	parser.add_argument("-r", "--repo", default=None, help="Input repository. Defaults to current directory.")
	parser.add_argument("--log", help="Pass this option to git log", action="append", default=[])
	
	formats_group = parser.add_argument_group("Formatting Options", "Options that control the appearance of the output")
	formats_group.add_argument("-l", "--linestyle", default=4, type=int, help="Line style to use. 1 = linear, 2 = quadratic bezier, 3 and 4 = cubic beziers")
	formats_group.add_argument("-f", "--format", default="%s", help="Message format. See git log's `format:` documentation")
	formats_group.add_argument("-c", "--branchcolors", type=int, default=6, help="Number of branch color styles to generate")
	formats_group.add_argument("--branchspacing", type=int, default=30, help="Space between branches")
	formats_group.add_argument("--entryheight", type=int, default=25, help="Space between each commit entry")
	
	args = parser.parse_args()
	
	logging.basicConfig(level=args.level, format="%(message)s")
	
	check(args.linestyle >= 1 and args.linestyle <= 4, "Invalid line style")
	check(args.branchcolors  > 0, "Invalid number of branch colors")
	check(args.branchspacing > 0, "Invalid branch spacing")
	check(args.entryheight   > 0, "Invalid entry height")
	
	logging.info("Parsing commits from log")
	roots = gitprocess.parseLog(gitprocess.getLog(args.repo, args.log, args.format))
	graph = grapher.SvgGraph(args.outfile)
	
	graph.line_style = args.linestyle
	graph.branch_styles = args.branchcolors
	graph.branch_spacing = args.branchspacing
	graph.entry_height = args.entryheight
	
	logging.info("Creating graph")
	graph.create(roots)
	
	logging.info("Saving graph to disk")
	graph.save()
	
	logging.info("Done")

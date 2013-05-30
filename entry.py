
class Entry(object):
	def __init__(self, identifier, msg, time, parents=None, children=None):
		self.id = identifier
		self.msg = msg
		self.time = time
		self.parents = [] if parents is None else parents
		self.children = [] if children is None else children
	
	def __str__(self):
		return "Entry({0},{1},{2})".format(self.id, self.time, self.msg)
	__repr__ = __str__
	
	def __eq__(self, other):
		return self.id == other.id
	def __hash__(self):
		return hash(self.id)

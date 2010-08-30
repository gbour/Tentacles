# -*- coding: utf8 -*-
import byteplay as byte
import opcodes

# parse python opcode, convert it to a pseudo AST
class Parser(object):

	def walk(self, code):
		c = byte.Code.from_code(code.func_code)
		print c.args, c.freevars, c.newlocals, c.varargs, c.varkwargs
		print code.func_code.co_varnames, code.func_code.co_freevars, code.func_code.co_cellvars

		# 1st function argument is the "table line"
#		tblarg  = c.args[0]
		stack   = []
		jumps   = {}
		globals = []

		self.ast   = []
		self.stack = []
		self.jumps = {}
		self.co_varnames = {}

		for opcode, attr in c.code:
			print opcode, attr#, isinstance(opcode, byte.Label)#, self.stack
			if isinstance(opcode, byte.Label): # jump destination
				attr   = opcode
				opcode = 'LABEL'

			if not hasattr(self, 'do_%s' % opcode):
				print '>> NOT FOUND::', opcode; continue

			getattr(self, 'do_%s' % opcode)(attr)

		#import pprint; pprint.pprint(self.stack)
		#return self.ast
		return self.stack

	def do_SetLineno(self, attr):
		""" ignore """
		pass

	def do_LOAD_CONST(self, attr):
		print attr, type(attr)
		self.stack.append((opcodes.CONST, attr))

	def do_LOAD_GLOBAL(self, attr):
		if   attr == 'True':
			self.stack.append((opcodes.CONST, True))
		elif attr == 'False':
			self.stack.append((opcodes.CONST, False))
		else:
			self.stack.append((opcodes.VAR, attr))

	def do_LOAD_FAST(self, attr):
		self.stack.append((opcodes.VAR, attr))
		print self.stack

	def do_LOAD_ATTR(self, attr):
		self.stack.append((opcodes.ATTR, self.stack.pop(), attr))

	def do_BUILD_TUPLE(self, attr):
#		print self.stack, attr
		tupl = self.stack[-attr:]
		del self.stack[-attr:]

		self.stack.append((opcodes.LIST, tupl))

	def do_BUILD_LIST(self, attr):
		if attr == 0:
			self.stack.append((opcodes.LIST, []))
			return

		self.stack.append((opcodes.LIST, self.stack[-attr:]))
		del self.stack[-attr-1:-1]
		print self.stack

	def do_LIST_APPEND(self, attr):
		# MAY BE a variable (don't know the typeof)
		#assert self.stack[-2][0] == opcodes.LIST 
		print self.stack
	
		value = self.stack.pop()
		self.stack.append([opcodes.APPEND, self.stack.pop(), value])
		print self.stack

	def do_RETURN_VALUE(self, attr):
		print 'RET=', self.stack, '<'
		top = self.stack.pop()
		if top[0] == opcodes.MARKER_IFFALSE:
			if len(top[2]) != 1:
				raise Exception()

			top[0] = opcodes.AND
			top[2] = top[2][0]
		elif top[0] == opcodes.MARKER_IFTRUE:
			if len(top[2]) != 1:
				raise Exception()

			top[0] = opcodes.OR
			top[2] = top[2][0]

		self.stack.append([opcodes.RET, top])

	def do_BINARY_SUBSCR(self, attr):
		""" list[10] """
		self.stack.append((opcodes.AT, self.stack.pop(-2), self.stack.pop()))

	def do_CALL_FUNCTION(self, attr):
		"""
		
			attr: function arguments count (taken from top stack)
		"""
		args = []
		if attr > 0:
			args = self.stack[-attr:]
			del self.stack[-attr:]
		
		self.stack.append((opcodes.CALL, self.stack.pop(), args))

	def do_SLICE_0(self, attr):
		"""
			neither start or stop argument == whole list slice
			
			list[:]
		"""
		self.stack.append((opcodes.SLICE, None, None, None))

	def do_SLICE_1(self, attr):
		"""
			only start argument (on top of stack)
			
			list[5:]
		"""
		self.stack.append((opcodes.SLICE, self.stack.pop(-2), self.stack.pop(), None))

	def do_SLICE_2(self, attr):
		"""
			only start argument (on top of stack)
			
			list[:10]
		"""
		self.stack.append((opcodes.SLICE, self.stack.pop(-2), None, self.stack.pop()))

	def do_SLICE_3(self, attr):
		"""
			only start argument (on top of stack)
			
			list[5:10]
		"""
		self.stack.append((opcodes.SLICE, self.stack.pop(-3), self.stack.pop(-2), self.stack.pop()))

	def do_BINARY_ADD(self, attr):
		self.stack.append((opcodes.ADD, self.stack.pop(-2), self.stack.pop()))

	def do_BINARY_SUBTRACT(self, attr):
		self.stack.append((opcodes.SUB, self.stack.pop(-2), self.stack.pop()))

	def do_BINARY_DIVIDE(self, attr):
		self.stack.append((opcodes.DIV, self.stack.pop(-2), self.stack.pop()))

	def do_BINARY_MULTIPLY(self, attr):
		self.stack.append((opcodes.MUL, self.stack.pop(-2), self.stack.pop()))

	def do_BINARY_MODULO(self, attr):
		self.stack.append((opcodes.MOD, self.stack.pop(-2), self.stack.pop()))

	def do_BUILD_MAP(self, attr):
		"""
			attr = number of items in dict
			
			BUILD_MAP 2
			...
		"""
		self.stack.append((opcodes.DICT, []))

	def do_STORE_FAST(self, attr):
		print self.stack
		if self.stack[-1][0] == opcodes.FOR:
			self.stack[-1][1] = ('var', attr)
		else:
			self.stack.append((opcodes.SET, ('var', attr), self.stack.pop()))
		print self.stack

	def do_STORE_MAP(self, attr):
		"""
			call for each key/value couple
			
			LOAD_ATTR name
			LOAD_CONST joe
			STORE_MAP None
		"""
		self.stack[-3][1].append((opcodes.KV, self.stack.pop(), self.stack.pop()))

	COMPARE_MAP = {
		'is'    : opcodes.EQ,
		'is not': opcodes.NEQ,
		'=='    : opcodes.EQ,
		'!='    : opcodes.NEQ,
		'>'     : opcodes.LT,
		'<'     : opcodes.GT,
		'>='    : opcodes.GEQ,
		'<='    : opcodes.LEQ,
		'in'    : opcodes.IN,
	}
	def do_COMPARE_OP(self, attr):
		self.stack.append((self.COMPARE_MAP[attr], self.stack.pop(-2), self.stack.pop()))

	def do_UNARY_NOT(self, attr):
		top = self.stack.pop()
		if top[0] == opcodes.MARKER_IFFALSE:
			if len(top[2]) != 1:
				raise Exception()

			top[0] = opcodes.AND
			top[2] = top[2][0]
		elif top[0] == opcodes.MARKER_IFTRUE:
			if len(top[2]) != 1:
				raise Exception()

			top[0] = opcodes.OR
			top[2] = top[2][0]

		self.stack.append((opcodes.NOT, top))

	def do_POP_TOP(self, attr):
#		print self.stack
#		self.stack.append((opcodes.MARKER_POPTOP))
#		self.stack.pop()
		pass

	def do_DUP_TOP(self, attr):
		pass

	def do_JUMP_IF_FALSE(self, attr):
		jmp = [opcodes.AND, self.stack.pop(), None]
		self.stack.append(jmp)

		node = self.jumps.setdefault(attr, [])
		node.insert(0, jmp)
		print self.stack

	def do_JUMP_IF_TRUE(self, attr):
		jmp = [opcodes.OR, self.stack.pop(), None]
		self.stack.append(jmp)

		node = self.jumps.setdefault(attr, [])
		node.insert(0, jmp)

	def do_JUMP_FORWARD(self, attr):
		jmp = [opcodes.MARKER_JUMP, attr]
		self.stack.append(jmp)

		node = self.jumps.setdefault(attr, [])
		self.jumps[attr].insert(0, jmp)
		

	def do_JUMP_ABSOLUTE(self, attr):
		jmp = [opcodes.MARKER_JUMP, attr]
		self.stack.append(jmp)

		node = self.jumps.setdefault(attr, [])
		self.jumps[attr].insert(0, jmp)

	def do_GET_ITER(self, attr):
		self.stack.append([opcodes.FOR, None, self.stack.pop(), None])
		print self.stack

	def do_FOR_ITER(self, attr):
		assert self.stack[-1][0] == opcodes.FOR

		node = self.jumps.setdefault(attr, [])
		self.jumps[attr].insert(0, self.stack[-1])
		print self.jumps

	def _update_refs(self, old, new):
		"""
			Must be optimized
		"""
		for key, jumps in self.jumps.iteritems():
			if old not in jumps:
				continue

			jumps = [new if j is old else j for j in jumps]
			jumps.reverse()
			j2    = []
			for i in xrange(len(jumps)):
				if jumps[i] in jumps[i+1:]:
					continue

				j2.insert(0, jumps[i])
				
			# we may have duplicates, and should remove them
			# we can't use set because values are also list (error TypeError: unhashable type:
			# 'list')
			
			self.jumps[key] = j2

	def do_LABEL(self, label):
#		print '  . previous=', self.stack[-1]

		if label not in self.jumps:
			print " *** flashback label ***", label
			return

		print '>> label::', self.jumps[label], self.stack
		for instr in self.jumps[label]:
			i = self.stack_index(instr)
			if i is None:
				print " *** instruction not found ***", self.stack, instr; continue

			act = self.stack[i]
			print "act=", act
			#j = len(self.stack) - 1 # stack top
			#print i, j
			prev = self.stack.pop() #None #(None, None, None)
			do = True
			if prev == act:
				do = False
				top = prev
			else:
				top  = self.stack.pop()
			

#			print "do=", do
			while do: #j > i:
				#top = self.stack.pop(); #j = j-1
				print "top=", top, prev


				if act[0] == opcodes.FOR:
					assert prev[0] == opcodes.MARKER_JUMP and act[3] is None
					# we should check jump destination is FOR
					# loop

					act[3] = self.stack[i+1:]
					del self.stack[i:] # we also push out 'for' from stack

					act[3].append(top)
					top = act

				# we can get it out of the while loop
				elif prev[0] == opcodes.MARKER_JUMP or\
				   prev[0] == opcodes.RET:
					assert act[0] in (opcodes.AND, opcodes.OR) and act[2] is None

					if act[0] == opcodes.OR:
						# or == not and
#						print "reverse or"
						act[1] = [opcodes.NOT, act[1]]

#					print "found jump"
					prev[0] = opcodes.IF
					prev[1] = act[1]
					# unstack from index i (excluded) to top
					prev.extend([self.stack[i+1:], None])
					del self.stack[i+1:]

					prev[2].append(top)
					self._update_refs(top, prev)
					self._update_refs(act, prev)
#					print 'plop'
					top = prev
					act = prev
					if len(self.stack) > 0:
						self.stack.pop() # unstack act as replaced by prev
					
				elif act[0] == opcodes.IF:
					assert act[3] is None

					act[3] = self.stack[i+1:]
					del self.stack[i+1:]
					if top != act:
						self.stack.pop()
						act[3].append(top)
					act[3].append(prev)

					top = act

				elif top[0] in [opcodes.AND, opcodes.OR] and top[2] is None:
#					assert top[2] is None

#					if top == act and prev[0] in [opcodes.AND, opcodes.OR]:
#						print 'PLOP'
					if prev[0] in [opcodes.AND, opcodes.OR] \
					   and prev[2] is None \
					   and top[2]   is None:
						# merge top in prev
#						print 'zzz'
						top[2]   = prev[1]
						prev[1] = top

						self._update_refs(top, prev)
						if top == act:
							act = prev
						top      = prev # prevent swap
				
					elif prev[0] == opcodes.IF:
						# we merge with IF condition
						top[2]  = prev[1]
						prev[1] = top

						self._update_refs(top, prev)
						if top == act:
							act = prev
						top     = prev
	
					else:
						# merge prev in top
						top[2]   = prev
						self._update_refs(prev, top)

#					if len(self.stack) > 0:
#						untop = self.stack.pop()
#						assert untop[2] is None
#						untop[2] = top[1]
#						top[1]   = untop
#					else:
#						assert top[2] is None
#						top[2]   = prev

					# NEED updating references (untop -> top)
					#self.update_refs(untop, top)

					

#				print 'loop', top, act
				if top == act:
					break;

				prev = top
#				print self.stack
				top   = self.stack.pop()

			self.stack.append(top)
			print "endwhile: ", self.stack

		print '<< label::', self.stack
			

#		print '>> instrs=', self.jumps[label]
#		top    = self.stack.pop()
#
#		# IF branch detection
#		#   if top stack value is a JUMP, values between this JUMP and LABEL source condition
#		#   are concatenated in a list of instructions (if main branch instructions)
#		if top[0] == opcodes.MARKER_JUMP:
#			print 'found jump'
#			top[0] = opcodes.IF; top[1] = None
#			top.extend([None, None])
#
#		for instr in self.jumps[label]:
#			i = self.stack_index(instr)
#
#			if i is None:
#				print " *** instruction not found ***", self.stack, instr; continue
#
#			act = self.stack[i]
#			del self.stack[i]
#			print 'zz:', act, top
#			if top[0] == opcodes.IF:
#				if top[1] == None: # no condition yet
#					# act[0] MUST be and, act[2] MUST be NULL
#				
#					top[1] = act[1]
#					top[2] = self.stack[i:]
#					del self.stack[i:]
#				
#				# we still have a condition : must merge
#				else:
#					act[2] = top[1]
#					top[1] = act
#
#			elif act[0] == opcodes.IF:
#				act[3] = self.stack[i:]
#				act[3].append(top)
#				del self.stack[i:]
#
#				top = act
#
#			# dans les 2 cas suivants, il faut merger se qui se trouve entre stack[i] et stack[top]
#
#			elif top[0] in [opcodes.AND, opcodes.OR] and top[2] is None:
#				print "case 1"
#				act[2] = top[1]
#				top[1] = act
#
#			else:
#				print "case 2"
#				act[2] = top
#				top = act
#
#		self.stack.append(top)
#		print "stack=", self.stack
#


	def stack_index(self, instruction):
		for i in xrange(len(self.stack)):
			if id(instruction) == id(self.stack[i]):
				return i
				
		return None


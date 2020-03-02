import random
class NN:
	def __init__(self,layers=3):
		self.layers = [Layer() for _ in range(0,layers)]
		self.inputs = None
	def input(self,inputs):
		self.inputs = inputs
		for i,l in enumerate(self.layers):
			if i == 0:
				l.input(self.inputs)
			else:
				l.input(self.layers[i-1].vector)

	def addLayer(self,layer):
		self.layers.append(layer)
	def delLayer(self,layer=None,idx=None):
		if idx:
			self.layers.pop(idx)
		elif layer:
			self.layers.remove(layer)
	def __str__(self):
		t = f"This neural network's current inputs are:\n{self.inputs}\nIt contains {len(self.layers)} layers:\n"
		for layer in self.layers:
			t += str(layer) + "\n"
		t += f'\nNN output: {self.layers[-1].vector}' 
		return t

class Layer:
	def __init__(self,perceptrons=6):
		self.perceptrons = [Perceptron() for _ in range(0,perceptrons)]
		self.inputs = None
	@property
	def vector(self):
		return [p.output for p in self.perceptrons]
	
	def input(self,inputs):
		self.inputs = inputs
		for p in self.perceptrons:
			p.input(inputs)

	def addPerceptron(self,perceptron):
		self.perceptrons.append(perceptron)

	def delPerceptron(self,perceptron=None,idx=None):
		if perceptron:
			self.perceptrons.remove(perceptron)
		elif idx:
			self.perceptrons.pop(idx)
	def __str__(self):
		t = '[Layer]\n'
		for p in self.perceptrons:
			t += str(p) + "\n"
		return t

class Perceptron:
	def __init__(self,bias=0):
		self.inputs=[]
		self.weights=[]
		self.output = 0
		self.baseWeight = 0
		self.bias = bias

	@property
	def sum(self):
		wx = 0
		for w,x in zip(self.weights,self.inputs):
			wx += w*x
		return wx + self.bias

	def checkParameters(self,inputs):
		if len(inputs) > len(self.inputs):
			self.weights += [random.randint(0,10) for _ in range(0,len(inputs)-len(self.inputs))]
		elif len(inputs) < len(self.inputs):
			self.weights = self.weights[:len(inputs)]

	def input(self,inputs):
		self.checkParameters(inputs)
		self.inputs = inputs
		if self.sum > 0:
			self.fire()
	
	def fire(self):
		self.output = 1

	def __str__(self):
		return f'[P]\ninputs:  {self.inputs}\nweights: {self.weights}\nbias: {self.bias}\noutput: {self.output}'


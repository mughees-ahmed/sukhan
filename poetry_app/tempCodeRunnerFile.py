class stack :
    def __init__(self):
        self.values=[]
    def push(self,x):
        self.values=[x]+self.values
    def pop (self):
            return self.values.pop(0)
    
stack1=stack()
stack1.push(1)
stack1.push(87)
stack1.push(45)
stack1.push(19)
print(stack1.values)
stack1.pop()
print (stack1.values)
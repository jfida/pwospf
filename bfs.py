V = ['v1', 'v2', 'v3', 'v4']
E = [('v1', 'v2'), ('v1', 'v3'), ('v1', 'v4'), ('v3', 'v4')]

prev = {}
next = {}  

# init prev maps
for v in V:
  prev[v] = {}
  for w in V:
    prev[v][w] = None
next = prev

# compute prev dict
for v in prev:
  front, visit = [v], [v]
  while front:
    w = front.pop(0)
    for x in [edge[1 - edge.index(w)] for edge in E if w in edge]:
      if x not in visit:
        visit.append(x)
        prev[v][x] = w
        front.append(x)

# compute next dict
for v in V:
  for w in V:
    if prev[v][w] == w:
      next[w][v] = w
    else:
      next[w][v] = prev[v][w]
    
print next

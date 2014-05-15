from visual import *
from random import shuffle
import itertools
background=(1,1,1)
background=(0,0,0)

foreground=[1-x for x in background]
scene = display(title="Counterfeit", background=background)
shape_cylinders = False

def polygon_triangle():
  points = []
  # sin/cos just once
  angle = -2.0*pi/5.0
  a = math.cos( angle )
  b = math.sin( angle )

  # rotation matrix, clockwise
  R = mat( [[a, -b], [b, a]] )
  v = mat( [1.0,0] )   # unit vector along x-axis

  nv = v * R
  vx,vy = v.T  # transpose
  x = math.cos( angle )
  y = math.sin( angle )
  v = nv
  points.append([1.0,0])
  points.append([x,y])
  points.append([0,0])
  return points

g_PolygonTriangle=polygon_triangle()

def rectangle(width, height, color, frame=frame(), origin=(0,0,0)):
  # Define the geometry of a part
  # This has 11 points. Points must be in clockwise order of cartesian
  # cordinates
  # e.g. start from first partid (+x, +y) go to the second... (+x, -y)
  # and so on. The last point must be the start point to complete the shape
  points = zeros((5, 2), float)
  points[0] = ([ width/2.0, height/2.0])
  points[1] = ([ width/2.0,-height/2.0])
  points[2] = ([-width/2.0,-height/2.0])
  points[3] = ([-width/2.0, height/2.0])
  points[4] = ([ width/2.0, height/2.0])
  # End geometry

  model = faces( pos = zeros( ((len(points)-1)*3,3), float ), frame = frame , normal = (0,0,1))
  # Vertex 0 of triangles
  model.pos[0::3, 0] = points[:-1:, 0]
  model.pos[0::3, 1] = points[:-1:, 1]

  # Vertex 1 of triangles
  model.pos[2::3, 0] = points[1::, 0]
  model.pos[2::3, 1] = points[1::, 1]

  model.color = color
  # Vertex 2 of triangles
  model.pos[1::3, 2] = 0

  model.pos += origin
  return model

def part(
    size=4.0,
    counterfeit=False,
    partid=0,
    frame=frame()):

  #colors = [(0, 0.6, 1.0), (0.0, 0.0, 1.0)]
  colors = [(0, 0.0, 1.0), (0.0, 0.0, 1.0)]
  size = size - 0.1
  if counterfeit:
    size = size/1.25

  width = size/2.0
  height = size/3.0

  origin = [
      ( width*0.5, height, 0),
      ( width*0.5,      0, 0),
      ( width*0.5,-height, 0),
      (-width*0.5, height, 0),
      (-width*0.5,      0, 0),
      ]
  if shape_cylinders:
    origin = [
        ( 0, height, 0),
        ( 0,      0, 0),
        ( 0,-height, 0),
        (-width, height, 0),
        (-width,      0, 0),
        ]
    return cylinder(
        radius=height/2.0,
        pos=origin[partid],
        length=width,
        frame=frame,
        color=colors[partid%2],
        )
  else:
    return rectangle(
        width=width-.1,
        height=height-.1,
        frame=frame,
        color=colors[partid%2],
        origin=origin[partid])

def unit(counterfeits=[],frame=frame(),origin=(0,0,0)):
  size = 4.0
  rectangle(width=size*0.95, height=size*0.95, color=foreground, frame=frame)
  for i in range(5):
    part(partid=i, counterfeit=i in counterfeits, frame=frame, size=size*0.9)
  frame.pos += origin
  return frame

def A0(frame): return unit(frame=frame)
def A1(frame): return unit(frame=frame, counterfeits=[0])
def A2(frame): return unit(frame=frame, counterfeits=[1])
def A12(frame): return unit(frame=frame, counterfeits=[0,1])

class Scene:
  def __init__(self):
    self.units = []
    self.max_cols = 2
    self.current = (-self.max_cols, -self.max_cols)
    self.frame = frame()
    self.size = 4.0
    self.headers={}

  def add(self, partid):
    r,c = self.current
    origin = r*self.size, c*self.size, 0
    if c == self.max_cols:
      r += 1
      c  = -self.max_cols
    else:
      c += 1
    self.current = r,c
    p = partid(frame())
    p.pos += origin
    self.units.append(p)
    return p

  def data(self, path):
    with open(path) as f:
      l=f.readline().strip()
      h=l.split(',')
      for i in range(len(h)):
        self.headers[h[i]] = i
      for l in f:
        yield [float(x) for x in l.strip().split(',')]

  def render(self, path):
    units = []
    for d in self.data(path):
      units = []
      units.append(d[self.headers['"!c0"']])
      units.append(d[self.headers['"!c1"']])
      units.append(d[self.headers['"!c2"']])
      units.append(d[self.headers['"!c12"']])

    total = sum(units)
    self.max_cols = int(sqrt(total)/2)
    self.current = (-self.max_cols, -self.max_cols)
    self.label = label(pos=(self.size*self.max_cols, -self.size*self.max_cols, 0))
    types = [A0, A1, A2, A12]
    units = [[types[i]] * int(units[i]) for i in range(4)]
    all = []
    for u in units:
      all.extend(u)
    shuffle(all)
    good_units = {}
    for u in all:
      us = good_units.get(u, [])
      us.append(self.add(u))
      good_units[u] = us
    for k,v in good_units.iteritems():
      shuffle(v)
    all_units = dict(good_units)

    def get_units(badunits, header, item_class, parts, prev_snapshot):
      num = int(d[self.headers[header]])
      if prev_snapshot:
        num -= int(prev_snapshot[self.headers[header]])
      if num != 0:
        print "%d %s units failed due to parts %s" % (num, item_class, parts)
      for u in good_units.get(item_class, [])[:num]: badunits.append((u,parts))
      good_units[item_class] = good_units.get(item_class, [])[num:]

    i = 0
    prev_snapshot = None
    for d in self.data(path):
      rate(1)
      self.label.text = str(d[self.headers['"Time"']])
      i += 1

      badunits = []
      get_units(badunits, '"!fc1"', A1, [0], prev_snapshot)
      get_units(badunits, '"!fc2"', A2, [1], prev_snapshot)
      get_units(badunits, '"!fc121"', A12, [0], prev_snapshot)
      get_units(badunits, '"!fc122"', A12, [1], prev_snapshot)
      get_units(badunits, '"!fc1212"', A12, [0, 1], prev_snapshot)

      for i in range(1, 6):
        for p in itertools.permutations(range(1, 6), i):
          header = '"!fp%s"' % ''.join([str(x) for x in p])
          if self.headers.get(header) is None: continue
          get_units(badunits, header, A0, [x-1 for x in p], prev_snapshot)

      for u,badparts in badunits:
        for p in badparts:
          u.objects[p+1].color = color.red

      prev_snapshot = d
      # For testing only
      # start remove
      while not scene.kb.keys:
        rate(1)
      k = scene.kb.getkey()
      # end remove

if __name__ == '__main__':
  import sys
  if len(sys.argv) == 2:
    s=Scene()
    s.render(sys.argv[1])
  else:
    unit()

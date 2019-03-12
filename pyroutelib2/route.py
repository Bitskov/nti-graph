#!/usr/bin/python
#----------------------------------------------------------------
# Routing for OSM data
#
#------------------------------------------------------
# Usage as library:
#   datastore = loadOsm('transport type')
#   router = Router(datastore)
#   result, route = router.doRoute(node1, node2)
#
# (where transport is cycle, foot, car, etc...)
#------------------------------------------------------
# Copyright 2007-2008, Oliver White
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#------------------------------------------------------
import sys
import math 
from pyroutelib2.loadOsm import LoadOsm

class Router(object):
  def __init__(self, data):
    self.data = data
    

  def distance(self,n1,n2):
    """Calculate distance between two nodes"""
    lat1 = self.data.rnodes[n1][0]
    lon1 = self.data.rnodes[n1][1]
    lat2 = self.data.rnodes[n2][0]
    lon2 = self.data.rnodes[n2][1]
    # TODO: projection issues
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    dist2 = dlat * dlat + dlon * dlon
    dist = math.sqrt(dist2)
    return(dist)

  def doRoute(self,start,end):
    """Do the routing"""
    self.searchEnd = end
    closed = [start]
    self.queue = []
    
    # Start by queueing all outbound links from the start node
    blankQueueItem = {'end':-1,'distance':0,'nodes':str(start)}

    try:
      for i, weight in self.data.routing[start].items():
        self.addToQueue(start,i, blankQueueItem, weight)
    except KeyError:
      return('no_such_node',[])

    # Limit for how long it will search
    count = 0
    while count < 1000000:
      count = count + 1
      try:
        nextItem = self.queue.pop(0)
      except IndexError:
        # Queue is empty: failed
        # TODO: return partial route?
        return('no_route',[])
      x = nextItem['end']
      if x in closed:
        continue
      if x == end:
        # Found the end node - success
        routeNodes = [int(i) for i in nextItem['nodes'].split(",")]
        return('success', routeNodes)
      closed.append(x)
      try:
        for i, weight in self.data.routing[x].items():
          if not i in closed:
            self.addToQueue(x,i,nextItem, weight)
      except KeyError:
        pass
    else:
      return('gave_up',[])
  
  def addToQueue(self,start,end, queueSoFar, weight = 1):
    """Add another potential route to the queue"""

    # getArea() checks that map data is available around the end-point,
    # and downloads it if necessary
    #
    # TODO: we could reduce downloads even more by only getting data around
    # the tip of the route, rather than around all nodes linked from the tip
    end_pos = self.data.rnodes[end]
    self.data.getArea(end_pos[0], end_pos[1])
    
    # If already in queue, ignore
    for test in self.queue:
      if test['end'] == end:
        return
    distance = self.distance(start, end)
    if(weight == 0):
      return
    distance = distance / weight
    
    # Create a hash for all the route's attributes
    distanceSoFar = queueSoFar['distance']
    queueItem = { \
      'distance': distanceSoFar + distance,
      'maxdistance': distanceSoFar + self.distance(end, self.searchEnd),
      'nodes': queueSoFar['nodes'] + "," + str(end),
      'end': end}
    
    # Try to insert, keeping the queue ordered by decreasing worst-case distance
    count = 0
    for test in self.queue:
      if test['maxdistance'] > queueItem['maxdistance']:
        self.queue.insert(count,queueItem)
        break
      count = count + 1
    else:
      self.queue.append(queueItem)


from math import radians, cos, sin, asin, sqrt
def haversine(n1,n2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    
    lat1 = n1[0]
    lon1 = n1[1]
    lat2 = n2[0]
    lon2 = n2[1]
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    # Radius of earth in kilometers is 6371
    km = 6371* c
    return km


def calk_route_dist(route, data):
     answer = 0.0
     for i in range(1, len(route)):
          node_start = data.rnodes[route[i-1]]
          node_end = data.rnodes[route[i]]
          answer += haversine(node_start, node_end)         
     return answer


def get_dist(n1, n2):
    data = LoadOsm("foot")
    node1 = data.findNode(*n1)
    node2 = data.findNode(*n2)
    router = Router(data)
    result, route = router.doRoute(node1, node2)
    return 1000 * calk_route_dist(route, data)

 
if __name__ == "__main__":
  # Test suite - do a little bit of easy routing in birmingham
  data = LoadOsm("foot")

  n1 = (52.282673935069106, 104.28143367544139,)
  n2 = (52.282374539713466, 104.28054854646648,)
  n4 = (52.281596431286715, 104.27944884077036,)
  
  node1 = data.findNode(*n1) #52.282673935069106, 104.28143367544139
  node2 = data.findNode(*n4) #52.282374539713466, 104.28054854646648

 # print(node1)
 # print(node2)

  router = Router(data)
  result, route = router.doRoute(node1, node2)
  if result == 'success':
    # list the nodes
    print("ROUTE")
    print("---------------------------")
    print(route)
    print("---------------------------")
 # print("Points")

    # list the lat/long
    for i in route:
      node = data.rnodes[i]
     # print(distance)
      print("%d: %f,%f" % (i,node[0],node[1]))
  else:
    print("Failed (%s)" % result)
  print(1000 * calk_route_dist(route, data))
  
  print(get_dist(n1, n4))


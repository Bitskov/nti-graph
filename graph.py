from pyroutelib2.route import get_dist
import copy
import json


class Point:

    def __init__(self, name, x, y, coords, delay_time):
        self.name = name
        self.x = x
        self.y = y
        self.coords = coords
        self.delay_time = delay_time  # Сколько по времени занимает нахождение в точке
        self.overloaded_coeff = 0.5
        self.waiting_time = 0  # Сколько суммарно на этой точке ждали команды. Если в точке ждут две команды
        # то счетчик увеличивается на 2
        self.ocupation = []  # Список команд, находящихся в данной точке (очередь)

    def __str__(self):
        return "%s %i" % (self.name, self.delay_time)

    def __eq__(self, other):
        return self.name == other.name

    @staticmethod
    def fromJSON(key, value):
        """
        :param key: Имя точки из json объекта
        :param value: Все остальные параметры точки
        :return: экземпляр Point
        """
        return Point(key, int(value['x']), int(value['y']),
                     (float(value['coords']['latitude']), float(value['coords']['longitude']),),
                     int(value['delay_time']))


class Edge:

    def __init__(self, point1, point2, delay_time):
        self.point1 = point1
        self.point2 = point2
        self.delay_time = delay_time

    def __str__(self):
        return "%s %s %i" % (self.point1, self.point2, self.delay_time)


class Graph:

    def __init__(self, points):
        self.points = points
        self.edges = []
        # Ниже считаются все возможные ребра и их веса
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                w = get_dist(points[i].coords, points[j].coords)
                self.edges.append(Edge(points[i], points[j], (w / 1.5 + 30) // 60, ))  # Тут примерная формула, которая
                # должна показывать кол-во минут, за которые проходится ребро

    def __str__(self):
        s = ""
        for edge in self.edges:
            s += str(edge) + "\n"
        return s

    def get_point(self, point):
        for p in self.points:
            if p == point:
                return p
        return None

    def get_point_by_name(self, name):
        # Для JSON понадобилось искать точку по х и у, эта функция для этого
        for p in self.points:
            if p.name == name:
                return p
        return None

    def get_edge(self, point1, point2):
        # Ребро из графа, соединяющее point1 и point2
        for i in range(len(self.edges)):
            if self.edges[i].point1 == point1 and self.edges[i].point2 == point2:
                return Edge(self.edges[i].point1, self.edges[i].point2, self.edges[i].delay_time)
            elif self.edges[i].point1 == point2 and self.edges[i].point2 == point1:
                return Edge(self.edges[i].point2, self.edges[i].point1, self.edges[i].delay_time)
        return None

    @staticmethod
    def fromJSON(json_obj):
        points = []
        for key, value in json_obj.items():
            points.append(Point.fromJSON(key, value))
        return Graph(points)

    def toJSON(self, short=False):
        s = "\"points\": {\n"
        if not short:
            for point in self.points:
                s += '"%s":{"x": %i, "y": %i, "coords":{"latitude":%f, "longitude": %f}, ' \
                     '"delay_time":%i, "overloaded_coeff":%f}' % \
                     (point.name, point.x, point.y, point.coords[0], point.coords[1], point.delay_time,
                      point.overloaded_coeff)
                if point == self.points[-1]:
                    s += "\n"
                else:
                    s += ",\n"
        else:
            for point in self.points:
                s += '"%s":{"x": %i, "y": %i, "coords":{"latitude":%f, "longitude": %f}, ' \
                     '"delay_time":%i}' % \
                     (point.name, point.x, point.y, point.coords[0], point.coords[1], point.delay_time)
                if point == self.points[-1]:
                    s += "\n"
                else:
                    s += ",\n"
        s += "}"
        return s


class Way:
    # Путь группы, задается точками

    def __init__(self, name, points):
        self.name = name
        self.points = points
        self.delay = 0
        self.current_pos = (points[0], 0)  # Текущее место группы и время проведенное на точке (не в ожидании)
        # Если группа ждет очередь, то время остается равным 0
        self.finished = False  # Закончился ли маршрут

    def __str__(self):
        s = ""
        for p in self.points:
            s += str(p) + "\n"
        return s

    def next_point(self, point):
        # Следующяя точка маршрута
        for i in range(len(self.points) - 1):
            if self.points[i] == point:
                return self.points[i + 1]
        return None

    @staticmethod
    def fromJSON(name, json_obj, graph):
        points = []
        for element in json_obj['edges']:
            points.append(graph.get_point_by_name(element["from"]))
        points.append(graph.get_point_by_name(json_obj['edges'][len(json_obj['edges']) - 1]["to"]))
        return Way(name, points)


def simulate_walking(graph, ways):
    ans = []  # дополнительные данные на выход (возможно не все)
    time = 0

    # Группы ставятся в очередь на начальные точки
    for way in ways:
        graph.get_point(way.current_pos[0]).ocupation.append(way)

    # Цикл ходьбы
    while True:

        finished = 0  # Сколько групп в данный момент закончили маршрут
        change_occupation = []

        for way in ways:
            # print(way.current_pos[0], way.current_pos[1], end=' || ')
            if not way.finished:
                # Если группа находится на ребре или группа находится на первом месте в очереди
                if type(way.current_pos[0]) == Edge or way == graph.get_point(way.current_pos[0]).ocupation[0]:
                    # Время в точке увеличивается на 1
                    way.current_pos = (way.current_pos[0], way.current_pos[1] + 1,)
                else:
                    # Иначе, время ожидания в точке увеличивается и время,
                    # которое группа провела в очереди увеличивается
                    graph.get_point(way.current_pos[0]).waiting_time += 1
                    way.delay += 1

                # Если время в точке (ребре) равно времени, которое необходимо там провести,
                # то точка маршрута меняется на следующую
                if way.current_pos[1] == way.current_pos[0].delay_time:

                    # Если группа была в точке, следующее место ребро
                    if type(way.current_pos[0]) == Point:
                        # Находятся точки ребра
                        point1 = way.current_pos[0]
                        point2 = way.next_point(point1)
                        # Группа убирается из очереди
                        change_occupation.append(graph.get_point(point1))
                        # Если следующая точка нашлась, то текущее местоположение меняется на новое ребро
                        # Иначе путь отмечается как завершенный
                        if point2:
                            way.current_pos = (graph.get_edge(point1, point2), 0)
                        else:
                            ans.append(way)
                            way.finished = True

                    # Если группа была на ребре, то следующим местом становится второй конец ребра
                    elif type(way.current_pos[0]) == Edge:
                        point = way.current_pos[0].point2
                        way.current_pos = (point, 0)
                        graph.get_point(point).ocupation.append(way)

            else:
                finished += 1
        # print()

        for p in change_occupation:
            graph.get_point(p).ocupation = graph.get_point(p).ocupation[1:]

        # Условие завершения цикла
        if finished == len(ways):
            break
        else:
            time += 1

    return time


def simulate(JSON):
    json_obj = JSON
    graph = Graph.fromJSON(json_obj['chosen_points'])
    ways = []

    # print(dict(json_obj['graphs']))
    for key, way_obj in dict(json_obj['graphs']).items():
        way = Way.fromJSON(key, way_obj, graph)
        ways.append(way)
    print(graph)
    # print([way.name for way in ways])
    walk_result = simulate_walking(graph, ways)
    max_overload_time = 1 if sum([i for i in range(len(ways))]) == 0 else sum([i for i in range(len(ways))])
    # print(max_overload_time)
    for point in graph.points:
        point.overloaded_coeff = (point.waiting_time ) / (max_overload_time * point.delay_time)
        # print(point, ' overloaded_coeff=', point.overloaded_coeff, point.waiting_time, point.delay_time)

    # Простая оценка загруженности
    n = len(graph.points)
    E = 100 / n * sum([p.overloaded_coeff for p in graph.points])

    # Более сложный спопоб
    n = len(graph.points)
    c = 100 / sum([i + 1 for i in range(len(graph.points))])

    overloads = sorted([graph.points[i].overloaded_coeff for i in range(n)])[::-1]

    E1 = c * sum([(n - i) * overloads[i] for i in range(n)])

    # Формирование ответа. Short для детей и Long для стенда
    JSON_RESULT_SHORT = "{" + graph.toJSON(short=True) + ",\n"
    JSON_RESULT_LONG = "{\"width\": %i, \"height\": %i, \"all_points\":" % (int(json_obj['width']), int(json_obj['height'])) \
                                                                                + str(json_obj['all_points']).replace("'",
                                                                                "\"") + ",\n" + graph.toJSON() + ",\n"

    graphs = '"graphs":\n{\n'
    for way in ways:
        graphs += '"%s":[' % way.name
        for i in range(len(way.points)):
            p = way.points[i]
            if p == way.points[0]:
                graphs += '{"from": "%s",' % (p.name)
            elif p == way.points[-1]:
                graphs += '"to": "%s", "time": %i}]' % (p.name, graph.get_edge(p, way.points[i-1]).delay_time)
            else:
                graphs += '"to": "%s", "time": %i},{"from": "%s",' % (p.name, graph.get_edge(p, way.points[i-1]).delay_time, p.name)
        if way != ways[-1]:
            graphs += ",\n"
        else:
            graphs += "\n"
    graphs += "}, \"E\": %i, \n \"time\":%i" % (int(E1), int(walk_result))
    if walk_result >= 120:
        graphs += ",\"warning\": \"time limit exceeded\""
    graphs += "}"
    JSON_RESULT_LONG += graphs
    JSON_RESULT_SHORT += graphs
    return JSON_RESULT_LONG


if __name__ == '__main__':
    JSONSTR = """
    {
	"all_points": {
		"monument": {
			"x": 7,
			"y": 1,
			"coords": {
				"latitude": 52.282673935069106,
				"longitude": 104.28143367544139
			},
			"delay_time": 5
		},
		"pharmacy": {
			"x": 4,
			"y": 3,
			"coords": {
				"latitude": 52.282374539713466,
				"longitude": 104.28054854646648
			},
			"delay_time": 10
		},
		"cafe": {
			"x": 8,
			"y": 7,
			"coords": {
				"latitude": 52.28148621185799,
				"longitude": 104.28177163377725
			},
			"delay_time": 5
		},
		"pizza": {
			"x": 1,
			"y": 3,
			"coords": {
				"latitude": 52.28228077261808,
				"longitude": 104.27936837449991
			},
			"delay_time": 3
		},
		"wooden house": {
			"x": 1,
			"y": 6,
			"coords": {
				"latitude": 52.281596431286715,
				"longitude": 104.27944884077036
			},
			"delay_time": 10
		}
	},
	"chosen_points": {
		"monument": {
			"x": 7,
			"y": 1,
			"coords": {
				"latitude": 52.282673935069106,
				"longitude": 104.28143367544139
			},
			"delay_time": 5
		},
		"pharmacy": {
			"x": 4,
			"y": 3,
			"coords": {
				"latitude": 52.282374539713466,
				"longitude": 104.28054854646648
			},
			"delay_time": 10
		},
		"cafe": {
			"x": 8,
			"y": 7,
			"coords": {
				"latitude": 52.28148621185799,
				"longitude": 104.28177163377725
			},
			"delay_time": 5
		},
		"pizza": {
			"x": 1,
			"y": 3,
			"coords": {
				"latitude": 52.28228077261808,
				"longitude": 104.27936837449991
			},
			"delay_time": 3
		},
		"wooden house": {
			"x": 1,
			"y": 6,
			"coords": {
				"latitude": 52.281596431286715,
				"longitude": 104.27944884077036
			},
			"delay_time": 10
		}
	},
	"graphs": {
		"graph_1": {
			"edges": [
				{
					"from": "monument",
					"to": "pharmacy"
				},
				{
					"from": "pharmacy",
					"to": "cafe"
				},
				{
					"from": "cafe",
					"to": "pizza"
				},
				{
					"from": "pizza",
					"to": "wooden house"
				}
			]
		},
		"graph_2": {
			"edges": [
				{
					"from": "pharmacy",
					"to": "pizza"
				},
				{
					"from": "pizza",
					"to": "cafe"
				},
				{
					"from": "cafe",
					"to": "monument"
				},
				{
					"from": "monument",
					"to": "wooden house"
				}
			]
		},
		"graph_3": {
			"edges": [
				{
					"from": "cafe",
					"to": "pharmacy"
				},
				{
					"from": "pharmacy",
					"to": "monument"
				},
				{
					"from": "monument",
					"to": "wooden house"
				},
				{
					"from": "wooden house",
					"to": "pizza"
				}
			]
		},
		"graph_4": {
			"edges": [
				{
					"from": "cafe",
					"to": "pharmacy"
				},
				{
					"from": "pharmacy",
					"to": "monument"
				},
				{
					"from": "monument",
					"to": "wooden house"
				},
				{
					"from": "wooden house",
					"to": "pizza"
				}
			]
		},
		"graph_5": {
			"edges": [
				{
					"from": "cafe",
					"to": "pharmacy"
				},
				{
					"from": "pharmacy",
					"to": "monument"
				},
				{
					"from": "monument",
					"to": "wooden house"
				},
				{
					"from": "wooden house",
					"to": "pizza"
				}
			]
		}
	}
}"""
    JSONSTR2 = """
    {
	"all_points": {
		"monument": {
			"x": 7,
			"y": 1,
			"coords": {
				"latitude": 52.282673935069106,
				"longitude": 104.28143367544139
			},
			"delay_time": 5
		},
		"pharmacy": {
			"x": 4,
			"y": 3,
			"coords": {
				"latitude": 52.282374539713466,
				"longitude": 104.28054854646648
			},
			"delay_time": 10
		},
		"cafe": {
			"x": 8,
			"y": 7,
			"coords": {
				"latitude": 52.28148621185799,
				"longitude": 104.28177163377725
			},
			"delay_time": 5
		},
		"pizza": {
			"x": 1,
			"y": 3,
			"coords": {
				"latitude": 52.28228077261808,
				"longitude": 104.27936837449991
			},
			"delay_time": 3
		},
		"wooden house": {
			"x": 1,
			"y": 6,
			"coords": {
				"latitude": 52.281596431286715,
				"longitude": 104.27944884077036
			},
			"delay_time": 10
		}
	},
	"chosen_points": {
		"monument": {
			"x": 7,
			"y": 1,
			"coords": {
				"latitude": 52.282673935069106,
				"longitude": 104.28143367544139
			},
			"delay_time": 5
		},
		"pharmacy": {
			"x": 4,
			"y": 3,
			"coords": {
				"latitude": 52.282374539713466,
				"longitude": 104.28054854646648
			},
			"delay_time": 10
		},
		"cafe": {
			"x": 8,
			"y": 7,
			"coords": {
				"latitude": 52.28148621185799,
				"longitude": 104.28177163377725
			},
			"delay_time": 5
		},
		"pizza": {
			"x": 1,
			"y": 3,
			"coords": {
				"latitude": 52.28228077261808,
				"longitude": 104.27936837449991
			},
			"delay_time": 3
		},
		"wooden house": {
			"x": 1,
			"y": 6,
			"coords": {
				"latitude": 52.281596431286715,
				"longitude": 104.27944884077036
			},
			"delay_time": 10
		}
	},
	"graphs": {
		"graph_1": {
			"edges": [
				{
					"from": "monument",
					"to": "pharmacy"
				},
				{
					"from": "pharmacy",
					"to": "cafe"
				},
				{
					"from": "cafe",
					"to": "pizza"
				},
				{
					"from": "pizza",
					"to": "wooden house"
				}
			]
		},
		"graph_2": {
			"edges": [
				{
					"from": "monument",
					"to": "pharmacy"
				},
				{
					"from": "pharmacy",
					"to": "cafe"
				},
				{
					"from": "cafe",
					"to": "pizza"
				},
				{
					"from": "pizza",
					"to": "wooden house"
				}
			]
		},
		"graph_3": {
			"edges": [
				{
					"from": "monument",
					"to": "pharmacy"
				},
				{
					"from": "pharmacy",
					"to": "cafe"
				},
				{
					"from": "cafe",
					"to": "pizza"
				},
				{
					"from": "pizza",
					"to": "wooden house"
				}
			]
		}
	}
}"""
    simulate(json.loads(JSONSTR))

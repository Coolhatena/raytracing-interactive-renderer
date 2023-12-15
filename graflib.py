import math
import numpy as np


# The PutPixel() function.
def PutPixel(canvas, x, y, color):
	x = canvas.width/2 + x
	y = canvas.height/2 - y

	color = np.array(color).astype(int)

	if (x < 0 or x >= canvas.width or y < 0 or y >= canvas.height):
		return
	canvas.putpixel((int(x), int(y)), tuple(color))


# ======================================================================
#    Depth buffer.
# ======================================================================

def UpdateDepthBufferIfCloser(canvas, depth_buffer, x, y, inv_z):
	x = canvas.width/2 + (x | 0)
	y = canvas.height/2 - (y | 0) - 1

	if (x < 0 or x >= canvas.width or y < 0 or y >= canvas.height):
		return False
	

	offset = x + canvas.width*y
	if (depth_buffer[int(offset)] == None or depth_buffer[int(offset)] < inv_z):
		depth_buffer[int(offset)] = inv_z
		return True
	
	return False



# ======================================================================
#    Data model.
# ======================================================================

# A Point.
class Pt:
	def __init__(self, x, y, h):
		self.x = x
		self.y = y
		self.h = h



# A 3D vertex.
class Vertex:
	def __init__(self, x, y, z):
		self.x = x
		self.y = y
		self.z = z



# A 4D vertex (a 3D vertex in homogeneous coordinates).
class Vertex4:
	def __init__(self, arg1, y = 0, z = 0, w = 0):
		if isinstance(arg1, Vertex):
			self.x = arg1.x
			self.y = arg1.y
			self.z = arg1.z
			self.w = 1
			
		elif isinstance(arg1, Vertex4):
			self.x = arg1.x
			self.y = arg1.y
			self.z = arg1.z
			self.w = arg1.w
		else:
			self.x = arg1
			self.y = y
			self.z = z
			self.w = w


# A 4x4 matrix.
class Mat4x4:
	def __init__(self, data):
		self.data = data


Identity4x4 = Mat4x4([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])


# A Triangle.
class Triangle:
	def __init__(self, indexes, color, normals):
		self.indexes = indexes
		self.color = color
		self.normals = normals



# A Model.
class Model:
	def __init__(self, vertices, triangles, bounds_center, bounds_radius):
		self.vertices = vertices
		self.triangles = triangles
		self.bounds_center = bounds_center
		self.bounds_radius = bounds_radius


# An Instance.
class Instance: 
	def __init__(self, model, position, orientation = Identity4x4, scale = 1.0):
		self.model = model
		self.position = position
		self.orientation = orientation
		self.scale = scale

		self.transform = MultiplyMM4(MakeTranslationMatrix(self.position), MultiplyMM4(self.orientation, MakeScalingMatrix(self.scale)))



# The Camera.
class Camera: 
	def __init__(self, position, orientation):
		self.position = position
		self.orientation = orientation
		self.clipping_planes = []



# A Clipping Plane.
class Plane: 
	def __init__(self, normal, distance):
		self.normal = normal
		self.distance = distance



# A Light.
LT_AMBIENT = 0
LT_POINT = 1
LT_DIRECTIONAL = 2

class Light: 
	def __init__(self, type, intensity, vector = Vertex(-1, 0, 1)):
		self.type = type
		self.intensity = intensity
		self.vector = vector


# ======================================================================
#    Linear algebra and helpers.
# ======================================================================

# Computes k * vec.
def Multiply(k, vec):
	return Vertex(k*vec.x, k*vec.y, k*vec.z)



# Computes dot product.
def Dot(v1, v2):
	return v1.x*v2.x + v1.y*v2.y + v1.z*v2.z



# Computes cross product.
def Cross(v1, v2):
	return Vertex(
		v1.y*v2.z - v1.z*v2.y,
		v1.z*v2.x - v1.x*v2.z,
		v1.x*v2.y - v1.y*v2.x)



# Computes v1 + v2.
def Add(v1, v2):
	return Vertex(v1.x + v2.x, v1.y + v2.y, v1.z + v2.z)



# Computes vector magnitude.
def Magnitude(v1):
	return math.sqrt(Dot(v1, v1))


# Makes a transform matrix for a rotation around the OY axis.
def MakeOYRotationMatrix(degrees):
	cos = math.cos(degrees*math.pi/180.0)
	sin = math.sin(degrees*math.pi/180.0)

	return Mat4x4([[cos, 0, -sin, 0],
								 [    0, 1,        0, 0],
								 [sin, 0,    cos, 0],
								 [    0, 0,        0, 1]])



# Makes a transform matrix for a translation.
def MakeTranslationMatrix(translation):
	return Mat4x4([[1, 0, 0, translation.x],
								 [0, 1, 0, translation.y],
								 [0, 0, 1, translation.z],
								 [0, 0, 0,                         1]])


# Makes a transform matrix for a scaling.
def MakeScalingMatrix(scale):
	return Mat4x4([[scale,         0,         0, 0],
								 [        0, scale,         0, 0],
								 [        0,         0, scale, 0],
								 [        0,         0,         0, 1]])


# Multiplies a 4x4 matrix and a 4D vector.
def MultiplyMV(mat4x4, vec4):
	result = [0, 0, 0, 0]
	vec = [vec4.x, vec4.y, vec4.z, vec4.w]

	for i in range(0, 4):
		for j in range(0, 4):
			result[i] += mat4x4.data[i][j]*vec[j]

	return Vertex4(result[0], result[1], result[2], result[3])


# Multiplies two 4x4 matrices.
def MultiplyMM4(matA, matB):
	result = Mat4x4([[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])

	for i in range(0, 4):
		for j in range(0, 4):
			for k in range(0, 4):
				result.data[i][j] += matA.data[i][k]*matB.data[k][j]

	return result


# Transposes a 4x4 matrix.
def Transposed(mat):
	result = Mat4x4([[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
	for i in range(0, 4):
		for j in range(0, 4):
			result.data[i][j] = mat.data[j][i]

	return result



def Clamp(value):
	if (value < 0):
		return 0
	if (value > 255):
		return 255

	return value



# Adds two colors.
def AddColor(c1, c2):
	return [Clamp(c1[0] + c2[0]), Clamp(c1[1] + c2[1]), Clamp(c1[2] + c2[2])]



def MultiplyColor(color, k):
	return [Clamp(color[0]*k), Clamp(color[1]*k), Clamp(color[2]*k)]


# ======================================================================
#    Rasterization code.
# ======================================================================

# Scene setup.
viewport_size = 1
projection_plane_z = 1


def Interpolate(i0, d0, i1, d1):
	if (i0 == i1):
		return [d0]

	values = []
	a = (d1 - d0) / (i1 - i0)
	d = d0
	for i in range(i0, i1+1):
		values.append(d)
		d += a

	return values


def DrawLine(p0, p1, color):
	dx = p1.x - p0.x 
	dy = p1.y - p0.y

	if (math.abs(dx) > math.abs(dy)):
		# The line is horizontal-ish. Make sure it's left to right.
		if (dx < 0):
			p0, p1 = p1, p0

		# Compute the Y values and draw.
		ys = Interpolate(p0.x, p0.y, p1.x, p1.y)
		for x in range(p0.x, p1.x):
			PutPixel(x, ys[(x - p0.x) | 0], color)
		
	else:
		# The line is verical-ish. Make sure it's bottom to top.
		if (dy < 0):
			p0, p1 = p1, p0

		# Compute the X values and draw.
		xs = Interpolate(p0.y, p0.x, p1.y, p1.x)
		for y in range(p0.y, p1.y):
			PutPixel(xs[(y - p0.y) | 0], y, color)


def DrawWireframeTriangle(p0, p1, p2, color):
	DrawLine(p0, p1, color)
	DrawLine(p1, p2, color)
	DrawLine(p0, p2, color)


# Converts 2D viewport coordinates to 2D canvas coordinates.
def ViewportToCanvas(p2d, canvas):
	return Pt(int(p2d.x * canvas.width / viewport_size) | 0, int(p2d.y * canvas.height / viewport_size) | 0, None)


# Converts 2D canvas coordinates to 2D viewport coordinates.
def CanvasToViewport(canvas, p2d):
	return Pt(
		(p2d.x * viewport_size / canvas.width),
		(p2d.y * viewport_size / canvas.height),
		None
	)


def ProjectVertex(canvas, v):
	return ViewportToCanvas(Pt(v.x * projection_plane_z / v.z, v.y * projection_plane_z / v.z, None), canvas)


def UnProjectVertex(canvas, x, y, inv_z):
	oz = 1.0 / inv_z
	ux = x*oz / projection_plane_z
	uy = y*oz / projection_plane_z
	p2d = CanvasToViewport(canvas, Pt(ux, uy, None))
	return Vertex(p2d.x, p2d.y, oz)


# Sort the points from bottom to top.
# Technically, sort the indexes to the vertex indexes in the triangle from bottom to top.
def SortedVertexIndexes(vertex_indexes, projected):
	indexes = [0, 1, 2]

	if (projected[vertex_indexes[indexes[1]]].y < projected[vertex_indexes[indexes[0]]].y):
		indexes[0], indexes[1] = indexes[1], indexes[0] 

	if (projected[vertex_indexes[indexes[2]]].y < projected[vertex_indexes[indexes[0]]].y): 
		indexes[0], indexes[2] = indexes[2], indexes[0] 

	if (projected[vertex_indexes[indexes[2]]].y < projected[vertex_indexes[indexes[1]]].y): 
		indexes[1], indexes[2] = indexes[2], indexes[1] 

	return indexes


def ComputeTriangleNormal(v0, v1, v2):
	v0v1 = Add(v1, Multiply(-1, v0))
	v0v2 = Add(v2, Multiply(-1, v0))
	return Cross(v0v1, v0v2)


def ComputeIllumination(vertex, normal, camera, lights):
	illumination = 0
	for l in range(0, len(lights)):
		light = lights[l]
		if (light.type == LT_AMBIENT):
			illumination += light.intensity
			continue
		
		# var vl
		if (light.type == LT_DIRECTIONAL):
			cameraMatrix = Transposed(camera.orientation)
			rotated_light = MultiplyMV(cameraMatrix, Vertex4(light.vector))
			vl = rotated_light
		elif (light.type == LT_POINT):
			cameraMatrix = MultiplyMM4(Transposed(camera.orientation), MakeTranslationMatrix(Multiply(-1, camera.position)))
			transformed_light = MultiplyMV(cameraMatrix, Vertex4(light.vector))
			vl = Add(transformed_light, Multiply(-1, vertex)) # light.vector - vertex
		

		# Diffuse component.
		if (LightingModel & LM_DIFFUSE):
			cos_alpha = Dot(vl, normal) / (Magnitude(vl) * Magnitude(normal))
			if (cos_alpha > 0):
				illumination += cos_alpha * light.intensity

		# Specular component.
		if (LightingModel & LM_SPECULAR):
			reflected = Add(Multiply(2*Dot(normal, vl), normal), Multiply(-1, vl))
			view = Add(camera.position, Multiply(-1, vertex))

			cos_beta = Dot(reflected, view) / (Magnitude(reflected) * Magnitude(view))
			if (cos_beta > 0):
				specular = 50
				illumination += math.pow(cos_beta, specular) * light.intensity

	return illumination



LM_DIFFUSE = 1
LM_SPECULAR = 2

SM_FLAT = 0
SM_GOURAUD = 1
SM_PHONG = 2

LightingModel = LM_SPECULAR | LM_DIFFUSE
ShadingModel = SM_FLAT
UseVertexNormals = True

def EdgeInterpolate(y0, v0, y1, v1, y2, v2):
	v01 = Interpolate(y0, v0, y1, v1)
	v12 = Interpolate(y1, v1, y2, v2)
	v02 = Interpolate(y0, v0, y2, v2)
	v01.pop()
	v012 = v01 + v12
	return v02, v012



def RenderTriangle(canvas, depth_buffer, triangle, vertices, projected, camera, lights, orientation):
	# Sort by projected point Y.
	indexes = SortedVertexIndexes(triangle.indexes, projected)
	i0, i1, i2 = indexes[0], indexes[1], indexes[2]

	v0 = vertices[triangle.indexes[i0]]
	v1 = vertices[triangle.indexes[i1]]
	v2 = vertices[triangle.indexes[i2]]

	# Compute triangle normal. Use the unsorted vertices, otherwise the winding of the points may change.
	normal = ComputeTriangleNormal(vertices[triangle.indexes[0]], vertices[triangle.indexes[1]], vertices[triangle.indexes[2]])

	# Backface culling.
	vertex = vertices[triangle.indexes[0]]
	if (Dot(vertex, normal) >= 0):
		return
	

	# Get attribute values (X, 1/Z) at the vertices.
	p0 = projected[triangle.indexes[i0]]
	p1 = projected[triangle.indexes[i1]]
	p2 = projected[triangle.indexes[i2]]

	# Compute attribute values at the edges.
	x02, x012 = EdgeInterpolate(p0.y, p0.x, p1.y, p1.x, p2.y, p2.x)
	iz02, iz012 = EdgeInterpolate(p0.y, 1.0/v0.z, p1.y, 1.0/v1.z, p2.y, 1.0/v2.z)

	if (UseVertexNormals):
		transform = MultiplyMM4(Transposed(camera.orientation), orientation)
		normal0 = MultiplyMV(transform, Vertex4(triangle.normals[i0]))
		normal1 = MultiplyMV(transform, Vertex4(triangle.normals[i1]))
		normal2 = MultiplyMV(transform, Vertex4(triangle.normals[i2]))
	else:
		normal0 = normal
		normal1 = normal
		normal2 = normal
	
	# Gouraud?
	i02, i012 = EdgeInterpolate(p0.y, i0, p1.y, i1, p2.y, i2)
	nx02, nx012 = EdgeInterpolate(p0.y, normal0.x, p1.y, normal1.x, p2.y, normal2.x)
	ny02, ny012 = EdgeInterpolate(p0.y, normal0.y, p1.y, normal1.y, p2.y, normal2.y)
	nz02, nz012 = EdgeInterpolate(p0.y, normal0.z, p1.y, normal1.z, p2.y, normal2.z)

	if (ShadingModel == SM_FLAT):
		# Flat shading: compute lighting for the entire triangle.
		center = Vertex((v0.x + v1.x + v2.x)/3.0, (v0.y + v1.y + v2.y)/3.0, (v0.z + v1.z + v2.z)/3.0)
		intensity = ComputeIllumination(center, normal0, camera, lights)
	elif (ShadingModel == SM_GOURAUD):
		# Gouraud shading: compute lighting at the vertices, and interpolate.
		i0 = ComputeIllumination(v0, normal0, camera, lights)
		i1 = ComputeIllumination(v1, normal1, camera, lights)
		i2 = ComputeIllumination(v2, normal2, camera, lights)
	elif (ShadingModel == SM_PHONG):
		# Phong shading: interpolate normal vectors.
		...


	# Determine which is left and which is right.
	m = int(len(x02)/2) | 0
	if (x02[m] < x012[m]):
		x_left, x_right = x02, x012
		iz_left, iz_right = iz02, iz012
		i_left, i_right = i02, i012

		nx_left, nx_right = nx02, nx012
		ny_left, ny_right = ny02, ny012
		nz_left, nz_right = nz02, nz012
	else:
		x_left, x_right = x012, x02
		iz_left, iz_right = iz012, iz02
		i_left, i_right = i012, i02

		nx_left, nx_right = nx012, nx02
		ny_left, ny_right = ny012, ny02
		nz_left, nz_right = nz012, nz02


	# Draw horizontal segments.
	for y in range(p0.y, p2.y+1):
		xl, xr = int(x_left[y - p0.y]) | 0, int(x_right[y - p0.y]) | 0

		# Interpolate attributes for self scanline.
		zl, zr = iz_left[y - p0.y], iz_right[y - p0.y]
		zscan = Interpolate(xl, zl, xr, zr)
	# console.log(zscan)

		if (ShadingModel == SM_GOURAUD):
			il, ir = i_left[y - p0.y], i_right[y - p0.y]
			iscan = Interpolate(xl, il, xr, ir)
		elif (ShadingModel == SM_PHONG):
			nxl, nxr = nx_left[y - p0.y], nx_right[y - p0.y]
			nyl, nyr = ny_left[y - p0.y], ny_right[y - p0.y]
			nzl, nzr = nz_left[y - p0.y], nz_right[y - p0.y]

			nxscan = Interpolate(xl, nxl, xr, nxr)
			nyscan = Interpolate(xl, nyl, xr, nyr)
			nzscan = Interpolate(xl, nzl, xr, nzr)

		for x in range(xl, xr):
			inv_z = zscan[x - xl]
			if (UpdateDepthBufferIfCloser(canvas, depth_buffer, x, y, inv_z)):

				if (ShadingModel == SM_FLAT):
					# Just use the per-triangle intensity.
					...
				elif (ShadingModel == SM_GOURAUD):
					intensity = iscan[x-xl]
				elif (ShadingModel == SM_PHONG):
					vertex = UnProjectVertex(canvas, x, y, inv_z)
					normal = Vertex(nxscan[x - xl], nyscan[x - xl], nzscan[x - xl])
					intensity = ComputeIllumination(vertex, normal, camera, lights)
				

				PutPixel(canvas, x, y, MultiplyColor(triangle.color, intensity))



# Clips a triangle against a plane. Adds output to triangles and vertices.
def ClipTriangle(triangle, plane, triangles, vertices):
	v0 = vertices[triangle.indexes[0]]
	v1 = vertices[triangle.indexes[1]]
	v2 = vertices[triangle.indexes[2]]

	in0 = Dot(plane.normal, v0) + plane.distance > 0
	in1 = Dot(plane.normal, v1) + plane.distance > 0
	in2 = Dot(plane.normal, v2) + plane.distance > 0

	in_count = in0 + in1 + in2
	if (in_count == 0):
		# Nothing to do - the triangle is fully clipped out.
		...
	elif (in_count == 3):
		# The triangle is fully in front of the plane.
		triangles.append(triangle)
	elif (in_count == 1):
		# The triangle has one vertex in. Output is one clipped triangle.
		...
	elif (in_count == 2):
		# The triangle has two vertices in. Output is two clipped triangles.
		...


def TransformAndClip(clipping_planes, model, scale, transform):
	# Transform the bounding sphere, and attempt early discard.
	center = MultiplyMV(transform, Vertex4(model.bounds_center))
	radius = model.bounds_radius*scale
	for p in range(0, len(clipping_planes)):
		distance = Dot(clipping_planes[p].normal, center) + clipping_planes[p].distance
		if (distance < -radius):
			return None

	# Apply modelview transform.
	vertices = []
	for i in range(0, len(model.vertices)):
		vertices.append(MultiplyMV(transform, Vertex4(model.vertices[i])))

	# Clip the entire model against each successive plane.
	triangles = model.triangles.copy()
	for p in range(0, len(clipping_planes)):
		new_triangles = []
		for i in range(0, len(triangles)):
			ClipTriangle(triangles[i], clipping_planes[p], new_triangles, vertices)
		
		triangles = new_triangles

	return Model(vertices, triangles, center, model.bounds_radius)


def RenderModel(canvas, depth_buffer, model, camera, lights, orientation):
	projected = []
	for i in range(0, len(model.vertices)):
		projected.append(ProjectVertex(canvas, Vertex4(model.vertices[i])))
	for i in range(0, len(model.triangles)):
		RenderTriangle(canvas, depth_buffer, model.triangles[i], model.vertices, projected, camera, lights, orientation)


def RenderScene(canvas, depth_buffer, camera, instances, lights):
	cameraMatrix = MultiplyMM4(Transposed(camera.orientation), MakeTranslationMatrix(Multiply(-1, camera.position)))

	for i in range(0, len(instances)):
		transform = MultiplyMM4(cameraMatrix, instances[i].transform)
		clipped = TransformAndClip(camera.clipping_planes, instances[i].model, instances[i].scale, transform)
		if (clipped != None):
			RenderModel(canvas, depth_buffer, clipped, camera, lights, instances[i].orientation)


# ----- Sphere model generator -----
def GenerateSphere(divs, color):
	vertices = []
	triangles = []

	delta_angle = 2.0*math.pi / divs

	# Generate vertices and normals.
	for d in range(0, divs+1):
		y = (2.0 / divs) * (d - divs/2)
		radius = math.sqrt(1.0 - y*y)
		for i in range(0, divs):
			vertex = Vertex(radius*math.cos(i*delta_angle), y, radius*math.sin(i*delta_angle))
			vertices.append(vertex)


	# Generate triangles.
	for d in range(0, divs):
		for i in range(0, divs):
			i0 = d*divs + i
			i1 = (d+1)*divs + (i+1)%divs
			i2 = divs*d + (i+1)%divs
			tri0 = [i0, i1, i2]
			tri1 = [i0, i0+divs, i1]
			triangles.append(Triangle(tri0, color, [vertices[tri0[0]], vertices[tri0[1]], vertices[tri0[2]]]))
			triangles.append(Triangle(tri1, color, [vertices[tri1[0]], vertices[tri1[1]], vertices[tri1[2]]]))


	return Model(vertices, triangles, Vertex(0, 0, 0), 1.0)


vertices = [
	Vertex(1, 1, 1),
	Vertex(-1, 1, 1),
	Vertex(-1, -1, 1),
	Vertex(1, -1, 1),
	Vertex(1, 1, -1),
	Vertex(-1, 1, -1),
	Vertex(-1, -1, -1),
	Vertex(1, -1, -1)
]

RED = [255, 0, 0]
GREEN = [0, 255, 0]
BLUE = [0, 0, 255]
YELLOW = [255, 255, 0]
PURPLE = [255, 0, 255]
CYAN = [0, 255, 255]

triangles = [
	Triangle([0, 1, 2], RED,        [Vertex( 0,    0,    1), Vertex( 0,    0,    1), Vertex( 0,    0,    1)]),
	Triangle([0, 2, 3], RED,        [Vertex( 0,    0,    1), Vertex( 0,    0,    1), Vertex( 0,    0,    1)]),
	Triangle([4, 0, 3], GREEN,    [Vertex( 1,    0,    0), Vertex( 1,    0,    0), Vertex( 1,    0,    0)]),
	Triangle([4, 3, 7], GREEN,    [Vertex( 1,    0,    0), Vertex( 1,    0,    0), Vertex( 1,    0,    0)]),
	Triangle([5, 4, 7], BLUE,     [Vertex( 0,    0, -1), Vertex( 0,    0, -1), Vertex( 0,    0, -1)]),
	Triangle([5, 7, 6], BLUE,     [Vertex( 0,    0, -1), Vertex( 0,    0, -1), Vertex( 0,    0, -1)]),
	Triangle([1, 5, 6], YELLOW, [Vertex(-1,    0,    0), Vertex(-1,    0,    0), Vertex(-1,    0,    0)]),
	Triangle([1, 6, 2], YELLOW, [Vertex(-1,    0,    0), Vertex(-1,    0,    0), Vertex(-1,    0,    0)]),
	Triangle([1, 0, 5], PURPLE, [Vertex( 0,    1,    0), Vertex( 0,    1,    0), Vertex( 0,    1,    0)]),
	Triangle([5, 0, 4], PURPLE, [Vertex( 0,    1,    0), Vertex( 0,    1,    0), Vertex( 0,    1,    0)]),
	Triangle([2, 6, 7], CYAN,     [Vertex( 0, -1,    0), Vertex( 0, -1,    0), Vertex( 0, -1,    0)]),
	Triangle([2, 7, 3], CYAN,     [Vertex( 0, -1,    0), Vertex( 0, -1,    0), Vertex( 0, -1,    0)]),
]
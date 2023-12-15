import math
import tkinter as tk
import graflib as gl
import numpy as np
from PIL import Image, ImageTk

class LightData:
	def __init__(self, light_x = 1, light_y = 1, light_z = 1, light_intensity = 1):
		self.x = light_x
		self.y = light_y
		self.z = light_z
		self.intensity = light_intensity
		

class CameraData:
	def __init__(self, camera_x = 0, camera_y = 0, camera_z = 0, camera_rotation = 0):
		self.x = camera_x
		self.y = camera_y
		self.z = camera_z
		self.rotation = camera_rotation


class FigureData:
	def __init__(self, figure_type = "Cube", figure_x = 0, figure_y = 0, figure_z = 5, figure_scale = 1, figure_rotation = 0):
		self.type = figure_type
		self.x = figure_x
		self.y = figure_y
		self.z = figure_z
		self.scale = figure_scale
		self.rotation = figure_rotation		


class rootApp(tk.Tk):
	def __init__(self):
		tk.Tk.__init__(self)
		self._frame = None
		self.switch_frame(StartPage)

	def switch_frame(self, frame_class):
		# Destroys current frame and replaces it with a new one.
		new_frame = frame_class(self)
		if self._frame is not None:
			self._frame.destroy()
		self._frame = new_frame
		self._frame.pack()


class StartPage(tk.Frame):
	def __init__(self, master):
		tk.Frame.__init__(self, master)
		leftSide = tk.Frame(self)
		rightSide = tk.Frame(self)
		lightControllers = tk.LabelFrame(rightSide, text="Iluminacion")
		figureControllers = tk.LabelFrame(rightSide, text="Figura")
		cameraControllers = tk.LabelFrame(rightSide, text="Camara")

		light = LightData()
		camera = CameraData()
		figure = FigureData()
		canva = self.drawCanvas(light, camera, figure)
		tkpic = ImageTk.PhotoImage(canva)
		label = tk.Label(leftSide, image=tkpic)
		label.image = tkpic  # Save reference to image
		label.pack(padx=10, pady=10)

		@staticmethod
		def callback():
			light, camera, figure = self.buildRenderData()
			canva = self.drawCanvas(light, camera, figure)
			tkpic = ImageTk.PhotoImage(canva)
			label.config(image=tkpic)
			label.image = tkpic  # Save reference to image

		# Light Controllers
		self.x_light_bar = tk.Scale(lightControllers, label="X" ,from_=5, to=-5)
		self.x_light_bar.pack(side=tk.LEFT)
		self.y_light_bar = tk.Scale(lightControllers, label="Y" ,from_=5, to=-5)
		self.y_light_bar.pack(side=tk.LEFT)
		self.z_light_bar = tk.Scale(lightControllers, label="Z" ,from_=5, to=-5)
		self.z_light_bar.pack(side=tk.LEFT)
		self.intensity_light_bar = tk.Scale(lightControllers, label="Intensidad" ,from_=0, to=100)
		self.intensity_light_bar.pack(side=tk.LEFT)

		# Figure UI controls
		self.x_figure_bar = tk.Scale(figureControllers, label="X" ,from_=5, to=-5)
		self.x_figure_bar.pack(side=tk.LEFT)
		self.y_figure_bar = tk.Scale(figureControllers, label="Y" ,from_=5, to=-5)
		self.y_figure_bar.pack(side=tk.LEFT)
		self.z_figure_bar = tk.Scale(figureControllers, label="Z" ,from_=15, to=5)
		self.z_figure_bar.pack(side=tk.LEFT)
		self.scale_figure_bar = tk.Scale(figureControllers, label="Scale" ,from_=1, to=5)
		self.scale_figure_bar.pack(side=tk.LEFT)
		self.rotation_figure_bar = tk.Scale(figureControllers, label="Rotation" ,from_=-180, to=180)
		self.rotation_figure_bar.pack(side=tk.LEFT)

		lighting_list = ["Flat", "Gouraud", "Phong"]
		self.actual_lighting = tk.StringVar()
		self.actual_lighting.set("Flat")
		self.lighting_menu = tk.OptionMenu(figureControllers, self.actual_lighting, *lighting_list) 
		self.lighting_menu.pack() 

		figures_list = ["Cube", "Sphere"]
		self.actual_figure = tk.StringVar()
		self.actual_figure.set("Cube")
		self.figure_menu = tk.OptionMenu(figureControllers, self.actual_figure, *figures_list) 
		self.figure_menu.pack() 

		# Camera UI controls
		self.x_camera_bar = tk.Scale(cameraControllers, label="X" ,from_=5, to=-5)
		self.x_camera_bar.pack(side=tk.LEFT)
		self.y_camera_bar = tk.Scale(cameraControllers, label="Y" ,from_=5, to=-5)
		self.y_camera_bar.pack(side=tk.LEFT)
		self.z_camera_bar = tk.Scale(cameraControllers, label="Z" ,from_=-5, to=1)
		self.z_camera_bar.pack(side=tk.LEFT)
		self.rotation_camera_bar = tk.Scale(cameraControllers, label="Rotation" ,from_=-180, to=180)
		self.rotation_camera_bar.pack(side=tk.LEFT)
		
		lightControllers.pack(padx=10)
		figureControllers.pack(padx=10)
		cameraControllers.pack(padx=10)

		render_button = tk.Button(rightSide, text="render", command=callback)
		render_button.pack(padx=5)

		leftSide.pack(side=tk.LEFT)
		rightSide.pack(side=tk.RIGHT)


	@staticmethod
	def setLighthing(light_type):
		if light_type == "Flat":
			gl.ShadingModel = 0
		elif light_type == "Gouraud":
			gl.ShadingModel = 2
		elif light_type == "Phong":
			gl.ShadingModel = 2


	# Take values from sliders and set them as atributes of controller objects
	def buildRenderData(self):
		self.setLighthing(self.actual_lighting.get())
		light = LightData(self.x_light_bar.get(), self.y_light_bar.get(), self.z_light_bar.get(), self.intensity_light_bar.get())
		camera = CameraData(self.x_camera_bar.get(), self.y_camera_bar.get(), self.z_camera_bar.get(), self.rotation_camera_bar.get())
		figure = FigureData(self.actual_figure.get(), self.x_figure_bar.get(), self.y_figure_bar.get(), self.z_figure_bar.get(), self.scale_figure_bar.get(), self.rotation_figure_bar.get())

		return light, camera, figure


	@staticmethod
	def drawCanvas(light_data, camera_data, figure_data):
		canvas = Image.new("RGB", (601, 601), (255, 255, 255))
		depth_buffer = np.zeros( canvas.size[0] * canvas.size[1])

		vertices = gl.vertices
		triangles = gl.triangles

		if figure_data.type == "Cube":
			cube = gl.Model(vertices, triangles, gl.Vertex(0, 0, 0), math.sqrt(3))
			instance = gl.Instance(cube, gl.Vertex(figure_data.x, figure_data.y, figure_data.z), gl.MakeOYRotationMatrix(figure_data.rotation), figure_data.scale)
		else:
			sphere = gl.GenerateSphere(25, gl.GREEN)
			instance = gl.Instance(sphere, gl.Vertex(figure_data.x, figure_data.y, figure_data.z), gl.MakeOYRotationMatrix(figure_data.rotation), figure_data.scale)

		instances = [
			instance
		]
		camera = gl.Camera(gl.Vertex(camera_data.x, camera_data.y, camera_data.z), gl.MakeOYRotationMatrix(camera_data.rotation))

		s2 = math.sqrt(2)
		camera.clipping_planes = [
			gl.Plane(gl.Vertex(    0,     0,    1), -1), # Near
			gl.Plane(gl.Vertex( s2,     0, s2),    0), # Left
			gl.Plane(gl.Vertex(-s2,     0, s2),    0), # Right
			gl.Plane(gl.Vertex(    0, -s2, s2),    0), # Top
			gl.Plane(gl.Vertex(    0,    s2, s2),    0), # Bottom
		]

		lights = [
			gl.Light(gl.LT_AMBIENT, 0.2),
			gl.Light(gl.LT_DIRECTIONAL, 0.2, gl.Vertex(-1, 0, 1)),
			gl.Light(gl.LT_POINT, light_data.intensity/100, gl.Vertex(light_data.x, light_data.y, light_data.z))
		]

		gl.RenderScene(canvas, depth_buffer, camera, instances, lights)
		print("Rendered")
		return canvas


if __name__ == "__main__":
	app = rootApp()
	app.title("Examen 3")
	app.mainloop()      
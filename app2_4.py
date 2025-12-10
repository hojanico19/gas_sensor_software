# -*- coding: utf-8 -*-
import nidaqmx
import serial
import time
import os
from tabulate import tabulate
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches
import threading
import pyvisa
import serial.tools.list_ports
import sys
from PyThreadKiller import PyThreadKiller
import json

#FOR WINDOW
from tkinter import *
from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox
from tkinter import Checkbutton
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

class CanvasTooltip:
    def __init__(self, canvas, item_id, text):
        self.canvas = canvas
        self.item_id = item_id
        self.text = text
        self.tooltip_window = None

        self.canvas.tag_bind(self.item_id, '<Enter>', self.show_tooltip)
        self.canvas.tag_bind(self.item_id, '<Leave>', self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return

        # Calculate tooltip position relative to mouse cursor
        x, y = self.canvas.winfo_pointerx(), self.canvas.winfo_pointery()
        
        self.tooltip_window = Toplevel(self.canvas)
        self.tooltip_window.wm_overrideredirect(True) # Remove window decorations
        self.tooltip_window.wm_geometry(f"+{x+10}+{y+10}") # Offset from cursor

        label = Label(self.tooltip_window, text=self.text, background="lightyellow",
                         relief="solid", borderwidth=1, font=(self.font, self.size_1))
        label.pack(padx=1, pady=1)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class App():
    def __init__ (self):
        #95.6
        #Lectura del archivo de configuracion
        with open(resource_path('config.json'), 'r') as file:
            self.data_json = json.load(file)

        #LEER LO QUE HAY EN EL JSON DE CALEFACTORES
        with open(resource_path('calefactores.json'),'r') as file_cal:
            self.dict_calefactores = json.load(file_cal)
        
        self.data_tiempo = [0]
        self.data_r1 = [0]
        self.data_r2 = [0]
        self.data_r3 = [0]
        self.data_r1_ni = [0]
        self.data_r2_ni = [0]
        self.data_r3_ni = [0]
        self.data_gas = [0]
        self.update()
        self.size_1 = 12
        self.size_2 = 14
        self.font= 'Segoe UI'

                #INICIO DE SERIALS
        self.ino_control = serial.Serial(port=self.port_control, baudrate=9600)
        self.ino_control.flushInput()
        self.ino_pwm = serial.Serial(port=self.port_pwm, baudrate=9600)
        self.ino_pwm.flushInput()

        self.root = Tk()
        self.root.title( "LABMAM GAS SENSOR V2.4" )
        self.root.update_idletasks()
        self.root.state('zoomed')
        self.root.iconbitmap(resource_path("icono.ico"))
        #self.root.resizable(False,False)
        #self.root.attributes('-fullscreen', True) 
        #self.root.bind( "<Escape>", closer )

        #MENU
        self.menu=Menu(self.root)
        self.root.config(menu=self.menu)
        self.menuopciones=Menu(self.menu, tearoff=0)
        self.menuopciones.add_command(label="Iniciar", command=self.run_app)
        self.menuopciones.add_command(label="Ejemplo", command=self.salir, state="disabled")
        self.menuopciones.add_separator()
        self.menuopciones.add_command(label="Detener", command=self.detener)
        self.menuopciones.add_separator()
        self.menuopciones.add_command(label="Salir", command=self.salir)

        self.menuconf=Menu(self.menu, tearoff=0)
        self.menuconf.add_command(label="Puertos", command=self.puertos)
        self.menuconf.add_command(label="Equipo", command=self.equipo)
        self.menuconf.add_command(label="Medida", command=self.medida)
        self.menuconf.add_command(label="Placas", command=self.placas)

        self.menuapp=Menu(self.menu, tearoff=0)
        self.menuapp.add_command(label="Calefactores", command=self.calefactores)
        self.menuapp.add_command(label="Graficador", command=self.graficador)

        self.menu.add_cascade(label="Opciones", menu=self.menuopciones, font=(self.font, self.size_1))
        self.menu.add_cascade(label="Configuración", menu=self.menuconf, font=(self.font, self.size_1))
        self.menu.add_cascade(label="Aplicaciones", menu=self.menuapp, font=(self.font, self.size_1))

        #VARIABLES TK
        self.text_file_ino=StringVar()
        self.text_file_ino.set('Escribiendo Archivo: ')
        self.text_file_ni=StringVar()
        self.text_file_ni.set('Escribiendo Archivo: ')

        self.text_slot1 = StringVar()
        self.text_slot1.set('SLOT 1')

        self.text_slot2 = StringVar()
        self.text_slot2.set('SLOT 2')

        self.text_slot3 = StringVar()
        self.text_slot3.set('SLOT 3')

        self.text_empty = StringVar() 

        self.text_rele_s1 = StringVar()
        self.text_rele_s2 = StringVar()
        self.text_rele_s3 = StringVar()

        self.text_volt_s1_ino = StringVar()
        self.text_volt_s2_ino = StringVar()
        self.text_volt_s3_ino = StringVar()

        self.text_volt_s1_ni = StringVar()
        self.text_volt_s2_ni = StringVar()
        self.text_volt_s3_ni = StringVar()

        self.text_res_s1_ino = StringVar()
        self.text_res_s2_ino = StringVar()
        self.text_res_s3_ino = StringVar()

        self.text_res_s1_ni = StringVar()
        self.text_res_s2_ni = StringVar()
        self.text_res_s3_ni = StringVar()

        self.text_curr_s1_ino = StringVar()
        self.text_curr_s2_ino = StringVar()
        self.text_curr_s3_ino = StringVar()

        self.text_curr_s1_ni = StringVar()
        self.text_curr_s2_ni = StringVar()
        self.text_curr_s3_ni = StringVar()

        self.text_temp_s1 = StringVar()
        self.text_temp_s2 = StringVar()
        self.text_temp_s3 = StringVar()


        self.marco_principal1=Frame(self.root)
        self.marco_principal1.pack(fill='x', expand=True, anchor='n')

        self.marco_principal1.grid_columnconfigure(1, weight=1) 

        self.marco_info=Frame(self.marco_principal1)
        self.marco_info.grid(column=1, row=0, sticky='nwes')

        self.marco_sup=Frame(self.marco_principal1)
        self.marco_sup.grid(column=1, row=1, sticky='nwes', pady=6)

        self.marco_sup.grid_columnconfigure(19, weight=1) 

        self.general_separator = ttk.Separator(self.marco_principal1, orient='horizontal')
        self.general_separator.grid(column=1, row=2, columnspan=19, sticky='nwes') # fill 'x' to expand horizontally

        self.canvas_state = Canvas(self.marco_info, width=250, height=60, highlightthickness=0)
        self.canvas_state.grid(row=0, column=0, sticky="w", padx=5)
        self.rec_state = self.create_rounded_rectangle(self.canvas_state, 10, 10, 240, 50, 1, fill="lightblue", outline="black")
        self.wid_state=self.canvas_state.create_text(120, 30, text="Estado: Standby", fill="black", font=(self.font, self.size_2,'bold'), tag='state_off')

        self.canvas_id = Canvas(self.marco_info, width=250, height=60, highlightthickness=0)
        self.canvas_id.grid(row=0, column=1, sticky="w", padx=5)
        self.rec_id = self.create_rounded_rectangle(self.canvas_id, 10, 10, 240, 50, 1, fill="lightblue", outline="black")
        self.wid_id=self.canvas_id.create_text(120, 30, text="ID: ", fill="black", font=(self.font, self.size_2,'bold'), tag='id_off')

        self.canvas_tiempo = Canvas(self.marco_info, width=250, height=60, highlightthickness=0)
        self.canvas_tiempo.grid(row=0, column=2, sticky="w", padx=5)
        self.rec_tiempo = self.create_rounded_rectangle(self.canvas_tiempo, 10, 10, 240, 50, 1, fill="lightblue", outline="black")
        self.wid_tiempo=self.canvas_tiempo.create_text(120, 30, text="Tiempo: ", fill="black", font=(self.font, self.size_2,'bold'), tag='tiempo_off')

        self.canvas_aire = Canvas(self.marco_info, width=250, height=60, highlightthickness=0)
        self.canvas_aire.grid(row=0, column=3, sticky="w", padx=5)
        self.rec_aire = self.create_rounded_rectangle(self.canvas_aire, 10, 10, 240, 50, 1, fill="lightblue", outline="black")
        self.wid_aire=self.canvas_aire.create_text(120, 30, text="Aire: ", fill="black", font=(self.font, self.size_2,'bold'), tag='aire_off')
        self.tooltip_aire = CanvasTooltip(self.canvas_aire, "aire_on", "Valor No es igual al seteado")

        self.canvas_gas = Canvas(self.marco_info, width=250, height=60, highlightthickness=0)
        self.canvas_gas.grid(row=0, column=4, sticky="w", padx=5)
        self.rec_gas = self.create_rounded_rectangle(self.canvas_gas, 10, 10, 240, 50, 1, fill="lightblue", outline="black")
        self.wid_gas=self.canvas_gas.create_text(120, 30, text="Gas: ", fill="black", font=(self.font, self.size_2,'bold'), tag='gas_off')
        self.tooltip_gas = CanvasTooltip(self.canvas_gas, "gas_on", "Valor No es igual al seteado")    

        self.canvas_ppm = Canvas(self.marco_info, width=250, height=60, highlightthickness=0)
        self.canvas_ppm.grid(row=0, column=5, sticky="w", padx=5)
        self.rec_ppm = self.create_rounded_rectangle(self.canvas_ppm, 10, 10, 240, 50, 1, fill="lightblue", outline="black")
        self.wid_ppm=self.canvas_ppm.create_text(120, 30, text="Gas: ", fill="black", font=(self.font, self.size_2,'bold'), tag='ppm_off')     

        self.label_slot1 = Label(self.marco_sup, textvariable=self.text_slot1, justify="left", font=(self.font, self.size_1,'bold'), width=15)
        self.label_slot1.grid(row=1, column=0, sticky="ewns", padx=5)
        self.label_slot2 = Label(self.marco_sup, textvariable=self.text_slot2, justify="left", font=(self.font, self.size_1,'bold'), width=15)
        self.label_slot2.grid(row=2, column=0, sticky="ewns", padx=5)
        self.label_slot3 = Label(self.marco_sup, textvariable=self.text_slot3, justify="left", font=(self.font, self.size_1,'bold'), width=15)
        self.label_slot3.grid(row=3, column=0, sticky="ewns", padx=5)

        self.label_rele = Label(self.marco_sup, text='RELE', justify="left", font=(self.font, self.size_1,'bold'), width=15, bg='gray73')
        self.label_rele.grid(row=0, column=1, sticky="ewns")

        self.label_rele_s1 = Label(self.marco_sup, textvariable=self.text_rele_s1, justify="left", width=15, bg='gray73', font=(self.font, self.size_1))
        self.label_rele_s1.grid(row=1, column=1, sticky="ewns")
        self.label_rele_s2 = Label(self.marco_sup, textvariable=self.text_rele_s2, justify="left", width=15, bg='gray73', font=(self.font, self.size_1))
        self.label_rele_s2.grid(row=2, column=1, sticky="ewns")
        self.label_rele_s3 = Label(self.marco_sup, textvariable=self.text_rele_s3, justify="left", width=15, bg='gray73', font=(self.font, self.size_1))
        self.label_rele_s3.grid(row=3, column=1, sticky="ewns")

        self.label_volt_ino = Label(self.marco_sup, text='V(INO) [V]', justify="left", font=(self.font, self.size_1,'bold'), width=15, bg='gray88')
        self.label_volt_ino.grid(row=0, column=2, sticky="ewns")

        self.label_volt_s1_ino = Label(self.marco_sup, textvariable=self.text_volt_s1_ino, justify="left", width=15, bg='gray88', font=(self.font, self.size_1))
        self.label_volt_s1_ino.grid(row=1, column=2, sticky="ewns")
        self.label_volt_s2_ino = Label(self.marco_sup, textvariable=self.text_volt_s2_ino, justify="left", width=15, bg='gray88', font=(self.font, self.size_1))
        self.label_volt_s2_ino.grid(row=2, column=2, sticky="ewns")
        self.label_volt_s3_ino = Label(self.marco_sup, textvariable=self.text_volt_s3_ino, justify="left", width=15, bg='gray88', font=(self.font, self.size_1))
        self.label_volt_s3_ino.grid(row=3, column=2, sticky="ewns")

        self.label_volt_ni = Label(self.marco_sup, text='V(NI) [V]', justify="left", font=(self.font, self.size_1,'bold'), width=15, bg='gray73')
        self.label_volt_ni.grid(row=0, column=3, sticky="ewns")

        self.label_volt_s1_ni = Label(self.marco_sup, textvariable=self.text_volt_s1_ni, justify="left", width=15, bg='gray73', font=(self.font, self.size_1))
        self.label_volt_s1_ni.grid(row=1, column=3, sticky="ewns")
        self.label_volt_s2_ni = Label(self.marco_sup, textvariable=self.text_volt_s2_ni, justify="left", width=15, bg='gray73', font=(self.font, self.size_1))
        self.label_volt_s2_ni.grid(row=2, column=3, sticky="ewns")
        self.label_volt_s3_ni = Label(self.marco_sup, textvariable=self.text_volt_s3_ni, justify="left", width=15, bg='gray73', font=(self.font, self.size_1))
        self.label_volt_s3_ni.grid(row=3, column=3, sticky="ewns")

        self.label_res_ino = Label(self.marco_sup, text='R(INO) [k\u03A9]', justify="left", font=(self.font, self.size_1,'bold'), width=15, bg='gray88')
        self.label_res_ino.grid(row=0, column=4, sticky="ewns")

        self.label_res_s1_ino = Label(self.marco_sup, textvariable=self.text_res_s1_ino, justify="left", width=15, bg='gray88', font=(self.font, self.size_1))
        self.label_res_s1_ino.grid(row=1, column=4, sticky="ewns")
        self.label_res_s2_ino = Label(self.marco_sup, textvariable=self.text_res_s2_ino, justify="left", width=15, bg='gray88', font=(self.font, self.size_1))
        self.label_res_s2_ino.grid(row=2, column=4, sticky="ewns")
        self.label_res_s3_ino = Label(self.marco_sup, textvariable=self.text_res_s3_ino, justify="left", width=15, bg='gray88', font=(self.font, self.size_1))
        self.label_res_s3_ino.grid(row=3, column=4, sticky="ewns")

        self.label_res_ni = Label(self.marco_sup, text='R(NI) [k\u03A9]', justify="left", font=(self.font, self.size_1,'bold'), width=15, bg='gray73')
        self.label_res_ni.grid(row=0, column=5, sticky="ewns")

        self.label_res_s1_ni = Label(self.marco_sup, textvariable=self.text_res_s1_ni, justify="left", width=15, bg='gray73', font=(self.font, self.size_1))
        self.label_res_s1_ni.grid(row=1, column=5, sticky="ewns")
        self.label_res_s2_ni = Label(self.marco_sup, textvariable=self.text_res_s2_ni, justify="left", width=15, bg='gray73', font=(self.font, self.size_1))
        self.label_res_s2_ni.grid(row=2, column=5, sticky="ewns")
        self.label_res_s3_ni = Label(self.marco_sup, textvariable=self.text_res_s3_ni, justify="left", width=15, bg='gray73', font=(self.font, self.size_1))
        self.label_res_s3_ni.grid(row=3, column=5, sticky="ewns")

        self.label_curr_ino = Label(self.marco_sup, text='I(INO) [mA]', justify="left", font=(self.font, self.size_1,'bold'), width=15, bg='gray88')
        self.label_curr_ino.grid(row=0, column=6, sticky="ewns")

        self.label_curr_s1_ino = Label(self.marco_sup, textvariable=self.text_curr_s1_ino, justify="left", width=15, bg='gray88', font=(self.font, self.size_1))
        self.label_curr_s1_ino.grid(row=1, column=6, sticky="ewns")
        self.label_curr_s2_ino = Label(self.marco_sup, textvariable=self.text_curr_s2_ino, justify="left", width=15, bg='gray88', font=(self.font, self.size_1))
        self.label_curr_s2_ino.grid(row=2, column=6, sticky="ewns")
        self.label_curr_s3_ino = Label(self.marco_sup, textvariable=self.text_curr_s3_ino, justify="left", width=15, bg='gray88', font=(self.font, self.size_1))
        self.label_curr_s3_ino.grid(row=3, column=6, sticky="ewns")

        self.label_curr_ni = Label(self.marco_sup, text='I(NI) [mA]', justify="left", font=(self.font, self.size_1,'bold'), width=15, bg='gray73')
        self.label_curr_ni.grid(row=0, column=7, sticky="ewns")

        self.label_curr_s1_ni = Label(self.marco_sup, textvariable=self.text_curr_s1_ni, justify="left", width=15, bg='gray73', font=(self.font, self.size_1))
        self.label_curr_s1_ni.grid(row=1, column=7, sticky="ewns")
        self.label_curr_s2_ni = Label(self.marco_sup, textvariable=self.text_curr_s2_ni, justify="left", width=15, bg='gray73', font=(self.font, self.size_1))
        self.label_curr_s2_ni.grid(row=2, column=7, sticky="ewns")
        self.label_curr_s3_ni = Label(self.marco_sup, textvariable=self.text_curr_s3_ni, justify="left", width=15, bg='gray73', font=(self.font, self.size_1))
        self.label_curr_s3_ni.grid(row=3, column=7, sticky="ewns")

        self.label_temp = Label(self.marco_sup, text='TEMP [°C]', justify="left", font=(self.font, self.size_1,'bold'), width=15, bg='gray88')
        self.label_temp.grid(row=0, column=8, sticky="ewns")

        self.label_temp_s1 = Label(self.marco_sup, textvariable=self.text_temp_s1, justify="left", width=15, bg='gray88', font=(self.font, self.size_1))
        self.label_temp_s1.grid(row=1, column=8, sticky="ewns")
        self.label_temp_s2 = Label(self.marco_sup, textvariable=self.text_temp_s2, justify="left", width=15, bg='gray88', font=(self.font, self.size_1))
        self.label_temp_s2.grid(row=2, column=8, sticky="ewns")
        self.label_temp_s3 = Label(self.marco_sup, textvariable=self.text_temp_s3, justify="left", width=15, bg='gray88', font=(self.font, self.size_1))
        self.label_temp_s3.grid(row=3, column=8, sticky="ewns")

        ##SECCION GRAFICO

        self.marco_principal1.grid_columnconfigure(1, weight=1)
        self.marco_grafico = Frame(self.marco_principal1)
        self.marco_grafico.grid(column=1, row=3, sticky='ensw')

        #6.4, 4.8
        self.fig1, (self.ax1,self.ax2) = plt.subplots(2, sharex=True, gridspec_kw={'height_ratios': [1, 3]}, figsize=(8, 5.2))
        self.fig2, (self.ax3,self.ax4) = plt.subplots(2, sharex=True, gridspec_kw={'height_ratios': [1, 3]}, figsize=(8, 5.2))
        self.fig1.subplots_adjust(left=0.164)
        self.fig2.subplots_adjust(left=0.164)

        self.line1, = self.ax1.plot([], [], color = 'black') #GAS INO
        self.line5, = self.ax3.plot([], [], color = 'black') #GAS NI (son los mismos por si acaso)
        
        for i in range(len(self.graf_on)):
            if i==0 and self.graf_on[i]==1:
                self.line2, = self.ax2.plot([], [], 'b-') #SLOT 1 INO b
                self.line6, = self.ax4.plot([], [], 'b-') #SLOT 1 NI b
            if i==1 and self.graf_on[i]==1:
                self.line3, = self.ax2.plot([], [], 'r-') #SLOT 2 INO r
                self.line7, = self.ax4.plot([], [], 'r-') #SLOT 2 NI r
            if i==2 and self.graf_on[i]==1:
                self.line4, = self.ax2.plot([], [], 'g-') #SLOT 3 INO g
                self.line8, = self.ax4.plot([], [], 'g-') #SLOT 3 NI g

        self.marco_grafico_1 = Frame(self.marco_grafico, highlightthickness=2, highlightbackground="gray")
        self.marco_grafico_1.grid(column=0, row=0, sticky='w')

        self.marco_grafico_2 = Frame(self.marco_grafico, highlightthickness=2, highlightbackground="gray")
        self.marco_grafico_2.grid(column=1, row=0, sticky='w')

        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self.marco_grafico_1)
        self.canvas1_wid = self.canvas1.get_tk_widget()
        self.canvas1_wid.grid(column=0, row=0)
        #self.canvas1_wid.config(highlightthickness=2)

        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.marco_grafico_2)
        self.canvas2_wid = self.canvas2.get_tk_widget()
        self.canvas2_wid.grid(column=0, row=0)
        #self.canvas2_wid.config(highlightthickness=2)

        s1_patch = mpatches.Patch(color='blue', label='SLOT 1')
        s2_patch = mpatches.Patch(color='red', label='SLOT 2')
        s3_patch = mpatches.Patch(color='green', label='SLOT 3')
        self.ax2.legend(handles=[s1_patch, s2_patch, s3_patch])
        self.ax4.legend(handles=[s1_patch, s2_patch, s3_patch])

        self.ani1 = FuncAnimation(self.fig1, self.graficar_ino, frames=200, interval=5000, blit=False)
        self.ani2 = FuncAnimation(self.fig2, self.graficar_ni, frames=200, interval=5000, blit=False)

        self.frame_tool_1=Frame(self.marco_grafico_1)
        self.frame_tool_1.grid(column=0, row=1, sticky='w')

        self.frame_tool_2=Frame(self.marco_grafico_2)
        self.frame_tool_2.grid(column=0, row=1, sticky='w')

        self.toolbar = NavigationToolbar2Tk(self.canvas1,self.frame_tool_1)
        self.toolbar = NavigationToolbar2Tk(self.canvas2,self.frame_tool_2)
        
        self.marco_grafico.grid_columnconfigure(2, weight=1)
        self.marco_inf=Frame(self.marco_grafico, highlightthickness=2, highlightbackground="gray")
        self.marco_inf.grid(column=2, row=0, sticky='wnes')
        self.marco_inf.grid_columnconfigure(0, weight=1)
        #self.marco_inf.grid_rowconfigure(0, weight=1)

        #self.marco_inf.grid_columnconfigure(0, weight=1) 
        #self.marco_inf.grid_columnconfigure(2, weight=1) 

        self.style = ttk.Style()
        self.style.configure('my.TButton', font=(self.font, self.size_2,'bold'))

        self.BotonIniciar=ttk.Button(self.marco_inf, text="Iniciar", cursor="hand2", command=self.run_app, style='my.TButton')
        self.BotonIniciar.grid(row=0, column=0, sticky="ewns", padx=5, pady=5)

        self.BotonDetener=ttk.Button(self.marco_inf, text="Detener", cursor="hand2", command=self.detener, style='my.TButton')
        self.BotonDetener.grid(row=1, column=0, sticky="ewns", padx=5, pady=5)

        self.BotonSalir=ttk.Button(self.marco_inf, text="Salir", cursor="hand2", command=self.salir, style='my.TButton')
        self.BotonSalir.grid(row=2, column=0, sticky="ewns", padx=5, pady=5)

        self.root.mainloop()

    

    def run_app(self):
        self.kill=0
        self.hilo_app = PyThreadKiller(target=self.app)
        self.hilo_app.start()

    def update(self, a = 0):
        self.max_gas = self.data_json['max_gas']
        self.NI9265_name = self.data_json['NI9265_name']
        self.NI9269_name = self.data_json['NI9269_name']
        self.NI9205_name = self.data_json['NI9205_name']
        self.out_flow = 20 #sccm
        self.port_control = self.data_json['port_control']
        self.port_pwm = self.data_json['port_pwm']
        self.port_source = self.data_json['port_source']
        self.c1_a = self.data_json['calefactor_1'][0]
        self.c1_b = self.data_json['calefactor_1'][1]
        self.c1_c = self.data_json['calefactor_1'][2]
        self.c2_a = self.data_json['calefactor_2'][0]
        self.c2_b = self.data_json['calefactor_2'][1]
        self.c2_c = self.data_json['calefactor_2'][2]
        self.c3_a = self.data_json['calefactor_3'][0]
        self.c3_b = self.data_json['calefactor_3'][1]
        self.c3_c = self.data_json['calefactor_3'][2]
        self.pcb_1 = 0
        self.pcb_2 = 0
        self.pcb_3 = 0
        self.volt = self.data_json['volt']
        self.max_relay = 9.0
        self.min_relay = 0.9
        ##PLAN [PPM GAS, TIEMPO, TEMP] 0 = NO APPLY
        #self.plan_gas = [[0,7200,100],[5,600,100],[0,3600,100],[10,600,100],[0,3600,100],[25,600,100],[0,3600,100],[50,600,100],[0,3600,100],[75,600,100],[0,7200,100]] #PPM;Seconds
        self.plan_gas = self.data_json['plan_gas']
        self.tipo_pcb_1 = self.data_json['tipo_pcb_1'] #opciones: ohm, kilo, mega
        self.tipo_pcb_2 = self.data_json['tipo_pcb_2']
        self.tipo_pcb_3 = self.data_json['tipo_pcb_3']
        #self.resistor = {'ohm': {'Ri': [1, 10.2, 100, 990], 'Ro': 100000, 'Rs': 1}, 'kilo': {'Ri': [1, 10.2, 100, 990], 'Ro': 100000, 'Rs': 10}, 'mega': {'Ri': [1, 10.2, 100, 990], 'Ro': 100000, 'Rs': 217}}
        self.resistor = self.data_json['resistor']
        self.tiempo = 0
        self.flow_1 = 0
        self.flow_2 = 0
        self.flow_3 = 0
        if a==0:
            self.pcb_1 = 0
            self.pcb_2 = 0
            self.pcb_3 = 0
            self.slot_1 = 0
            self.slot_2 = 0
            self.slot_3 = 0
            self.slot_4 = 0
            self.slot_1_ni = 0
            self.slot_2_ni = 0
            self.slot_3_ni = 0
        self.inicio = 1
        self.kill = 0
        self.temp_on = self.data_json['temp_on']
        self.graf_on = self.data_json['graf_on']
        self.current_max = 1
        list_com = list(serial.tools.list_ports.comports())
        self.list_port = []
        pos = 0
        for port, desc, hwid in sorted(list_com):
            self.list_port.append(["{}: {}".format(port, desc),port])


    def app(self):
        #try:
        self.data_tiempo = [0]
        self.data_r1 = [0]
        self.data_r2 = [0]
        self.data_r3 = [0]
        self.data_r1_ni = [0]
        self.data_r2_ni = [0]
        self.data_r3_ni = [0]
        self.data_gas = [0]
        if True:
            #file = input('Ingrese nombre de archivo: ')
            file = filedialog.asksaveasfilename(filetypes=[('Archivo', '*.csv')])

            #ARCHIVO INO
            if 'csv' not in file:
                file_ino =file + '.csv'
            else:
                file_ino = file
            f_ino = open(file_ino, "w")
            f_ino.write('id,time_s,gas_sccm,air_sccm,gas_ppm,pcb_1,pcb_2,pcb_3,volt_1,volt_2,volt_3,r_1,r_2,r_3,i_1,i_2,i_3,temp')
            f_ino.close()

            #ARCHIVO NI
            if 'csv' not in file:
                file_ni =file + '_ni' + '.csv'
            else:
                file_ni = file.split('.csv')[0] + '_ni.csv'
            f_ni = open(file_ni, "w")
            f_ni.write('id,time_s,gas_sccm,air_sccm,gas_ppm,pcb_1,pcb_2,pcb_3,volt_1,volt_2,volt_3,r_1,r_2,r_3,i_1,i_2,i_3,temp')
            f_ni.close()


            self.init_source()
            self.set_source('ON')

            self.canvas_state.itemconfig(self.wid_state, text='Estado: Midiendo...')
            self.canvas_state.itemconfig(self.rec_state, fill="lightgreen")


            id = 0
            self.tiempo = 0
            time_start = time.time()
            plan = time.time()
            iter = 0

            #Inicializacion, uso 5v para iniciar
            self.set_relay(5,5,5)
            self.set_gas(self.plan_gas[iter][0])
            time.sleep(2)

            self.temp_ant = [0,0,0]
            if self.temp_on[0]==1:
                self.text_temp_s1.set(str(self.plan_gas[0][2]))
            else:
                self.text_temp_s1.set('RT')

            if self.temp_on[1]==1:
                self.text_temp_s2.set(str(self.plan_gas[0][2]))
            else:
                self.text_temp_s2.set('RT')
            
            if self.temp_on[2]==1:
                self.text_temp_s3.set(str(self.plan_gas[0][2]))
            else:
                self.text_temp_s3.set('RT')

            #x = threading.Thread(target=self.graficar)
            self.hilo_graficar = PyThreadKiller(target=self.graficar)
            self.hilo_graficar.start()

            # x_ni = threading.Thread(target=self.graficar_ni)
            # x_ni.start()

            self.hilo_v_ni = PyThreadKiller(target=self.get_ni_voltage_mean)
            self.hilo_v_ni.start()
            
            self.set_temperature(self.plan_gas[0][2])
            while True:
                
                line_byte = self.ino_pwm.readline()
                try:
                    line = line_byte.decode()
                except:
                    line=''
                if line!='' and 'A' in line and 'B' in line:
                    part_1 = line.split('A')[1]
                    part_2 = part_1.split('B')[0]
                    if part_2!='':
                        data_str = part_2.split('\t')
                        self.flow_1 = (int(data_str[0])-10000)/1000.0
                        self.flow_2 = (int(data_str[1])-10000)/1000.0
                        self.flow_3 = (int(data_str[2])-10000)/1000.0
                        self.slot_1 = (int(data_str[3])-10000)*2/1000.0
                        self.slot_2 = (int(data_str[5])-10000)*2/1000.0
                        self.slot_3 = (int(data_str[6])-10000)*2/1000.0
                        self.slot_4 = (int(data_str[4])-10000)*2/1000.0

                        #Database
                        id = id + 1
                        self.tiempo = time.time() - time_start
                        data = str(id) + ',' + str(format(self.tiempo, ".2f")) + ','
                        data_ni = str(id) + ',' + str(format(self.tiempo, ".2f")) + ','
                        
                        self.canvas_tiempo.itemconfig(self.wid_tiempo, text='Tiempo: '+str(int(self.tiempo))+' [s]')
                        self.canvas_tiempo.itemconfig(self.rec_tiempo, fill="lightgreen")
                        self.canvas_id.itemconfig(self.wid_id, text='ID: '+str(id))
                        self.canvas_id.itemconfig(self.rec_id, fill="lightgreen")
                        
                        #Data gas
                        data = data + str(self.get_gas_flow('gas',self.flow_1)) + ',' + str(self.get_gas_flow('air',self.flow_3)) + ','
                        data_ni = data_ni + str(self.get_gas_flow('gas',self.flow_1)) + ',' + str(self.get_gas_flow('air',self.flow_3)) + ','
                        [aire_set, gas_set] = self.get_gas_setting(self.plan_gas[iter][0])
                        [aire_get, gas_get] = [self.get_gas_flow('air',self.flow_3), self.get_gas_flow('gas',self.flow_1)]

                        self.canvas_aire.itemconfig(self.wid_aire, text='Aire: ' + str(format(aire_get, ".2f")) + ' [sccm]')
                        if aire_get>(aire_set-1.5) and aire_get<(aire_set+1.5):
                            self.canvas_aire.itemconfig(self.rec_aire, fill="lightgreen")
                            self.canvas_aire.itemconfig(self.wid_aire, tag="aire_off")
                        else: 
                            self.canvas_aire.itemconfig(self.rec_aire, fill="orangered")
                            self.canvas_aire.itemconfig(self.wid_aire, tag="aire_on")

                        self.canvas_gas.itemconfig(self.wid_gas, text='Gas: ' + str(format(gas_get, ".2f"))+ ' [sccm]')
                        self.canvas_ppm.itemconfig(self.wid_gas, text='Gas: ' + str(format(self.plan_gas[iter][0], ".2f"))+ ' [ppm]')
                        if gas_get>(gas_set-1.5) and gas_get<(gas_set+1.5):
                            self.canvas_gas.itemconfig(self.rec_gas, fill="lightgreen")
                            self.canvas_ppm.itemconfig(self.rec_ppm, fill="lightgreen")
                            self.canvas_gas.itemconfig(self.wid_gas, tag="aire_off")
                        else:
                            self.canvas_gas.itemconfig(self.rec_gas, fill="orangered")
                            self.canvas_ppm.itemconfig(self.rec_ppm, fill="orangered")
                            self.canvas_gas.itemconfig(self.wid_gas, tag="aire_on")


                        
                        data = data + str(self.plan_gas[iter][0]) + ',' #PPM
                        data_ni = data_ni + str(self.plan_gas[iter][0]) + ',' #PPM
                        self.gas_now = self.plan_gas[iter][0]

                        #Data rele
                        data = data + str(self.pcb_1) + ',' + str(self.pcb_2) + ',' + str(self.pcb_3) + ','
                        data_ni = data_ni + str(self.pcb_1) + ',' + str(self.pcb_2) + ',' + str(self.pcb_3) + ','

                        data = data + str(self.slot_1) + ',' + str(self.slot_2) + ',' + str(self.slot_3) + ','
                        data_ni = data_ni + str(self.slot_1_ni) + ',' + str(self.slot_2_ni) + ',' + str(self.slot_3_ni) + ','

                        #Data bruta
                        #R in K
                        data = data + str(self.get_resistor(self.pcb_1,self.slot_1,self.tipo_pcb_1)/1000) + ',' + str(self.get_resistor(self.pcb_2,self.slot_2,self.tipo_pcb_2)/1000) + ',' + str(self.get_resistor(self.pcb_3,self.slot_3,self.tipo_pcb_3)/1000) + ','
                        data_ni = data_ni + str(self.get_resistor(self.pcb_1,self.slot_1_ni,self.tipo_pcb_1)/1000) + ',' + str(self.get_resistor(self.pcb_2,self.slot_2_ni,self.tipo_pcb_2)/1000) + ',' + str(self.get_resistor(self.pcb_3,self.slot_3_ni,self.tipo_pcb_3)/1000) + ','

                        data = data + str(self.get_current(self.pcb_1,self.slot_1,self.tipo_pcb_1)) + ',' + str(self.get_current(self.pcb_2,self.slot_2,self.tipo_pcb_2)) + ',' + str(self.get_current(self.pcb_3,self.slot_3,self.tipo_pcb_3)) + ','
                        data_ni = data_ni + str(self.get_current(self.pcb_1,self.slot_1_ni,self.tipo_pcb_1)) + ',' + str(self.get_current(self.pcb_2,self.slot_2_ni,self.tipo_pcb_2)) + ',' + str(self.get_current(self.pcb_3,self.slot_3_ni,self.tipo_pcb_3)) + ','

                        #Data temp
                        data = data + str(self.plan_gas[iter][2])
                        data_ni = data_ni + str(self.plan_gas[iter][2])

                        #Escribir el archivo INO
                        f_ino = open(file_ino, "a")
                        f_ino.write(data+'\n')
                        f_ino.close()

                        #Escribir el archivo NI
                        f_ni = open(file_ni, "a")
                        f_ni.write(data_ni+'\n')
                        f_ni.close()
                        
                        #os.system("cls")
                        self.text_file_ino.set('Escribiendo archivo ' + file_ino)
                        self.text_rele_s1.set(str(self.pcb_1))
                        self.text_rele_s2.set(str(self.pcb_2))
                        self.text_rele_s3.set(str(self.pcb_3))

                        self.text_volt_s1_ino.set('{:.{}g}'.format(self.slot_1, 4))
                        self.text_volt_s2_ino.set('{:.{}g}'.format(self.slot_2, 4))
                        self.text_volt_s3_ino.set('{:.{}g}'.format(self.slot_3, 4))
                        self.text_res_s1_ino.set('{:.{}g}'.format(self.get_resistor(self.pcb_1,self.slot_1,self.tipo_pcb_1)/1000, 6))
                        self.text_res_s2_ino.set('{:.{}g}'.format(self.get_resistor(self.pcb_2,self.slot_2,self.tipo_pcb_2)/1000, 6))
                        self.text_res_s3_ino.set('{:.{}g}'.format(self.get_resistor(self.pcb_3,self.slot_3,self.tipo_pcb_3)/1000, 6))
                        self.text_curr_s1_ino.set('{:.{}g}'.format(self.get_current(self.pcb_1,self.slot_1,self.tipo_pcb_1)*1000, 6))
                        self.text_curr_s2_ino.set('{:.{}g}'.format(self.get_current(self.pcb_2,self.slot_2,self.tipo_pcb_2)*1000, 6))
                        self.text_curr_s3_ino.set('{:.{}g}'.format(self.get_current(self.pcb_3,self.slot_3,self.tipo_pcb_3)*1000, 6))

                        self.text_file_ni.set('Escribiendo archivo ' + file_ni)
                        self.text_volt_s1_ni.set('{:.{}g}'.format(self.slot_1_ni, 4))
                        self.text_volt_s2_ni.set('{:.{}g}'.format(self.slot_2_ni, 4))
                        self.text_volt_s3_ni.set('{:.{}g}'.format(self.slot_3_ni, 4))
                        self.text_res_s1_ni.set('{:.{}g}'.format(self.get_resistor(self.pcb_1,self.slot_1_ni,self.tipo_pcb_1)/1000, 6))
                        self.text_res_s2_ni.set('{:.{}g}'.format(self.get_resistor(self.pcb_2,self.slot_2_ni,self.tipo_pcb_2)/1000, 6))
                        self.text_res_s3_ni.set('{:.{}g}'.format(self.get_resistor(self.pcb_3,self.slot_3_ni,self.tipo_pcb_3)/1000, 6))
                        self.text_curr_s1_ni.set('{:.{}g}'.format(self.get_current(self.pcb_1,self.slot_1_ni,self.tipo_pcb_1)*1000, 6))
                        self.text_curr_s2_ni.set('{:.{}g}'.format(self.get_current(self.pcb_2,self.slot_2_ni,self.tipo_pcb_2)*1000, 6))
                        self.text_curr_s3_ni.set('{:.{}g}'.format(self.get_current(self.pcb_3,self.slot_3_ni,self.tipo_pcb_3)*1000, 6))

                        if self.temp_on[0]==1 and self.plan_gas[iter][2]!=self.temp_ant[0]:
                            self.text_temp_s1.set(str(self.plan_gas[iter][2]))
                            self.temp_ant[0] = self.plan_gas[iter][2]
                        elif self.temp_on[0]==0:
                            self.text_temp_s1.set('RT')

                        if self.temp_on[1]==1 and self.plan_gas[iter][2]!=self.temp_ant[1]:
                            self.text_temp_s2.set(str(self.plan_gas[iter][2]))
                            self.temp_ant[1] = self.plan_gas[iter][2]
                        elif self.temp_on[1]==0:
                            self.text_temp_s2.set('RT')
                        
                        if self.temp_on[2]==1 and self.plan_gas[iter][2]!=self.temp_ant[2]:
                            self.text_temp_s3.set(str(self.plan_gas[iter][2]))
                            self.temp_ant[2] = self.plan_gas[iter][2]
                        elif self.temp_on[2]==0:
                            self.text_temp_s3.set('RT')
                        

                        #Vemos iteracion
                        if (time.time())-plan >= self.plan_gas[iter][1]:
                            iter=iter+1
                            plan = time.time()
                            
                        if iter == len(self.plan_gas):
                            break

                        #Verifica valores para cambio de rele y escribe en ino
                        relay = threading.Thread(target=self.set_relay, args=(self.slot_1_ni,self.slot_2_ni,self.slot_3_ni))
                        relay.start()
                        #self.set_relay(self.slot_1_ni,self.slot_2_ni,self.slot_3_ni)

                        #Escribe gases
                        gas = threading.Thread(target=self.set_gas, args=(self.plan_gas[iter][0],))
                        gas.start()
                        #self.set_gas(self.plan_gas[iter][0])

                        temp = threading.Thread(target=self.set_temperature, args=(self.plan_gas[iter][2],))
                        temp.start()
                        #self.set_temperature(self.plan_gas[iter][2])

                if self.kill == 1:
                    break
                        
            self.set_gas_flow(0)
            self.set_air_flow(0)
            self.set_source('OFF')
            self.ino_control.write('*000000000000*\n'.encode('utf-8'))
            self.ino_pwm.write('*000000000*\n'.encode('utf-8'))
        #except:
            self.set_gas_flow(0)
            self.set_air_flow(0)
            self.ino_control.write('*000000000000*\n'.encode('utf-8'))
            self.ino_pwm.write('*000000000*\n'.encode('utf-8'))
            self.kill = 1
        #plt.show()
            

    def set_gas(self, ppm):
        if ppm > self.max_gas:
            print('Valor de gas supera el maximo, seteando a ' + str(self.max_gas))
            ppm = self.max_gas
        flow_gas = (ppm * self.out_flow) / self.max_gas #sccm
        flow_air = self.out_flow - flow_gas #sccm
        try:
            self.set_gas_flow(flow_gas) 
            self.set_air_flow(flow_air)
        except: pass

    def get_gas_setting(self, ppm):
        if ppm > self.max_gas:
            print('Valor de gas supera el maximo, seteando a ' + str(self.max_gas))
            ppm = self.max_gas
        flow_gas = (ppm * self.out_flow) / self.max_gas #sccm
        flow_air = self.out_flow - flow_gas #sccm
        return [flow_air,flow_gas]

    def set_gas_flow(self, value):
        if value >= 20:
            value = 20
        voltage = (value/20.0) * 5.0 #

        try:
            self.daq.write(f"SOUR:VOLT {voltage}, (@101)")
        except: pass

        #with nidaqmx.Task() as task:
           # task.ao_channels.add_ao_voltage_chan(self.NI9269_name+"/ao0", min_val=-10, max_val=10)
           # task.write(voltage,auto_start=True)

    def set_air_flow(self, value):
        if value >= 50:
            value = 50
        current = ((value*16.0/50.0) + 4.0) / 1000.0  #mA

        try:
            self.daq.write(f"SOUR:CURR {current}, (@103)")
        except: pass
            
       # with nidaqmx.Task() as task:
           # task.ao_channels.add_ao_current_chan(self.NI9265_name+"/ao0", min_val=0, max_val=0.02)
           # task.write(current,auto_start=True)

    def set_relay(self, slot_1, slot_2, slot_3):
        output = '*'

        #SLOT1
        if self.pcb_1 == 0:
            self.pcb_1 = 4
        if slot_1 >= self.max_relay:
            if self.pcb_1 < 4:
                self.pcb_1 = self.pcb_1 + 1
        elif slot_1 < self.min_relay:
            if self.pcb_1 > 1:
                self.pcb_1 = self.pcb_1 - 1
        output = output + self.get_string(self.pcb_1)

        #SLOT2
        if self.pcb_2 == 0:
            self.pcb_2 = 4
        if slot_2 >= self.max_relay:
            if self.pcb_2 < 4:
                self.pcb_2 = self.pcb_2 + 1
        elif slot_2 < self.min_relay:
            if self.pcb_2 > 1:
                self.pcb_2 = self.pcb_2 - 1
        output = output + self.get_string(self.pcb_2)

        #SLOT3
        if self.pcb_3 == 0:
            self.pcb_3 = 4
        if slot_3 >= self.max_relay:
            if self.pcb_3 < 4:
                self.pcb_3 = self.pcb_3 + 1
        elif slot_3 < self.min_relay:
            if self.pcb_3 > 1:
                self.pcb_3 = self.pcb_3 - 1
        output = output + self.get_string(self.pcb_3) + '*\n'

        #ENVIAR STRING
        self.ino_control.write(output.encode('utf-8'))

    def set_temperature(self,temp):
        import math
        send = "*"
        if self.temp_on[0] == 0:
            send = send + "000"
        else:
            a_1 = float(self.data_json['calefactor_1'][0])
            b_1 = float(self.data_json['calefactor_1'][1])
            c_1 = float(self.data_json['calefactor_1'][2])
            pwm_1 = (-b_1 + math.sqrt(b_1*b_1-4*a_1*(c_1-temp))) / (2*a_1) 
            #print(pwm_1)
            send = send + "{:03d}".format(int(pwm_1))
        if self.temp_on[1]== 0:
            send = send + "000"
        else:
            a_2 = float(self.data_json['calefactor_2'][0])
            b_2 = float(self.data_json['calefactor_2'][1])
            c_2 = float(self.data_json['calefactor_2'][2])
            pwm_2 = (-b_2 + math.sqrt(b_2*b_2-4*a_2*(c_2-temp))) / (2*a_2)
            print(pwm_2)
            send = send + "{:03d}".format(int(pwm_2))
        if self.temp_on[2]== 0:
            send = send + "000"
        else:
            a_3 = float(self.data_json['calefactor_3'][0])
            b_3 = float(self.data_json['calefactor_3'][1])
            c_3 = float(self.data_json['calefactor_3'][2])
            pwm_3 = (-b_3 + math.sqrt(b_3*b_3-4*a_3*(c_3-temp))) / (2*a_3)
            #print(pwm_3)
            send = send + "{:03d}".format(int(pwm_3))
        send = send + "*\n"
        self.ino_pwm.write(send.encode("utf-8"))

    def get_gas_flow(self, type, value):
        if type=='gas':
            return (value/5.0)*20
        elif type=='air':
            return (value/5.0)*50
        
    def get_string(self, value):
        if value == 1:
            return '1000'
        elif value == 2:
            return '0100'
        elif value == 3:
            return '0010'
        elif value == 4:
            return '0001'
        
    def read_daq_channels(self, channels):
  
        valores = []
        for ch in channels:
            try:
                # Configura el canal como voltaje DC
                self.daq.write(f"CONF:VOLT:DC (@{ch})")
                self.daq.write("INIT")  # Inicia medición
                val = float(self.daq.query("READ?"))  # Lee valor
                valores.append(val)
            except:
                valores.append(None)  # Si falla, agrega None
        return valores
        
    def get_resistor(self, pcb, value, tipo):
        return value
        
        
        #corriente=self.get_current(pcb, value, tipo)
        #if corriente == 0:
         #   return 100000000
        #else:
         #   resistance = self.volt / corriente
        #return resistance


    def get_current(self, pcb, value, tipo):
        #31.0 es la calibracion
        return value
        #current = ( value * self.resistor[tipo]['Ri'][pcb-1] * 30.25) / float(self.resistor[tipo]['Ro'] * self.resistor[tipo]['Rs'])
        #return current

    def get_ni_voltage_mean(self):
        cont = 0
        data_sum = [0,0,0]
        time.sleep(1)
        inicio = time.time()
        while True:
            with nidaqmx.Task() as task:
                    task.ai_channels.add_ai_voltage_chan(self.NI9205_name+'/ai5', min_val=-10.0, max_val=10.0)
                    task.ai_channels.add_ai_voltage_chan(self.NI9205_name+'/ai6', min_val=-10.0, max_val=10.0)
                    task.ai_channels.add_ai_voltage_chan(self.NI9205_name+'/ai7', min_val=-10.0, max_val=10.0)
                    datos = task.read()
            for i in range(3):
                data_sum[i] = data_sum[i] + datos[i]
            cont = cont + 1
            if (time.time()-inicio) >= 1:
                self.slot_1_ni = data_sum[0] / cont
                self.slot_2_ni = data_sum[1] / cont
                self.slot_3_ni = data_sum[2] / cont
                cont=0 
                data_sum = [0,0,0]
                inicio = time.time()
            if self.kill==1:
                break

    def graficar_ino(self, k):
        self.line1.set_data(self.data_tiempo,self.data_gas)

        for i in range(len(self.graf_on)):
            if i==0 and self.graf_on[i]==1:
                self.line2.set_data(self.data_tiempo,self.data_r1)
            if i==1 and self.graf_on[i]==1:
                self.line3.set_data(self.data_tiempo,self.data_r2)
            if i==2 and self.graf_on[i]==1:
                self.line4.set_data(self.data_tiempo,self.data_r3)

        #MAX AND MIN
        self.ax1.set_xlim(min(self.data_tiempo), max(self.data_tiempo))
        self.ax1.set_ylim(-1, 21)
        self.ax2.set_xlabel("Tiempo (s)")
        self.ax1.set_ylabel("PPM GAS")
        self.ax1.set_title("Gas - ARDUINO")
        self.ax2.set_ylabel("Resistencia (k$\Omega$)")
        self.ax2.set_title("Resistencia de Sensor de Gas - ARDUINO")
        if sum(self.graf_on)==3:
            self.ax2.set_xlim(min(self.data_tiempo), max(self.data_tiempo))
            minimo = min([min(self.data_r1),min(self.data_r2),min(self.data_r3)])
            maximo = max([max(self.data_r1),max(self.data_r2),max(self.data_r3)])
            dif = (maximo - minimo) * 0.02
            self.ax2.set_ylim(minimo - dif, maximo + dif)
            return self.line1, self.line2, self.line3, self.line4
        elif self.graf_on[0]==1 and self.graf_on[1]==1 and self.graf_on[2]!=1:
            self.ax2.set_xlim(min(self.data_tiempo), max(self.data_tiempo))
            minimo = min([min(self.data_r1),min(self.data_r2)])
            maximo = max([max(self.data_r1),max(self.data_r2)])
            dif = (maximo - minimo) * 0.02
            self.ax2.set_ylim(minimo - dif, maximo + dif)
            return self.line1, self.line2, self.line3
        elif self.graf_on[0]==1 and self.graf_on[1]!=1 and self.graf_on[2]==1:
            self.ax2.set_xlim(min(self.data_tiempo), max(self.data_tiempo))
            minimo = min([min(self.data_r1),min(self.data_r3)])
            maximo = max([max(self.data_r1),max(self.data_r3)])
            dif = (maximo - minimo) * 0.02
            self.ax2.set_ylim(minimo - dif, maximo + dif)
            return self.line1, self.line2, self.line4
        elif self.graf_on[0]!=1 and self.graf_on[1]==1 and self.graf_on[2]==1:
            self.ax2.set_xlim(min(self.data_tiempo), max(self.data_tiempo))
            minimo = min([min(self.data_r3),min(self.data_r2)])
            maximo = max([max(self.data_r3),max(self.data_r2)])
            dif = (maximo - minimo) * 0.02
            self.ax2.set_ylim(minimo - dif, maximo + dif)
            return self.line1, self.line3, self.line4
        elif self.graf_on[0]==1 and self.graf_on[1]!=1 and self.graf_on[2]!=1:
            self.ax2.set_xlim(min(self.data_tiempo), max(self.data_tiempo))
            minimo = min(min(self.data_r1))
            maximo = max(max(self.data_r1))
            dif = (maximo - minimo) * 0.02
            self.ax2.set_ylim(minimo - dif, maximo + dif)
            return self.line1, self.line2
        elif self.graf_on[0]!=1 and self.graf_on[1]==1 and self.graf_on[2]!=1:
            self.ax2.set_xlim(min(self.data_tiempo), max(self.data_tiempo))
            minimo = min(min(self.data_r2))
            maximo = max(max(self.data_r2))
            dif = (maximo - minimo) * 0.02
            self.ax2.set_ylim(minimo - dif, maximo + dif)
            return self.line1, self.line3
        else:
            self.ax2.set_xlim(min(self.data_tiempo), max(self.data_tiempo))
            minimo = min(min(self.data_r3))
            maximo = max(max(self.data_r3))
            dif = (maximo - minimo) * 0.02
            self.ax2.set_ylim(minimo - dif, maximo + dif)
            return self.line1, self.line4
        
    def graficar_ni(self, k):
        self.line5.set_data(self.data_tiempo,self.data_gas)

        for i in range(len(self.graf_on)):
            if i==0 and self.graf_on[i]==1:
                self.line6.set_data(self.data_tiempo,self.data_r1_ni)
            if i==1 and self.graf_on[i]==1:
                self.line7.set_data(self.data_tiempo,self.data_r2_ni)
            if i==2 and self.graf_on[i]==1:
                self.line8.set_data(self.data_tiempo,self.data_r3_ni)

        #MAX AND MIN
        self.ax3.set_xlim(min(self.data_tiempo), max(self.data_tiempo))
        self.ax3.set_ylim(-1, 21)
        self.ax4.set_xlabel("Tiempo (s)")
        self.ax3.set_ylabel("PPM GAS")
        self.ax3.set_title("Gas - NATIONAL INSTRUMENTS")
        self.ax4.set_ylabel("Resistencia (k$\Omega$)")
        self.ax4.set_title("Resistencia de Sensor de Gas - NI")
        if sum(self.graf_on)==3:
            self.ax4.set_xlim(min(self.data_tiempo), max(self.data_tiempo))
            minimo = min([min(self.data_r1_ni),min(self.data_r2_ni),min(self.data_r3_ni)])
            maximo = max([max(self.data_r1_ni),max(self.data_r2_ni),max(self.data_r3_ni)])
            dif = (maximo - minimo) * 0.02
            self.ax4.set_ylim(minimo - dif, maximo + dif)
            return self.line5, self.line6, self.line7, self.line8
        elif self.graf_on[0]==1 and self.graf_on[1]==1 and self.graf_on[2]!=1:
            self.ax4.set_xlim(min(self.data_tiempo), max(self.data_tiempo))
            minimo = min([min(self.data_r1_ni),min(self.data_r2_ni)])
            maximo = max([max(self.data_r1_ni),max(self.data_r2_ni)])
            dif = (maximo - minimo) * 0.02
            self.ax4.set_ylim(minimo - dif, maximo + dif)
            return self.line5, self.line6, self.line7
        elif self.graf_on[0]==1 and self.graf_on[1]!=1 and self.graf_on[2]==1:
            self.ax4.set_xlim(min(self.data_tiempo), max(self.data_tiempo))
            minimo = min([min(self.data_r1_ni),min(self.data_r3_ni)])
            maximo = max([max(self.data_r1_ni),max(self.data_r3_ni)])
            dif = (maximo - minimo) * 0.02
            self.ax4.set_ylim(minimo - dif, maximo + dif)
            return self.line5, self.line6, self.line8
        elif self.graf_on[0]!=1 and self.graf_on[1]==1 and self.graf_on[2]==1:
            self.ax4.set_xlim(min(self.data_tiempo), max(self.data_tiempo))
            minimo = min([min(self.data_r3_ni),min(self.data_r2_ni)])
            maximo = max([max(self.data_r3_ni),max(self.data_r2_ni)])
            dif = (maximo - minimo) * 0.02
            self.ax4.set_ylim(minimo - dif, maximo + dif)
            return self.line5, self.line7, self.line8
        elif self.graf_on[0]==1 and self.graf_on[1]!=1 and self.graf_on[2]!=1:
            self.ax4.set_xlim(min(self.data_tiempo), max(self.data_tiempo))
            minimo = min(min(self.data_r1_ni))
            maximo = max(max(self.data_r1_ni))
            dif = (maximo - minimo) * 0.02
            self.ax4.set_ylim(minimo - dif, maximo + dif)
            return self.line5, self.line6
        elif self.graf_on[0]!=1 and self.graf_on[1]==1 and self.graf_on[2]!=1:
            self.ax4.set_xlim(min(self.data_tiempo), max(self.data_tiempo))
            minimo = min(min(self.data_r2_ni))
            maximo = max(max(self.data_r2_ni))
            dif = (maximo - minimo) * 0.02
            self.ax4.set_ylim(minimo - dif, maximo + dif)
            return self.line5, self.line7
        else:
            self.ax4.set_xlim(min(self.data_tiempo), max(self.data_tiempo))
            minimo = min(min(self.data_r3_ni))
            maximo = max(max(self.data_r3_ni))
            dif = (maximo - minimo) * 0.02
            self.ax4.set_ylim(minimo - dif, maximo + dif)
            return self.line5, self.line8

    def graficar(self):
        crono = 0
        while True:
            time.sleep(1)
            crono = crono + 1
            if crono > 50:
                if True:
                    while self.inicio == 1:
                        if self.kill == 1:
                            self.ani1.event_source.stop() # Pause the animation
                            self.ani1.running = False
                            self.ani2.event_source.stop() # Pause the animation
                            self.ani2.running = False
                            break
                        self.data_tiempo.append(self.tiempo)
                        self.data_gas.append(self.gas_now)
                        self.data_r1.append(self.get_resistor(self.pcb_1,self.slot_1,self.tipo_pcb_1)/1000)
                        self.data_r2.append(self.get_resistor(self.pcb_2,self.slot_2,self.tipo_pcb_2)/1000)
                        self.data_r3.append(self.get_resistor(self.pcb_3,self.slot_3,self.tipo_pcb_3)/1000)

                        self.data_r1_ni.append(self.get_resistor(self.pcb_1,self.slot_1_ni,self.tipo_pcb_1)/1000)
                        self.data_r2_ni.append(self.get_resistor(self.pcb_2,self.slot_2_ni,self.tipo_pcb_2)/1000)
                        self.data_r3_ni.append(self.get_resistor(self.pcb_3,self.slot_3_ni,self.tipo_pcb_3)/1000)
                        if crono == 50:
                            del self.data_tiempo[0]
                            del self.data_r1[0]
                            del self.data_r2[0]
                            del self.data_r3[0]
                            del self.data_r1_ino[0]
                            del self.data_r2_ino[0]
                            del self.data_r3_ino[0]
                            del self.data_gas[0]
                        time.sleep(5)
            #except: pass

    def init_source(self):
        #self.rm = pyvisa.ResourceManager()
        #print(self.rm.list_resources())
        #self.source = self.rm.open_resource(self.port_source)
        rm = pyvisa.ResourceManager()
        rm.list_resources()
        daq = rm.open_resource('USB0::0x2A8D::0x8501::MY59014597::INSTR',write_termination= '\n', read_termination='\n')
        daq.timeout = 2000

    #STAT is ON or OFF
    def set_source(self, state):
        text = 'OUTP:STAT ' + state + '\nSOUR:VOLT ' + str(int(self.volt)) + '\nSOUR:CURR ' + str(int(self.current_max))
        self.source.query(text)

    def detener(self):
        self.canvas_state.itemconfig(self.rec_state, fill="lightblue")
        self.canvas_state.itemconfig(self.wid_state, text='Estado: Standby')
        self.canvas_tiempo.itemconfig(self.rec_tiempo, fill="lightblue")
        self.canvas_id.itemconfig(self.rec_id, fill="lightblue")
        self.canvas_tiempo.itemconfig(self.rec_tiempo, fill="lightblue")
        self.canvas_aire.itemconfig(self.rec_aire, fill="lightblue")
        self.canvas_gas.itemconfig(self.rec_gas, fill="lightblue")
        self.canvas_ppm.itemconfig(self.rec_ppm, fill="lightblue")
        self.kill=1
        try:
            self.hilo_graficar.kill()
        except: pass
        try:
            self.hilo_v_ni.kill()
        except: pass

    def salir(self):
        self.kill=1
        try:
            self.hilo_v_ni.kill()
        except: pass
        try:
            self.hilo_graficar.kill()
        except: pass
        time.sleep(1)
        try:
            self.hilo_app.kill()
        except: pass
        sys.exit()

    def puertos(self):
        def aplicar():
            self.data_json['NI9265_name'] = label_entry_9265.get()
            self.data_json['NI9269_name'] = label_entry_9269.get()
            self.data_json['NI9205_name'] = label_entry_9205.get()
            self.data_json['port_source'] = label_entry_source.get()
            self.data_json['port_control'] = lista_simple[combo_control.current()]
            self.data_json['port_pwm'] = lista_simple[combo_pwm.current()]
            with open(resource_path('config.json'), 'w') as file:
                json.dump(self.data_json, file, indent=4)

            self.update(1)

        def salir(directo=0):
            if directo==1:
                child.destroy()
            else:
                resp = messagebox.askyesnocancel(title='Salir', message='¿Desea guardar los cambios?')
                if resp is True:
                    aplicar()
                    salir(1)
                elif resp is False:
                    salir(1)
                else:
                    pass
        
        list_com = list(serial.tools.list_ports.comports())
        self.list_port = []
        lista_comp = []
        lista_simple = []
        for port, desc, hwid in sorted(list_com):
            self.list_port.append(["{}: {}".format(port, desc),port])
            lista_simple.append(port)
            lista_comp.append(desc)
        child = Toplevel( self.root )
        child.transient( self.root )
        child.title( "Configuración de Puertos" )
        child.resizable(False,False)

        child_frame_1=Frame(child)
        child_frame_1.pack(fill='x', expand=True, anchor='n')

        child_frame_2=Frame(child)
        child_frame_2.pack(fill='x', expand=True, anchor='n')

        label_port_NI = Label(child_frame_1, text='Puertos National Instruments & INO', justify="left",font=(self.font, self.size_1,'bold'))
        label_port_NI.grid(column=0, row=0, columnspan = 3, sticky='nwes')

        label_port_9265 = Label(child_frame_1, text='NI9265: ', justify="left", font=(self.font, self.size_1))
        label_port_9265.grid(column=0, row=1, sticky='w')

        label_entry_9265 = Entry(child_frame_1, justify="left", width=35, font=(self.font, self.size_1))
        label_entry_9265.grid(column=1, row=1, sticky='w', padx=(1, 6))
        label_entry_9265.delete(0, END)
        label_entry_9265.insert(0, self.data_json['NI9265_name'])

        label_port_9269 = Label(child_frame_1, text='NI9269: ', justify="left", font=(self.font, self.size_1))
        label_port_9269.grid(column=0, row=2, sticky='w')

        label_entry_9269 = Entry(child_frame_1, justify="left", width=35, font=(self.font, self.size_1))
        label_entry_9269.grid(column=1, row=2, sticky='w', padx=(1, 6))
        label_entry_9269.delete(0, END)
        label_entry_9269.insert(0, self.data_json['NI9269_name'])

        label_port_9205 = Label(child_frame_1, text='NI9205: ', justify="left", font=(self.font, self.size_1))
        label_port_9205.grid(column=0, row=3, sticky='w')

        label_entry_9205 = Entry(child_frame_1, justify="left", width=35, font=(self.font, self.size_1))
        label_entry_9205.grid(column=1, row=3, sticky='w', padx=(1, 6))
        label_entry_9205.delete(0, END)
        label_entry_9205.insert(0, self.data_json['NI9205_name'])

        label_port_source = Label(child_frame_1, text='Fuente: ', justify="left", font=(self.font, self.size_1))
        label_port_source.grid(column=0, row=4, sticky='w')

        label_entry_source = Entry(child_frame_1, justify="left", width=35, font=(self.font, self.size_1))
        label_entry_source.grid(column=1, row=4, sticky='w')
        label_entry_source.delete(0, END)
        label_entry_source.insert(0, self.data_json['port_source'])

        label_port_control = Label(child_frame_1, text='INO Control: ', justify="left", font=(self.font, self.size_1))
        label_port_control.grid(column=0, row=5, sticky='w')

        combo_control = ttk.Combobox(child_frame_1, state='readonly', values=list_com, width=32, font=(self.font, self.size_1))
        combo_control.grid(column=1, row=5, sticky='w', padx=(1, 6))
        control_index = lista_simple.index(self.data_json['port_control'])
        combo_control.current(control_index)

        label_port_pwm = Label(child_frame_1, text='INO PWM: ', justify="left", font=(self.font, self.size_1))
        label_port_pwm.grid(column=0, row=6, sticky='w')

        combo_pwm = ttk.Combobox(child_frame_1, state='readonly', values=list_com, width=32, font=(self.font, self.size_1))
        combo_pwm.grid(column=1, row=6, sticky='w', padx=(1, 6))
        pwm_index = lista_simple.index(self.data_json['port_pwm'])
        combo_pwm.current(pwm_index)

        boton_aplicar=Button(child_frame_2, text="Aplicar", cursor="hand2", padx=5, command=aplicar, font=(self.font, self.size_1))
        boton_aplicar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        boton_salir=Button(child_frame_2, text="Salir", cursor="hand2", padx=5, command=salir, font=(self.font, self.size_1))
        boton_salir.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        #self.root.bind( "<Escape>", closer )

        child.mainloop()

    def equipo(self):
        ##CALEFACTOR, VOLTAJE
        def aplicar():
            self.data_json['calefactor_1'][0] = float(entry_c1_a.get())
            self.data_json['calefactor_1'][1] = float(entry_c1_b.get())
            self.data_json['calefactor_1'][2] = float(entry_c1_c.get())
            self.data_json['calefactor_2'][0] = float(entry_c2_a.get())
            self.data_json['calefactor_2'][1] = float(entry_c2_b.get())
            self.data_json['calefactor_2'][2] = float(entry_c2_c.get())
            self.data_json['calefactor_3'][0] = float(entry_c3_a.get())
            self.data_json['calefactor_3'][1] = float(entry_c3_b.get())
            self.data_json['calefactor_3'][2] = float(entry_c3_c.get())
            self.data_json['volt'] = float(entry_volt.get())
            with open(resource_path('config.json'), 'w') as file:
                json.dump(self.data_json, file, indent=4)
            
            self.update(1)

        def salir(directo=0):
            if directo==1:
                child.destroy()
            else:
                resp = messagebox.askyesnocancel(title='Salir', message='¿Desea guardar los cambios?')
                if resp is True:
                    aplicar()
                    salir(1)
                elif resp is False:
                    salir(1)
                else:
                    pass

        def aplicar_cal_1():
            name = combo_cal_1.get()
            self.data_json['calefactor_1'][0] = self.dict_calefactores[name]['cal'][0]
            self.data_json['calefactor_1'][1] = self.dict_calefactores[name]['cal'][1]
            self.data_json['calefactor_1'][2] = self.dict_calefactores[name]['cal'][2]
            entry_c1_a.delete(0, END)
            entry_c1_a.insert(0, self.data_json['calefactor_1'][0])
            entry_c1_b.delete(0, END)
            entry_c1_b.insert(0, self.data_json['calefactor_1'][1])
            entry_c1_c.delete(0, END)
            entry_c1_c.insert(0, self.data_json['calefactor_1'][2])

        def aplicar_cal_2():
            name = combo_cal_2.get()
            self.data_json['calefactor_2'][0] = self.dict_calefactores[name]['cal'][0]
            self.data_json['calefactor_2'][1] = self.dict_calefactores[name]['cal'][1]
            self.data_json['calefactor_2'][2] = self.dict_calefactores[name]['cal'][2]
            entry_c2_a.delete(0, END)
            entry_c2_a.insert(0, self.data_json['calefactor_2'][0])
            entry_c2_b.delete(0, END)
            entry_c2_b.insert(0, self.data_json['calefactor_2'][1])
            entry_c2_c.delete(0, END)
            entry_c2_c.insert(0, self.data_json['calefactor_2'][2])

        def aplicar_cal_3():
            name = combo_cal_3.get()
            self.data_json['calefactor_3'][0] = self.dict_calefactores[name]['cal'][0]
            self.data_json['calefactor_3'][1] = self.dict_calefactores[name]['cal'][1]
            self.data_json['calefactor_3'][2] = self.dict_calefactores[name]['cal'][2]
            entry_c3_a.delete(0, END)
            entry_c3_a.insert(0, self.data_json['calefactor_3'][0])
            entry_c3_b.delete(0, END)
            entry_c3_b.insert(0, self.data_json['calefactor_3'][1])
            entry_c3_c.delete(0, END)
            entry_c3_c.insert(0, self.data_json['calefactor_3'][2])

        child = Toplevel( self.root )
        child.transient( self.root )
        child.title( "Configuración de Equipo" )
        child.resizable(False,False)

        list_cal = list(self.dict_calefactores.keys())

        child_frame_1=Frame(child)
        child_frame_1.pack(fill='x', expand=True, anchor='n')

        child_frame_2=Frame(child)
        child_frame_2.pack(fill='x', expand=True, anchor='n')

        label_equipo_NI = Label(child_frame_1, text='Configuración del Equipo', justify="left",font=(self.font, self.size_1,'bold'))
        label_equipo_NI.grid(column=0, row=0, columnspan = 3, sticky='nwes')

        label_c1 = Label(child_frame_1, text='Calefactor 1: ', justify="left", font=(self.font, self.size_1))
        label_c1.grid(column=0, row=1, sticky='w')

        label_c1_a = Label(child_frame_1, text='a: ', justify="left", font=(self.font, self.size_1))
        label_c1_a.grid(column=1, row=1, sticky='w')

        entry_c1_a = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_c1_a.grid(column=2, row=1, sticky='w', padx=(1, 6))
        entry_c1_a.delete(0, END)
        entry_c1_a.insert(0, self.data_json['calefactor_1'][0])

        label_c1_b = Label(child_frame_1, text='b: ', justify="left", font=(self.font, self.size_1))
        label_c1_b.grid(column=3, row=1, sticky='w')

        entry_c1_b = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_c1_b.grid(column=4, row=1, sticky='w', padx=(1, 6))
        entry_c1_b.delete(0, END)
        entry_c1_b.insert(0, self.data_json['calefactor_1'][1])

        label_c1_c = Label(child_frame_1, text='c: ', justify="left", font=(self.font, self.size_1))
        label_c1_c.grid(column=5, row=1, sticky='w')

        entry_c1_c = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_c1_c.grid(column=6, row=1, sticky='w', padx=(1, 6))
        entry_c1_c.delete(0, END)
        entry_c1_c.insert(0, self.data_json['calefactor_1'][2])

        combo_cal_1 = ttk.Combobox(child_frame_1, state='readonly', values=list_cal, width=15, font=(self.font, self.size_1))
        combo_cal_1.grid(column=7, row=1, sticky='w', padx=(1, 6))
        #combo_cal.current(0)

        boton_aplicar_cal_1=Button(child_frame_1, text="Aplicar Calefactor", cursor="hand2", padx=5, command=aplicar_cal_1, font=(self.font, 9))
        boton_aplicar_cal_1.grid(row=1, column=8, sticky="ew", padx=5, pady=(2, 1))

        label_c2 = Label(child_frame_1, text='Calefactor 2: ', justify="left", font=(self.font, self.size_1))
        label_c2.grid(column=0, row=2, sticky='w')

        label_c2_a = Label(child_frame_1, text='a: ', justify="left", font=(self.font, self.size_1))
        label_c2_a.grid(column=1, row=2, sticky='w')

        entry_c2_a = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_c2_a.grid(column=2, row=2, sticky='w', padx=(1, 6))
        entry_c2_a.delete(0, END)
        entry_c2_a.insert(0, self.data_json['calefactor_2'][0])

        label_c2_b = Label(child_frame_1, text='b: ', justify="left", font=(self.font, self.size_1))
        label_c2_b.grid(column=3, row=2, sticky='w')

        entry_c2_b = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_c2_b.grid(column=4, row=2, sticky='w', padx=(1, 6))
        entry_c2_b.delete(0, END)
        entry_c2_b.insert(0, self.data_json['calefactor_2'][1])

        label_c2_c = Label(child_frame_1, text='c: ', justify="left", font=(self.font, self.size_1))
        label_c2_c.grid(column=5, row=2, sticky='w')

        entry_c2_c = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_c2_c.grid(column=6, row=2, sticky='w', padx=(1, 6))
        entry_c2_c.delete(0, END)
        entry_c2_c.insert(0, self.data_json['calefactor_2'][2])

        combo_cal_2 = ttk.Combobox(child_frame_1, state='readonly', values=list_cal, width=15, font=(self.font, self.size_1))
        combo_cal_2.grid(column=7, row=2, sticky='w', padx=(1, 6))
        #combo_cal.current(0)

        boton_aplicar_cal_2=Button(child_frame_1, text="Aplicar Calefactor", cursor="hand2", padx=5, command=aplicar_cal_2, font=(self.font, 9))
        boton_aplicar_cal_2.grid(row=2, column=8, sticky="ew", padx=5, pady=(2, 1))

        label_c3 = Label(child_frame_1, text='Calefactor 3: ', justify="left", font=(self.font, self.size_1))
        label_c3.grid(column=0, row=3, sticky='w')

        label_c3_a = Label(child_frame_1, text='a: ', justify="left", font=(self.font, self.size_1))
        label_c3_a.grid(column=1, row=3, sticky='w')

        entry_c3_a = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_c3_a.grid(column=2, row=3, sticky='w', padx=(1, 6))
        entry_c3_a.delete(0, END)
        entry_c3_a.insert(0, self.data_json['calefactor_3'][0])

        label_c3_b = Label(child_frame_1, text='b: ', justify="left", font=(self.font, self.size_1))
        label_c3_b.grid(column=3, row=3, sticky='w')

        entry_c3_b = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_c3_b.grid(column=4, row=3, sticky='w', padx=(1, 6))
        entry_c3_b.delete(0, END)
        entry_c3_b.insert(0, self.data_json['calefactor_3'][1])

        label_c3_c = Label(child_frame_1, text='c: ', justify="left", font=(self.font, self.size_1))
        label_c3_c.grid(column=5, row=3, sticky='w')

        entry_c3_c = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_c3_c.grid(column=6, row=3, sticky='w', padx=(1, 6))
        entry_c3_c.delete(0, END)
        entry_c3_c.insert(0, self.data_json['calefactor_3'][2])

        combo_cal_3 = ttk.Combobox(child_frame_1, state='readonly', values=list_cal, width=15, font=(self.font, self.size_1))
        combo_cal_3.grid(column=7, row=3, sticky='w', padx=(1, 6))
        #combo_cal.current(0)

        boton_aplicar_cal_1=Button(child_frame_1, text="Aplicar Calefactor", cursor="hand2", padx=5, command=aplicar_cal_3, font=(self.font, 9))
        boton_aplicar_cal_1.grid(row=3, column=8, sticky="ew", padx=5, pady=(2, 1))

        label_volt = Label(child_frame_1, text='Voltaje: ', justify="left", font=(self.font, self.size_1))
        label_volt.grid(column=0, row=4, sticky='w')

        entry_volt = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_volt.grid(column=2, row=4, sticky='w', padx=(1, 6))
        entry_volt.delete(0, END)
        entry_volt.insert(0, self.data_json['volt'])

        boton_aplicar=Button(child_frame_2, text="Aplicar", cursor="hand2", padx=5, command=aplicar, font=(self.font, self.size_1))
        boton_aplicar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        boton_salir=Button(child_frame_2, text="Salir", cursor="hand2", padx=5, command=salir, font=(self.font, self.size_1))
        boton_salir.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        child.mainloop()
        


    def medida(self):

        def agregar():
            largo = len(lista_label_ciclos)
            lista_label_ciclos.append(Label(child_frame_1, text='Ciclo ' + str(largo+1)+': ', justify="left", font=(self.font, self.size_1)))
            lista_label_ciclos[largo].grid(column=0, row=11+largo,  sticky='w')

            lista_entry_ciclos_gas.append(Entry(child_frame_1, justify="left", width=10, font=(self.font, self.size_1)))
            lista_entry_ciclos_gas[largo].grid(column=1, row=11+largo, sticky='w', padx=(1, 6))

            lista_entry_ciclos_tiempo.append(Entry(child_frame_1, justify="left", width=10, font=(self.font, self.size_1)))
            lista_entry_ciclos_tiempo[largo].grid(column=2, row=11+largo, sticky='w', padx=(1, 6))

            lista_combo_ciclos_tiempo.append(ttk.Combobox(child_frame_1, state='readonly', values=list_tiempo, width=6, font=(self.font, self.size_1)))
            lista_combo_ciclos_tiempo[largo].grid(column=3, row=11+largo, sticky='w', padx=(1, 6))
            index = list_tiempo.index('seg')
            lista_combo_ciclos_tiempo[largo].current(index)

            lista_entry_ciclos_temp.append(Entry(child_frame_1, justify="left", width=10, font=(self.font, self.size_1)))
            lista_entry_ciclos_temp[largo].grid(column=4, row=11+largo, sticky='w', padx=(1, 6))

        def eliminar():
            lista_label_ciclos[-1].destroy()
            lista_label_ciclos.pop()
            lista_entry_ciclos_gas[-1].destroy()
            lista_entry_ciclos_gas.pop()
            lista_entry_ciclos_tiempo[-1].destroy()
            lista_entry_ciclos_tiempo.pop()
            lista_combo_ciclos_tiempo[-1].destroy()
            lista_combo_ciclos_tiempo.pop()
            lista_entry_ciclos_temp[-1].destroy()
            lista_entry_ciclos_temp.pop()

        def tiempo(value):
            if value>=3600 and value%3600==0:
                return [int(value/3600),'hora']
            elif value>=60 and value%60==0:
                return [int(value/60),'min']
            else:
                return [int(value), 'seg']

        def aplicar():
            list_ciclo = []
            for i in range(len(lista_entry_ciclos_gas)):
                #gas tiempo temp
                if lista_combo_ciclos_tiempo[i].get() == 'seg':
                    multiplicador = 1
                elif lista_combo_ciclos_tiempo[i].get() == 'min':
                    multiplicador = 60
                else:
                    multiplicador = 3600
                list_ciclo.append([int(lista_entry_ciclos_gas[i].get()),int(lista_entry_ciclos_tiempo[i].get())*multiplicador,int(lista_entry_ciclos_temp[i].get())])
            self.data_json['plan_gas'] = list_ciclo
            self.data_json['max_gas'] = float(entry_gas.get())
            self.data_json['temp_on'] = [var_temp_1.get(),var_temp_2.get(),var_temp_3.get()]
            self.data_json['graf_on'] = [var_graf_1.get(),var_graf_2.get(),var_graf_3.get()]
            self.data_json['tipo_pcb_1'] = combo_s1.get()
            self.data_json['tipo_pcb_2'] = combo_s2.get()
            self.data_json['tipo_pcb_3'] = combo_s3.get()

            with open(resource_path('config.json'), 'w') as file:
                json.dump(self.data_json, file, indent=4)

            self.update(1)

        def salir(directo=0):
            if directo==1:
                child.destroy()
            else:
                resp = messagebox.askyesnocancel(title='Salir', message='¿Desea guardar los cambios?')
                if resp is True:
                    aplicar()
                    salir(1)
                elif resp is False:
                    salir(1)
                else:
                    pass

        child = Toplevel( self.root )
        child.transient( self.root )
        child.title( "Configuración de Placas" )
        child.resizable(False,False)

        list = ['ohm','kilo','mega']

        var_temp_1 = IntVar()
        var_temp_1.set(self.data_json['temp_on'][0])
        var_temp_2 = IntVar()
        var_temp_2.set(self.data_json['temp_on'][1])
        var_temp_3 = IntVar()
        var_temp_3.set(self.data_json['temp_on'][2])

        var_graf_1 = IntVar()
        var_graf_1.set(self.data_json['graf_on'][0])
        var_graf_2 = IntVar()
        var_graf_2.set(self.data_json['graf_on'][1])
        var_graf_3 = IntVar()
        var_graf_3.set(self.data_json['graf_on'][2])

        child_frame_1=Frame(child)
        child_frame_1.pack(fill='x', expand=True, anchor='n')

        child_frame_2=Frame(child)
        child_frame_2.pack(fill='x', expand=True, anchor='n')

        label_equipo_NI = Label(child_frame_1, text='Configuración del Experimento', justify="left",font=(self.font, self.size_1,'bold'))
        label_equipo_NI.grid(column=0, row=0, columnspan = 6, sticky='nwes')

        label_slot = Label(child_frame_1, text='Configuración de Slots: ', justify="left", font=(self.font, self.size_1))
        label_slot.grid(column=0, row=1, columnspan = 3,  sticky='w')

        label_slot_1= Label(child_frame_1, text='SLOT 1: ', justify="left", font=(self.font, self.size_1))
        label_slot_1.grid(column=0, row=2,  sticky='w')

        check_temp_1 = Checkbutton(child_frame_1, variable=var_temp_1, text='Temperatura', justify='left', onvalue=1, offvalue=0, font=(self.font, self.size_1))
        check_temp_1.grid(column=1, row=2,  sticky='w')

        check_graf_1 = Checkbutton(child_frame_1, variable=var_graf_1, text='Graficar', justify='left', onvalue=1, offvalue=0, font=(self.font, self.size_1))
        check_graf_1.grid(column=2, row=2,  sticky='w')

        combo_s1 = ttk.Combobox(child_frame_1, state='readonly', values=list, width=10, font=(self.font, self.size_1))
        combo_s1.grid(column=3, row=2, sticky='w', padx=(1, 6))
        s1_index = list.index(self.data_json['tipo_pcb_1'])
        combo_s1.current(s1_index)

        label_slot_2= Label(child_frame_1, text='SLOT 2: ', justify="left", font=(self.font, self.size_1))
        label_slot_2.grid(column=0, row=3,  sticky='w')

        check_temp_2 = Checkbutton(child_frame_1, variable=var_temp_2, text='Temperatura', justify='left', onvalue=1, offvalue=0, font=(self.font, self.size_1))
        check_temp_2.grid(column=1, row=3,  sticky='w')

        check_graf_2 = Checkbutton(child_frame_1, variable=var_graf_2, text='Graficar', justify='left', onvalue=1, offvalue=0, font=(self.font, self.size_1))
        check_graf_2.grid(column=2, row=3,  sticky='w')

        combo_s2 = ttk.Combobox(child_frame_1, state='readonly', values=list, width=10, font=(self.font, self.size_1))
        combo_s2.grid(column=3, row=3, sticky='w', padx=(1, 6))
        s2_index = list.index(self.data_json['tipo_pcb_2'])
        combo_s2.current(s2_index)

        label_slot_3= Label(child_frame_1, text='SLOT 3: ', justify="left", font=(self.font, self.size_1))
        label_slot_3.grid(column=0, row=4,  sticky='w')

        check_temp_3 = Checkbutton(child_frame_1, variable=var_temp_3, text='Temperatura', justify='left', onvalue=1, offvalue=0, font=(self.font, self.size_1))
        check_temp_3.grid(column=1, row=4,  sticky='w')

        check_graf_3 = Checkbutton(child_frame_1, variable=var_graf_3, text='Graficar', justify='left', onvalue=1, offvalue=0, font=(self.font, self.size_1))
        check_graf_3.grid(column=2, row=4,  sticky='w')

        combo_s3 = ttk.Combobox(child_frame_1, state='readonly', values=list, width=10, font=(self.font, self.size_1))
        combo_s3.grid(column=3, row=4, sticky='w', padx=(1, 6))
        s3_index = list.index(self.data_json['tipo_pcb_3'])
        combo_s3.current(s3_index)

        separator = ttk.Separator(child_frame_1, orient='horizontal')
        separator.grid(column=0, row=5, columnspan=6, sticky='nwes') # fill 'x' to expand horizontally

        label_gas = Label(child_frame_1, text='Configuración de Gases: ', justify="left", font=(self.font, self.size_1))
        label_gas.grid(column=0, row=6, columnspan = 3,  sticky='w')

        label_ppm = Label(child_frame_1, text='PPM Gas: ', justify="left", font=(self.font, self.size_1))
        label_ppm.grid(column=0, row=7,  sticky='w')

        entry_gas = Entry(child_frame_1, justify="left", width=10, font=(self.font, self.size_1))
        entry_gas.grid(column=1, row=7, sticky='w', padx=(1, 6))
        entry_gas.delete(0, END)
        entry_gas.insert(0, self.data_json['max_gas'])

        separator_2 = ttk.Separator(child_frame_1, orient='horizontal')
        separator_2.grid(column=0, row=8, columnspan=6, sticky='nwes') # fill 'x' to expand horizontally

        label_ciclo = Label(child_frame_1, text='Configuración de Ciclos: ', justify="left", font=(self.font, self.size_1))
        label_ciclo.grid(column=0, row=9, columnspan = 3,  sticky='w')

        label_c_x = Label(child_frame_1, text='', justify="left", font=(self.font, self.size_1))
        label_c_x.grid(column=0, row=10,  sticky='w')

        label_c_g = Label(child_frame_1, text='PPM GAS', justify="left", font=(self.font, self.size_1))
        label_c_g.grid(column=1, row=10,  sticky='w')

        label_c_t = Label(child_frame_1, text='Tiempo', justify="center", font=(self.font, self.size_1))
        label_c_t.grid(column=2, row=10, columnspan=2,  sticky='we')

        label_c_c = Label(child_frame_1, text='Temperatura', justify="left", font=(self.font, self.size_1))
        label_c_c.grid(column=4, row=10,  sticky='w',padx=(1, 6))

        lista_label_ciclos = []
        lista_entry_ciclos_gas = []
        lista_entry_ciclos_tiempo = []
        lista_entry_ciclos_temp = []
        lista_combo_ciclos_tiempo = []

        list_tiempo = ['seg','min','hora']


        for i in range(len(self.data_json['plan_gas'])):
            lista_label_ciclos.append(Label(child_frame_1, text='Ciclo ' + str(i+1)+': ', justify="left", font=(self.font, self.size_1)))
            lista_label_ciclos[i].grid(column=0, row=11+i,  sticky='w')

            lista_entry_ciclos_gas.append(Entry(child_frame_1, justify="left", width=10, font=(self.font, self.size_1)))
            lista_entry_ciclos_gas[i].grid(column=1, row=11+i, sticky='w', padx=(1, 6))
            lista_entry_ciclos_gas[i].delete(0, END)
            lista_entry_ciclos_gas[i].insert(0, self.data_json['plan_gas'][i][0])

            [time, forma] = tiempo(self.data_json['plan_gas'][i][1])

            lista_entry_ciclos_tiempo.append(Entry(child_frame_1, justify="left", width=10, font=(self.font, self.size_1)))
            lista_entry_ciclos_tiempo[i].grid(column=2, row=11+i, sticky='w', padx=(1, 6))
            lista_entry_ciclos_tiempo[i].delete(0, END)
            lista_entry_ciclos_tiempo[i].insert(0, time)

            lista_combo_ciclos_tiempo.append(ttk.Combobox(child_frame_1, state='readonly', values=list_tiempo, width=6, font=(self.font, self.size_1)))
            lista_combo_ciclos_tiempo[i].grid(column=3, row=11+i, sticky='w', padx=(1, 6))
            index = list_tiempo.index(forma)
            lista_combo_ciclos_tiempo[i].current(index)

            lista_entry_ciclos_temp.append(Entry(child_frame_1, justify="left", width=10, font=(self.font, self.size_1)))
            lista_entry_ciclos_temp[i].grid(column=4, row=11+i, sticky='w', padx=(1, 6))
            lista_entry_ciclos_temp[i].delete(0, END)
            lista_entry_ciclos_temp[i].insert(0, self.data_json['plan_gas'][i][2])
        
        boton_agregar=Button(child_frame_2, text="Agregar", cursor="hand2", padx=5, command=agregar, font=(self.font, self.size_1))
        boton_agregar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        boton_eliminar=Button(child_frame_2, text="Eliminar", cursor="hand2", padx=5, command=eliminar, font=(self.font, self.size_1))
        boton_eliminar.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        boton_aplicar=Button(child_frame_2, text="Aplicar", cursor="hand2", padx=5, command=aplicar, font=(self.font, self.size_1))
        boton_aplicar.grid(row=0, column=2, sticky="ew", padx=5, pady=5)

        boton_salir=Button(child_frame_2, text="Salir", cursor="hand2", padx=5, command=salir, font=(self.font, self.size_1))
        boton_salir.grid(row=0, column=3, sticky="ew", padx=5, pady=5)

        child.mainloop()





    def placas(self):
        def aplicar():
            self.data_json['resistor']['ohm']['Ri'][0] = float(entry_ohm_ri_0.get())
            self.data_json['resistor']['ohm']['Ri'][1] = float(entry_ohm_ri_1.get())
            self.data_json['resistor']['ohm']['Ri'][2] = float(entry_ohm_ri_2.get())
            self.data_json['resistor']['ohm']['Ri'][3] = float(entry_ohm_ri_3.get())
            self.data_json['resistor']['ohm']['Ro'] = float(entry_ohm_ro.get())
            self.data_json['resistor']['ohm']['Rs'] = float(entry_ohm_rs.get())
            self.data_json['resistor']['kilo']['Ri'][0] = float(entry_kilo_ri_0.get())
            self.data_json['resistor']['kilo']['Ri'][1] = float(entry_kilo_ri_1.get())
            self.data_json['resistor']['kilo']['Ri'][2] = float(entry_kilo_ri_2.get())
            self.data_json['resistor']['kilo']['Ri'][3] = float(entry_kilo_ri_3.get())
            self.data_json['resistor']['kilo']['Ro'] = float(entry_kilo_ro.get())
            self.data_json['resistor']['kilo']['Rs'] = float(entry_kilo_rs.get())
            self.data_json['resistor']['mega']['Ri'][0] = float(entry_mega_ri_0.get())
            self.data_json['resistor']['mega']['Ri'][1] = float(entry_mega_ri_1.get())
            self.data_json['resistor']['mega']['Ri'][2] = float(entry_mega_ri_2.get())
            self.data_json['resistor']['mega']['Ri'][3] = float(entry_mega_ri_3.get())
            self.data_json['resistor']['mega']['Ro'] = float(entry_mega_ro.get())
            self.data_json['resistor']['mega']['Rs'] = float(entry_mega_rs.get())
            with open(resource_path('config.json'), 'w') as file:
                json.dump(self.data_json, file, indent=4)

            self.update(1)

        def salir(directo=0):
            if directo==1:
                child.destroy()
            else:
                resp = messagebox.askyesnocancel(title='Salir', message='¿Desea guardar los cambios?')
                if resp is True:
                    aplicar()
                    salir(1)
                elif resp is False:
                    salir(1)
                else:
                    pass

        child = Toplevel( self.root )
        child.transient( self.root )
        child.title( "Configuración de Placas" )
        child.resizable(False,False)

        child_frame_1=Frame(child)
        child_frame_1.pack(fill='x', expand=True, anchor='n')

        child_frame_2=Frame(child)
        child_frame_2.pack(fill='x', expand=True, anchor='n')

        label_equipo_NI = Label(child_frame_1, text='Configuración de Placas', justify="left",font=(self.font, self.size_1,'bold'))
        label_equipo_NI.grid(column=0, row=0, columnspan = 6, sticky='nwes')

        label_ohm = Label(child_frame_1, text='Placa OHM: ', justify="left", font=(self.font, self.size_1))
        label_ohm.grid(column=0, row=1, sticky='w')

        label_ohm_ri = Label(child_frame_1, text='Ri: ', justify="left", font=(self.font, self.size_1))
        label_ohm_ri.grid(column=0, row=2, columnspan=2, sticky='w')

        entry_ohm_ri_0 = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_ohm_ri_0.grid(column=2, row=2, sticky='w', padx=(1, 6))
        entry_ohm_ri_0.delete(0, END)
        entry_ohm_ri_0.insert(0, self.data_json['resistor']['ohm']['Ri'][0])

        entry_ohm_ri_1 = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_ohm_ri_1.grid(column=3, row=2, sticky='w', padx=(1, 6))
        entry_ohm_ri_1.delete(0, END)
        entry_ohm_ri_1.insert(0, self.data_json['resistor']['ohm']['Ri'][1])

        entry_ohm_ri_2 = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_ohm_ri_2.grid(column=4, row=2, sticky='w', padx=(1, 6))
        entry_ohm_ri_2.delete(0, END)
        entry_ohm_ri_2.insert(0, self.data_json['resistor']['ohm']['Ri'][2])

        entry_ohm_ri_3 = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_ohm_ri_3.grid(column=5, row=2, sticky='w', padx=(1, 6))
        entry_ohm_ri_3.delete(0, END)
        entry_ohm_ri_3.insert(0, self.data_json['resistor']['ohm']['Ri'][3])

        label_ohm_ro = Label(child_frame_1, text='Ro: ', justify="left", font=(self.font, self.size_1))
        label_ohm_ro.grid(column=0, row=3, columnspan=2, sticky='w')

        entry_ohm_ro = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_ohm_ro.grid(column=2, row=3, sticky='w', padx=(1, 6))
        entry_ohm_ro.delete(0, END)
        entry_ohm_ro.insert(0, self.data_json['resistor']['ohm']['Ro'])

        label_ohm_rs = Label(child_frame_1, text='Rs: ', justify="left", font=(self.font, self.size_1))
        label_ohm_rs.grid(column=0, row=4, columnspan=2, sticky='w')

        entry_ohm_rs = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_ohm_rs.grid(column=2, row=4, sticky='w', padx=(1, 6))
        entry_ohm_rs.delete(0, END)
        entry_ohm_rs.insert(0, self.data_json['resistor']['ohm']['Rs'])

        ###

        label_kilo = Label(child_frame_1, text='Placa KILO: ', justify="left", font=(self.font, self.size_1))
        label_kilo.grid(column=0, row=5, sticky='w')

        label_kilo_ri = Label(child_frame_1, text='Ri: ', justify="left", font=(self.font, self.size_1))
        label_kilo_ri.grid(column=0, row=6, columnspan=2, sticky='w')

        entry_kilo_ri_0 = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_kilo_ri_0.grid(column=2, row=6, sticky='w', padx=(1, 6))
        entry_kilo_ri_0.delete(0, END)
        entry_kilo_ri_0.insert(0, self.data_json['resistor']['kilo']['Ri'][0])

        entry_kilo_ri_1 = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_kilo_ri_1.grid(column=3, row=6, sticky='w', padx=(1, 6))
        entry_kilo_ri_1.delete(0, END)
        entry_kilo_ri_1.insert(0, self.data_json['resistor']['kilo']['Ri'][1])

        entry_kilo_ri_2 = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_kilo_ri_2.grid(column=4, row=6, sticky='w', padx=(1, 6))
        entry_kilo_ri_2.delete(0, END)
        entry_kilo_ri_2.insert(0, self.data_json['resistor']['kilo']['Ri'][2])

        entry_kilo_ri_3 = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_kilo_ri_3.grid(column=5, row=6, sticky='w', padx=(1, 6))
        entry_kilo_ri_3.delete(0, END)
        entry_kilo_ri_3.insert(0, self.data_json['resistor']['kilo']['Ri'][3])

        label_kilo_ro = Label(child_frame_1, text='Ro: ', justify="left", font=(self.font, self.size_1))
        label_kilo_ro.grid(column=0, row=7, columnspan=2, sticky='w')

        entry_kilo_ro = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_kilo_ro.grid(column=2, row=7, sticky='w', padx=(1, 6))
        entry_kilo_ro.delete(0, END)
        entry_kilo_ro.insert(0, self.data_json['resistor']['kilo']['Ro'])

        label_kilo_rs = Label(child_frame_1, text='Rs: ', justify="left", font=(self.font, self.size_1))
        label_kilo_rs.grid(column=0, row=8, columnspan=2, sticky='w')

        entry_kilo_rs = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_kilo_rs.grid(column=2, row=8, sticky='w', padx=(1, 6))
        entry_kilo_rs.delete(0, END)
        entry_kilo_rs.insert(0, self.data_json['resistor']['kilo']['Rs'])

        ###

        label_mega = Label(child_frame_1, text='Placa MEGA: ', justify="left", font=(self.font, self.size_1))
        label_mega.grid(column=0, row=9, sticky='w')

        label_mega_ri = Label(child_frame_1, text='Ri: ', justify="left", font=(self.font, self.size_1))
        label_mega_ri.grid(column=0, row=10, columnspan=2, sticky='w')

        entry_mega_ri_0 = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_mega_ri_0.grid(column=2, row=10, sticky='w', padx=(1, 6))
        entry_mega_ri_0.delete(0, END)
        entry_mega_ri_0.insert(0, self.data_json['resistor']['mega']['Ri'][0])

        entry_mega_ri_1 = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_mega_ri_1.grid(column=3, row=10, sticky='w', padx=(1, 6))
        entry_mega_ri_1.delete(0, END)
        entry_mega_ri_1.insert(0, self.data_json['resistor']['mega']['Ri'][1])

        entry_mega_ri_2 = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_mega_ri_2.grid(column=4, row=10, sticky='w', padx=(1, 6))
        entry_mega_ri_2.delete(0, END)
        entry_mega_ri_2.insert(0, self.data_json['resistor']['mega']['Ri'][2])

        entry_mega_ri_3 = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_mega_ri_3.grid(column=5, row=10, sticky='w', padx=(1, 6))
        entry_mega_ri_3.delete(0, END)
        entry_mega_ri_3.insert(0, self.data_json['resistor']['mega']['Ri'][3])

        label_mega_ro = Label(child_frame_1, text='Ro: ', justify="left", font=(self.font, self.size_1))
        label_mega_ro.grid(column=0, row=11, columnspan=2, sticky='w')

        entry_mega_ro = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_mega_ro.grid(column=2, row=11, sticky='w', padx=(1, 6))
        entry_mega_ro.delete(0, END)
        entry_mega_ro.insert(0, self.data_json['resistor']['mega']['Ro'])

        label_mega_rs = Label(child_frame_1, text='Rs: ', justify="left", font=(self.font, self.size_1))
        label_mega_rs.grid(column=0, row=12, columnspan=2, sticky='w')

        entry_mega_rs = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_mega_rs.grid(column=2, row=12, sticky='w', padx=(1, 6))
        entry_mega_rs.delete(0, END)
        entry_mega_rs.insert(0, self.data_json['resistor']['mega']['Rs'])

        boton_aplicar=Button(child_frame_2, text="Aplicar", cursor="hand2", padx=5, command=aplicar, font=(self.font, self.size_1))
        boton_aplicar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        boton_salir=Button(child_frame_2, text="Salir", cursor="hand2", padx=5, command=salir, font=(self.font, self.size_1))
        boton_salir.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        child.mainloop()

        
    def calefactores(self):
        def aplicar():
            value_str = entry_set_pwm.get()
            try:
                value = int (value_str)
                if value >=0 and value<=255:
                    try:
                        if value <10:
                            value_s = "00" + str(value)
                        elif value <100:
                            value_s = "0" + str(value)
                        else:
                            value_s = str(value)
                        string = "*" + value_s + value_s + value_s + "*\n"
                        
                        self.ino_pwm.write(string.encode("utf-8"))
                    except:
                        pass
                else:
                    messagebox.showerror('Error de Valor', 'Ingrese un valor entero entre 0 y 255')
            except:
                messagebox.showerror('Error de Valor', 'Ingrese un valor entero entre 0 y 255')

        def agregar():
            boton_eliminar['state'] = NORMAL
            largo = len(list_p)
            list_p.append(Label(child_frame_1, text='P' + str(largo+1) + ' :', justify="left", font=(self.font, self.size_1)))
            list_p[largo].grid(column=0, row=6+largo, sticky='w')
            list_entry_pwm.append(Label(child_frame_1, text=entry_set_pwm.get(), justify="left", font=(self.font, self.size_1)))
            list_entry_pwm[largo].grid(column=1, row=6+largo, sticky='w')
            list_entry_temp.append(Label(child_frame_1, text=entry_get_temp.get(), justify="left", font=(self.font, self.size_1)))
            list_entry_temp[largo].grid(column=2, row=6+largo, sticky='w')
            data_pwm.append(float(entry_set_pwm.get()))
            data_temp.append(float(entry_get_temp.get()))
            #print(data_pwm)
            #print(data_temp)
            if len(data_temp)>1:
                minimo = min(data_temp)
                maximo = max(data_temp)
                dif = (maximo - minimo) * 0.02
                ax.set_ylim(minimo - dif, maximo + dif)
            elif len(data_temp_fix)>1:
                minimo = min([min(data_temp),min(data_temp_fix)])
                maximo = max([max(data_temp),max(data_temp_fix)])
                dif = (maximo - minimo) * 0.02
                ax.set_ylim(minimo - dif, maximo + dif)
            else:
                ax.set_ylim(0,1)

            if len(data_pwm)>1:
                minimo = min(data_pwm)
                maximo = max(data_pwm)
                dif = (maximo - minimo) * 0.02
                ax.set_xlim(minimo - dif, maximo + dif)
            elif len(data_pwm_fix)>1:
                minimo = min([min(data_pwm),min(data_pwm_fix)])
                maximo = max([max(data_pwm),max(data_pwm_fix)])
                dif = (maximo - minimo) * 0.02
                ax.set_xlim(minimo - dif, maximo + dif)
            else:
                ax.set_xlim(0,1)

        def eliminar():
            if len(list_p)<=1:
                boton_eliminar['state'] = DISABLED
            if len(list_p)>0:
                list_p[-1].destroy()
                list_p.pop()
                list_entry_pwm[-1].destroy()
                list_entry_pwm.pop()
                list_entry_temp[-1].destroy()
                list_entry_temp.pop()
                try:
                    data_temp.pop()
                    data_pwm.pop()
                except:
                    pass
            if len(data_temp)>1:
                minimo = min(data_temp)
                maximo = max(data_temp)
                dif = (maximo - minimo) * 0.02
                ax.set_ylim(minimo - dif, maximo + dif)
            elif len(data_temp_fix)>1:
                minimo = min([min(data_temp),min(data_temp_fix)])
                maximo = max([max(data_temp),max(data_temp_fix)])
                dif = (maximo - minimo) * 0.02
                ax.set_ylim(minimo - dif, maximo + dif)
            else:
                ax.set_ylim(0,1)

            if len(data_pwm)>1:
                minimo = min(data_pwm)
                maximo = max(data_pwm)
                dif = (maximo - minimo) * 0.02
                ax.set_xlim(minimo - dif, maximo + dif)
            elif len(data_pwm_fix)>1:
                minimo = min([min(data_pwm),min(data_pwm_fix)])
                maximo = max([max(data_pwm),max(data_pwm_fix)])
                dif = (maximo - minimo) * 0.02
                ax.set_xlim(minimo - dif, maximo + dif)
            else:
                ax.set_xlim(0,1)

        def grafico(i):
            line1.set_data(data_pwm, data_temp)
            line2.set_data(data_pwm_fix, data_temp_fix)
            
            #ax.set_xlim(-1,256)
            
            #ax.relim()
            #ax.autoscale_view()
            #canvas.draw()
            return line1, line2
        
        def fit():
            if len(data_pwm)>2:
                cof = ajustar(data_pwm, data_temp)
                entry_a.delete(0, END)
                entry_a.insert(0, str(format(cof[0], ".4f")))
                entry_b.delete(0, END)
                entry_b.insert(0, str(format(cof[1], ".4f")))
                entry_c.delete(0, END)
                entry_c.insert(0, str(format(cof[2], ".4f")))
                arr = np.linspace(min(data_pwm), max(data_pwm), 30)
                arr_y = arr*arr*cof[0] + arr*cof[1] + cof[2]
                try:
                    data_pwm_fix.clear()
                    data_temp_fix.clear()
                except: pass
                
                data_pwm_fix.extend(arr.tolist())
                data_temp_fix.extend(arr_y.tolist())
            else:
                messagebox.showerror('Error de ajuste', 'Se requieren mínimo 3 datos para ajustar')
        
        def ajustar(x,y,g=2):
            import numpy as np
            x_a = np.array(x)
            y_a = np.array(y)
            coe = np.polyfit(x_a, y_a, g)
            list_c = []
            for i in coe:
                if float(i)<10e-8:
                    list_c.append(0)
                else:
                    list_c.append(float(i))
            return list_c
        
        def aplicar_cal():
            value = combo_cal.get()
            if value!="":
                entry_nombre.delete(0, END)
                entry_nombre.insert(0, value)

                resistor = self.dict_calefactores[value]['resistor']
                if resistor>=1000:
                    tipo = 1
                    resistor = resistor/1000
                else:
                    tipo = 0
                combo_res.current(tipo)
                entry_res.delete(0, END)
                entry_res.insert(0, str(resistor))
            
                entry_date.delete(0, END)
                entry_date.insert(0, self.dict_calefactores[value]['date'])

                indice = list_volt.index(self.dict_calefactores[value]['volt'])
                combo_sour.current(indice)

                entry_a.delete(0, END)
                entry_a.insert(0, self.dict_calefactores[value]['cal'][0])

                entry_b.delete(0, END)
                entry_b.insert(0, self.dict_calefactores[value]['cal'][1])

                entry_c.delete(0, END)
                entry_c.insert(0, self.dict_calefactores[value]['cal'][2])

                #RELLENAR PUNTOS
                while len(list_entry_pwm)>=1:
                    list_entry_pwm[-1].destroy()
                    list_entry_pwm.pop()

                while len(list_entry_temp)>=1:
                    list_entry_temp[-1].destroy()
                    list_entry_temp.pop()

                while len(data_pwm)>=1:
                    data_pwm.pop()

                while len(data_temp)>=1:
                    data_temp.pop()

                while len(data_pwm_fix)>=1:
                    data_pwm_fix.pop()

                while len(data_temp_fix)>=1:
                    data_temp_fix.pop()
                
                for i in range(len(self.dict_calefactores[value]['points'][1])):
                    list_entry_pwm.append(Label(child_frame_1, text=self.dict_calefactores[value]['points'][1][i], justify="left", font=(self.font, self.size_1)))
                    list_entry_pwm[i].grid(column=1, row=6+i, sticky='w')
                    list_entry_temp.append(Label(child_frame_1, text=self.dict_calefactores[value]['points'][0][i], justify="left", font=(self.font, self.size_1)))
                    list_entry_temp[i].grid(column=2, row=6+i, sticky='w')
                    list_p.append(Label(child_frame_1, text='P' + str(i+1) + ' :', justify="left", font=(self.font, self.size_1)))
                    list_p[i].grid(column=0, row=6+i, sticky='w')
                    data_pwm.append(self.dict_calefactores[value]['points'][1][i])
                    data_temp.append(self.dict_calefactores[value]['points'][0][i])

                if len(data_temp)>1:
                    minimo = min(data_temp)
                    maximo = max(data_temp)
                    dif = (maximo - minimo) * 0.02
                    ax.set_ylim(minimo - dif, maximo + dif)
                elif len(data_temp_fix)>1:
                    minimo = min([min(data_temp),min(data_temp_fix)])
                    maximo = max([max(data_temp),max(data_temp_fix)])
                    dif = (maximo - minimo) * 0.02
                    ax.set_ylim(minimo - dif, maximo + dif)
                else:
                    ax.set_ylim(0,1)

                if len(data_pwm)>1:
                    minimo = min(data_pwm)
                    maximo = max(data_pwm)
                    dif = (maximo - minimo) * 0.02
                    ax.set_xlim(minimo - dif, maximo + dif)
                elif len(data_pwm_fix)>1:
                    minimo = min([min(data_pwm),min(data_pwm_fix)])
                    maximo = max([max(data_pwm),max(data_pwm_fix)])
                    dif = (maximo - minimo) * 0.02
                    ax.set_xlim(minimo - dif, maximo + dif)
                else:
                    ax.set_xlim(0,1)

                arr = np.linspace(min(data_pwm), max(data_pwm), 30)
                arr_y = arr*arr*self.dict_calefactores[value]['cal'][0] + arr*self.dict_calefactores[value]['cal'][1] + self.dict_calefactores[value]['cal'][2]
                
                data_pwm_fix.extend(arr.tolist())
                data_temp_fix.extend(arr_y.tolist())

        def guardar():
            name_g = entry_nombre.get()
            if name_g=="":
                messagebox.showerror(title="Error", message="Faltan campos por rellenar")
                return
            if entry_res.get()=="":
                messagebox.showerror(title="Error", message="Faltan campos por rellenar")
                return
            resistor_g = float(entry_res.get())
            if combo_res.current()==1:
                resistor_g= resistor_g*1000
            date_g = entry_date.get()
            if date_g=="":
                messagebox.showerror(title="Error", message="Faltan campos por rellenar")
                return
            volt_g = combo_sour.get()
            if volt_g=="":
                messagebox.showerror(title="Error", message="Faltan campos por rellenar")
                return
            cal_a_g = entry_a.get()
            if cal_a_g=="":
                messagebox.showerror(title="Error", message="Faltan campos por rellenar")
                return
            cal_b_g = entry_b.get()
            if cal_b_g=="":
                messagebox.showerror(title="Error", message="Faltan campos por rellenar")
                return
            cal_c_g = entry_c.get()
            if cal_c_g=="":
                messagebox.showerror(title="Error", message="Faltan campos por rellenar")
                return
            
            if name_g in list_cal:
                    answer = messagebox.askyesno("Calefactor ya existe", "Desea reemplazar?")
                    if answer == False:
                        return
            else:
                self.dict_calefactores[name_g]={}

            self.dict_calefactores[name_g]['name']=name_g
            self.dict_calefactores[name_g]['resistor']= resistor_g
            self.dict_calefactores[name_g]['date'] =date_g
            self.dict_calefactores[name_g]['volt']= volt_g
            self.dict_calefactores[name_g]['points']=[data_temp,data_pwm]
            self.dict_calefactores[name_g]['cal']=[float(cal_a_g),float(cal_b_g),float(cal_c_g)]

            try:
                list_cal.clear()
            except: pass
            list_cal.extend(list(self.dict_calefactores.keys()))
            combo_cal['values']=list_cal
                
            with open(resource_path('calefactores.json'),'w') as file_cal:
                json.dump(self.dict_calefactores, file_cal, indent=4)

            messagebox.showinfo("Calefactor guardado", "Calefactor guardado con éxito")        
            


              


        child = Toplevel( self.root )
        child.transient( self.root )
        child.title( "Calibración de Calefactores" )
        child.resizable(False,False)


        list_volt = ['12V','24V','48V']
        list_res = ['\u03A9','k\u03A9']
        list_cal = list(self.dict_calefactores.keys())

        child_frame_1=Frame(child)
        child_frame_1.pack(fill='x', expand=True, anchor='n')

        label_nombre = Label(child_frame_1, text='Nombre: ', justify="left", font=(self.font, self.size_1))
        label_nombre.grid(column=0, row=0, columnspan=2, sticky='w')

        entry_nombre = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_nombre.grid(column=2, row=0, sticky='w', padx=(1, 6))

        combo_cal = ttk.Combobox(child_frame_1, state='readonly', values=list_cal, width=15, font=(self.font, self.size_1))
        combo_cal.grid(column=3, row=0, sticky='w', padx=(1, 6))
        #combo_cal.current(0)

        boton_aplicar_cal=Button(child_frame_1, text="Aplicar Calefactor", cursor="hand2", padx=5, command=aplicar_cal, font=(self.font, 9))
        boton_aplicar_cal.grid(row=0, column=4, sticky="ew", padx=5, pady=(2, 1))

        label_res = Label(child_frame_1, text='Resistencia: ', justify="left", font=(self.font, self.size_1))
        label_res.grid(column=0, row=1, columnspan=2, sticky='w')

        entry_res = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_res.grid(column=2, row=1, sticky='w', padx=(1, 6))

        combo_res = ttk.Combobox(child_frame_1, state='readonly', values=list_res, width=5, font=(self.font, self.size_1))
        combo_res.grid(column=3, row=1, sticky='w', padx=(1, 6))
        combo_res.current(0)

        label_date = Label(child_frame_1, text='Fecha Res: ', justify="left", font=(self.font, self.size_1))
        label_date.grid(column=0, row=2, columnspan=2, sticky='w')

        entry_date = Entry(child_frame_1, justify="left", width=20, font=(self.font, self.size_1))
        entry_date.grid(column=2, row=2, sticky='w', padx=(1, 6))

        label_date_2 = Label(child_frame_1, text='dd/mm/yyyy', justify="left", font=(self.font, self.size_1))
        label_date_2.grid(column=3, row=2, columnspan=2, sticky='w')

        label_sour = Label(child_frame_1, text='Fuente Volt: ', justify="left", font=(self.font, self.size_1))
        label_sour.grid(column=0, row=3, columnspan=2, sticky='w')

        combo_sour = ttk.Combobox(child_frame_1, state='readonly', values=list_volt, width=5, font=(self.font, self.size_1))
        combo_sour.grid(column=2, row=3, sticky='w', padx=(1, 6))
        combo_sour.current(0)

        label_puntos = Label(child_frame_1, text='Puntos: ', justify="left", font=(self.font, self.size_1))
        label_puntos.grid(column=0, row=4, columnspan=2, sticky='w')

        label_pwm = Label(child_frame_1, text='PWM', justify="left", font=(self.font, self.size_1))
        label_pwm.grid(column=1, row=5, sticky='w')
        
        label_temp = Label(child_frame_1, text='TEMP', justify="left", font=(self.font, self.size_1))
        label_temp.grid(column=2, row=5, sticky='w')

        data_temp = []
        data_pwm = []
        data_temp_fix = []
        data_pwm_fix = []
        list_p = []
        list_entry_pwm = []
        list_entry_temp = []

        separator_1 = ttk.Separator(child, orient='horizontal')
        separator_1.pack(fill='x') # fill 'x' to expand horizontally
        
        child_frame_2=Frame(child)
        child_frame_2.pack(fill='x', expand=True, anchor='n')

        label_pwm_2 = Label(child_frame_2, text='PWM: ', justify="left", font=(self.font, self.size_1))
        label_pwm_2.grid(column=0, row=0, sticky='w')

        entry_set_pwm = Entry(child_frame_2, justify="left", width=10, font=(self.font, self.size_1))
        entry_set_pwm.grid(column=1, row=0, sticky='w', padx=(1, 6))

        label_temp_2 = Label(child_frame_2, text='TEMP: ', justify="left", font=(self.font, self.size_1))
        label_temp_2.grid(column=2, row=0, sticky='w')

        entry_get_temp = Entry(child_frame_2, justify="left", width=10, font=(self.font, self.size_1))
        entry_get_temp.grid(column=3, row=0, sticky='w', padx=(1, 6))

        boton_aplicar=Button(child_frame_2, text="Aplicar PWM", cursor="hand2", padx=5, command=aplicar, font=(self.font, self.size_1))
        boton_aplicar.grid(row=0, column=4, sticky="ew", padx=5, pady=5)

        boton_agregar=Button(child_frame_2, text="Agregar Punto", cursor="hand2", padx=5, command=agregar, font=(self.font, self.size_1))
        boton_agregar.grid(row=0, column=5, sticky="ew", padx=5, pady=5)

        boton_eliminar=Button(child_frame_2, text="Eliminar", cursor="hand2", padx=5, command=eliminar, font=(self.font, self.size_1), state=DISABLED)
        boton_eliminar.grid(row=0, column=6, sticky="ew", padx=5, pady=5)

        separator_2 = ttk.Separator(child, orient='horizontal')
        separator_2.pack(fill='x') # fill 'x' to expand horizontally

        child_frame_3=Frame(child)
        child_frame_3.pack(fill='x', expand=True, anchor='n')

        fig = plt.Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.set_xlabel("PWM")
        ax.set_ylabel("Temperatura")
        canvas = FigureCanvasTkAgg(fig, master=child_frame_3)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(side=TOP, fill=BOTH, expand=1)
        line1, = ax.plot([], [], color='blue', marker='o', linestyle='')
        line2, = ax.plot([], [], color='red')

        s1_patch = mpatches.Patch(color='blue', label='Datos')
        s2_patch = mpatches.Patch(color='red', label='Ajuste')
        ax.legend(handles=[s1_patch, s2_patch])
        ax.set_title("Ajuste de Calefactor")

        ani1 = FuncAnimation(fig, grafico, frames=200, interval=1000, blit=False)

        separator_3 = ttk.Separator(child, orient='horizontal')
        separator_3.pack(fill='x') # fill 'x' to expand horizontally

        child_frame_4=Frame(child)
        child_frame_4.pack(fill='x', expand=True, anchor='n')

        label_res = Label(child_frame_4, text='Resultados: ', justify="left", font=(self.font, self.size_1))
        label_res.grid(column=0, row=0, sticky='w')

        label_a = Label(child_frame_4, text='a: ', justify="left", font=(self.font, self.size_1))
        label_a.grid(column=1, row=0, sticky='w')

        entry_a = Entry(child_frame_4, justify="left", width=10, font=(self.font, self.size_1))
        entry_a.grid(column=2, row=0, sticky='w', padx=(1, 6))

        label_b = Label(child_frame_4, text='b: ', justify="left", font=(self.font, self.size_1))
        label_b.grid(column=3, row=0, sticky='w')

        entry_b = Entry(child_frame_4, justify="left", width=10, font=(self.font, self.size_1))
        entry_b.grid(column=4, row=0, sticky='w', padx=(1, 6))

        label_c = Label(child_frame_4, text='c: ', justify="left", font=(self.font, self.size_1))
        label_c.grid(column=5, row=0, sticky='w')

        entry_c = Entry(child_frame_4, justify="left", width=10, font=(self.font, self.size_1))
        entry_c.grid(column=6, row=0, sticky='w', padx=(1, 6))

        boton_ajustar=Button(child_frame_4, text="Ajustar", cursor="hand2", padx=5, command=fit, font=(self.font, self.size_1))
        boton_ajustar.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        boton_guardar=Button(child_frame_4, text="Guardar", cursor="hand2", padx=5, command=guardar, font=(self.font, self.size_1))
        boton_guardar.grid(row=1, column=1,  columnspan=2, sticky="ew", padx=5, pady=5)



        child.mainloop()

    def graficador(self):

        child = Toplevel(self.root)
        child.transient(self.root)
        child.title("Editor de gráfico")
        child.resizable(False, False)

        child_frame_1 = Frame(child)
        child_frame_1.pack(fill='x', expand=True, anchor='n', padx=10, pady=10)

        # Título eje izquierdo
        Label(child_frame_1, text='Título eje Gas:', font=(self.font, self.size_1)).grid(row=0, column=0, sticky='w', padx=5, pady=5)
        entry_titulo_gas = Entry(child_frame_1, width=30, font=(self.font, self.size_1))
        entry_titulo_gas.insert(0, self.ax1.get_title())
        entry_titulo_gas.grid(row=0, column=1, sticky='w', padx=5, pady=5)

        # Título eje derecho
        Label(child_frame_1, text='Título eje Resistencia:', font=(self.font, self.size_1)).grid(row=1, column=0, sticky='w', padx=5, pady=5)
        entry_titulo_res = Entry(child_frame_1, width=30, font=(self.font, self.size_1))
        entry_titulo_res.insert(0, self.ax2.get_title())
        entry_titulo_res.grid(row=1, column=1, sticky='w', padx=5, pady=5)

        # Color línea gas
        Label(child_frame_1, text='Color línea Gas:', font=(self.font, self.size_1)).grid(row=2, column=0, sticky='w', padx=5, pady=5)
        color_var = tk.StringVar(value=self.line1.get_color())

        def elegir_color():
            color = colorchooser.askcolor(title="Seleccionar color")[1]
            if color:
                color_var.set(color)

        Button(child_frame_1, text="Seleccionar color", command=elegir_color, font=(self.font, self.size_1)).grid(row=2, column=1, sticky='w', padx=5, pady=5)

        # Mostrar leyenda
        leyenda_var = tk.BooleanVar(value=(self.ax2.get_legend() is not None))
        Checkbutton(child_frame_1, text='Mostrar leyenda', variable=leyenda_var, font=(self.font, self.size_1)).grid(row=3, column=1, sticky='w', padx=5, pady=5)

        # Botón aplicar
        def aplicar():
            self.ax1.set_title(entry_titulo_gas.get())
            self.ax2.set_title(entry_titulo_res.get())
            self.line1.set_color(color_var.get())

            if leyenda_var.get():
                self.ax2.legend()
            else:
                leg = self.ax2.get_legend()
                if leg:
                    leg.remove()

            self.canvas.draw()
            child.destroy()

        Button(child_frame_1, text="Aplicar", command=aplicar, font=(self.font, self.size_1)).grid(row=4, column=0, columnspan=2, pady=10)


    
   


    def create_rounded_rectangle(self,canvas, x1, y1, x2, y2, radius, **kwargs):
        points = [x1 + radius, y1,
                  x2 - radius, y1,
                  x2, y1 + radius,
                  x2, y2 - radius,
                  x2 - radius, y2,
                  x1 + radius, y2,
                  x1, y2 - radius,
                  x1, y1 + radius]
        return canvas.create_polygon(points, smooth=True, **kwargs)
        
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
        
a=App()
#a.app()
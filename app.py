import datetime
import requests
import json
import pandas
import csv
import subprocess
#import PythonMagick
import os
import glob
import shutil
import zipfile
import numpy

from flask import Flask, render_template, request, redirect, current_app
from bokeh.charts import Line, show, output_file, save, Dot, ColumnDataSource
from bokeh.models import Label,HoverTool,Range1d,TapTool,OpenURL
from bokeh.plotting import figure, show, output_file
from bokeh.layouts import widgetbox,column,row
from bokeh.models.widgets import CheckboxGroup,Slider
from bokeh.models.callbacks import CustomJS

from bokeh.embed import components
from collections import OrderedDict


app = Flask(__name__,static_url_path='/static')
app.debug = True

app.vars=''

@app.route('/')
def main():
  return redirect('/index')

@app.route('/index',methods=['GET','POST'])
def index():
	if request.method == 'GET':
  		return render_template('entry.html')
	else:
		app.vars=request.form['name']
		if len(app.vars)>2:
			f=open('history.txt','a')
			f.write(app.vars)
			f.write("\n")
			f.close()
			return redirect('/trying')
		else:
			return render_template('entry.html')
		
@app.route('/genemap',methods=['GET','POST'])
def genemap():
	return render_template('genemap.html')

@app.route('/trying',methods=['GET','POST'])
def trying():
	##files = glob.glob('.static/OUT/*')
	##print files
	##for f in files:
    	##	os.remove(f)
	gname=app.vars
	
	if os.path.exists('./static/zips/'+app.vars+'.zip'):
		with zipfile.ZipFile("./static/zips/"+app.vars+".zip","r") as zip_ref:
			zip_ref.extractall("./static/OUT/")
		filelink="/static/zips/"+app.vars+".zip"
		pnglist=glob.glob('./static/OUT/*km.png')
		object_list = get_csv()
		script,div=plot_levels()
		return render_template('trying.html', splicing=get_splice(gname), object_list=object_list, filelink=filelink, pnglist=pnglist,gname=gname,script=script, div=div)

	command = 'Rscript'
	path2script = './static/TCGAkm.r'
	args = [app.vars]
	cmd = [command, path2script] + args
	x = subprocess.check_output(cmd, universal_newlines=True)

	#img = PythonMagick.Image()
	#img.density("300")
	pdflist=glob.glob('./static/OUT/*.pdf')
	pnglist=[]
	for item in pdflist:
		#img.read(item)
		#newf=item[:-3]+'png'
		#img.write(newf)
		#pnglist.append(newf)
		os.rename(item,item[:-7]+'_tumor-km.pdf')

	path2script = './static/expr_med.r'
	cmd2 = [command, path2script]
	y=subprocess.check_output(cmd2, universal_newlines=True)

	path2script = './static/mutations.r'
	args = [app.vars]
	cmd3 = [command, path2script] + args
	z=subprocess.check_output(cmd3, universal_newlines=True)

	shutil.make_archive("./static/zips/"+app.vars, 'zip', "./static/OUT/")
	filelink="/static/zips/"+app.vars+".zip"
		
	object_list = get_csv()
	script,div=plot_levels()

	return render_template('trying.html', splicing=get_splice(gname), object_list=object_list, filelink=filelink, pnglist=pnglist, gname=gname,script=script, div=div)

def get_csv():
	p = './static/OUT/final.csv'
	f = open(p, 'r')
	return list(csv.DictReader(f))

def plot_levels():
	#read csv
	levelp='./static/OUT/levels.csv'
	df=pandas.read_csv(levelp,header='infer')
	df=df.replace(numpy.nan,0)
	df["cancers"] = df["tumor_type"] + '_' + df["condition"]
	cancers=list(df["cancers"])
	maxy=max(df["max"])+0.5
	
	#upperscore=list(df.iloc[:,4])
	#lowerscore=list(df.iloc[:,0])
	#q1score=list(df.iloc[:,1])
	#q2score=list(df.iloc[:,2])
	#q3score=list(df.iloc[:,3])
	#cutscore=list(df.iloc[:,5])
	#folds=list(df.iloc[:,5]/df.iloc[:,2])
	
	#zip?
	q2ratio=[]
	for i in range(len(df)):
		q2ratio.append(2**(df["median"][i]-df["median"][i//2*2]))
	minratio=[]
	for i in range(len(df)):
		minratio.append(2**(df["min"][i]-df["min"][i//2*2]))
	maxratio=[]
	for i in range(len(df)):
		maxratio.append(2**(df["max"][i]-df["max"][i//2*2]))
	cutratio=[]
	for i in range(len(df)):
		cutratio.append(2**(df["surv_cutoff"][i]-df["median"][i//2*2]))
	source=ColumnDataSource(
		data=dict(
		cancers=list(df["cancers"]),
		upperscore=list(df.iloc[:,4]),
		lowerscore=list(df.iloc[:,0]),
		q1score=list(df.iloc[:,1]),
		q2score=list(df.iloc[:,2]),
		q3score=list(df.iloc[:,3]),
		cutscore=list(df.iloc[:,5]),
		ratio=q2ratio
		)
	)
	source2=ColumnDataSource(
		data=dict(
		cancers=list(df["cancers"]),
		upperscore=list(df.iloc[:,4]),
		lowerscore=list(df.iloc[:,0]),
		q1score=list(df.iloc[:,1]),
		q2score=list(df.iloc[:,2]),
		q3score=list(df.iloc[:,3]),
		cutscore=list(df.iloc[:,5]),
		ratio=cutratio,
		)
	)
	source3=ColumnDataSource(
		data=dict(
		cancers=list(df["cancers"]),
		upperscore=list(df.iloc[:,4]),
		lowerscore=list(df.iloc[:,0]),
		q1score=list(df.iloc[:,1]),
		q2score=list(df.iloc[:,2]),
		q3score=list(df.iloc[:,3]),
		cutscore=list(df.iloc[:,5]),
		ratio=minratio,
		)
	)
	source4=ColumnDataSource(
		data=dict(
		cancers=list(df["cancers"]),
		upperscore=list(df.iloc[:,4]),
		lowerscore=list(df.iloc[:,0]),
		q1score=list(df.iloc[:,1]),
		q2score=list(df.iloc[:,2]),
		q3score=list(df.iloc[:,3]),
		cutscore=list(df.iloc[:,5]),
		ratio=maxratio,
		)
	)
	
	p = figure(tools=["save","hover",'tap'], background_fill_color="white", title="", x_range=cancers,plot_width=880)
	hover = p.select(dict(type=HoverTool))
	hover.tooltips = [('condition','@cancers'),('ratio/normal','@ratio{1.11}')]
	hover.point_policy='snap_to_data'
	p.segment('cancers', 'upperscore', 'cancers', 'q3score', line_color="black",source=source,legend="max")
	p.segment('cancers', 'lowerscore', 'cancers', 'q1score', line_color="black",source=source,legend="min")
	p.vbar('cancers', 0.35, 'q1score', 'q3score', fill_color=["#9ACD32","#FF4500"]*(len(df)/2), line_color="black",source=source,legend="quartiles")
	p.rect('cancers', 'q2score', 0.35, 0.045, line_color="black",fill_color="black",source=source,legend="median")
	p.rect('cancers', 'cutscore', 0.35, 0.045, line_color=["#FFFFFF","blue"]*(len(df)/2),fill_color="blue",source=source2,legend="cutpoint--link to KM plot",name='cut')
	p.rect('cancers', 'lowerscore', 0.1, 0.023, line_color="black",fill_color="black",source=source3,legend="min")
	p.rect('cancers', 'upperscore', 0.1, 0.023, line_color="black",fill_color="black",source=source4,legend="max")

	p.xgrid.grid_line_color = None
	p.ygrid.grid_line_color = "white"
	p.grid.grid_line_width = 2
	p.xaxis.major_label_text_font_size="12pt"
	p.yaxis.major_label_text_font_size="12pt"
	p.yaxis.axis_label_text_font_size="12pt"
	p.y_range=Range1d(0,maxy)
	p.yaxis.axis_label="RSEM(log2)"
	p.yaxis.axis_label_text_font_style = "normal"
	p.xaxis.major_label_orientation=numpy.pi/4

	p.legend.location = "bottom_left"
	p.legend.click_policy="hide"

	url = "http://0.0.0.0:33507/static/OUT/@cancers"
	url2= url+'-km.pdf'
	taptool = p.select(type=TapTool)
	taptool.names=['cut']
	taptool.callback = OpenURL(url=url2)

	script, div = components(p)
	return script,div

def get_splice(gname):
	with open('./static/TCGA_alt_spl_g.txt','r') as slist:
		rlist=slist.read().split('\n')
		if app.vars in rlist:
			splice="Significant Alternative Splicing"
		else:
			splice="No Significant Alternative Splicing"
		return splice

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=33507)

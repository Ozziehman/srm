import os
from flask import Blueprint, render_template, request, url_for
from .SmartRouteMaker.Facades import SmartRouteMakerFacade as srm
import ast

core = Blueprint('core', __name__,
    static_folder='Static',
    static_url_path='/Core/Static',
    template_folder='Templates')

@core.route('/')
def index():
    return render_template('home.html')

@core.route('/handle_routing', methods=['POST'])
def handle_routing():
    srmf = srm.SmartRouteMakerFacade()

    #pass the form data to the facade
    start = srmf.normalize_coordinates(request.form['start_point'])
    end = srmf.normalize_coordinates(request.form['end_point'])
    #total_elevation_diff = srmf.apply_elevation_param(request.form['total_elevation_diff'])
    


    route = srmf.plan_route(start, end, options={"analyze": True, "surface_dist": True})

    return render_template('result.html', 
        surfaces=route['surface_dist'],
        surfaceDistLegenda=route['surface_dist_legenda'],
        surfaceDistVisualisation=route['surface_dist_visualisation'],
        path_length=route['path_length'],
        elevation_nodes=route['elevation_nodes'],
        routeVisualisation=route['simple_polylines']
    )



@core.route('/handle_circular_routing', methods=['POST'])
def handle_circular_routing():
    srmf = srm.SmartRouteMakerFacade()

    #pass the form data to the facade
    start = srmf.normalize_coordinates(request.form['start_point2'])
    max_length = int(request.form['max_length'])
    try:
        total_elevation_diff = int(request.form['total_elevation_diff'])
    except:
        total_elevation_diff = None
    

    route = srmf.plan_circular_route_flower(start, max_length, elevation_diff_input = total_elevation_diff, options={"analyze": True, "surface_dist": True})
    
    

    return render_template('result.html', 
        surfaces=route['surface_dist'],
        surfaceDistLegenda=route['surface_dist_legenda'],
        surfaceDistVisualisation=route['surface_dist_visualisation'],
        path=route['path'],
        path_length=route['path_length'],
        elevation_diff=route['elevation_diff'],
        routeVisualisation=route['simple_polylines']
    )

@core.route('/export_GPX', methods=['POST'])
def export_GPX():
    node_ids_str = request.form.get('node_ids', '')
    node_ids = ast.literal_eval(node_ids_str)
    srmf = srm.SmartRouteMakerFacade()
    return srmf.export_GPX(node_ids)

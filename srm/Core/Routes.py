import os
from flask import Blueprint, redirect, render_template, request, url_for
from .SmartRouteMaker.Facades import SmartRouteMakerFacade as srm
import ast
import colorama
from termcolor import colored

dir_path = os.path.dirname(os.path.realpath(__file__))

core = Blueprint('core', __name__,
    static_folder=os.path.join(dir_path, 'static'),
    static_url_path='/Core/static',
    template_folder=os.path.join(dir_path, 'templates'))

@core.route('/')
def index():
    return render_template('home.html')

@core.route('/handle_routing', methods=['POST'])
def handle_routing():
    srmf = srm.SmartRouteMakerFacade()

    #pass the form data to the facade
    start = srmf.normalize_coordinates(request.form['start_point'])
    end = srmf.normalize_coordinates(request.form['end_point'])

    try:
        route = srmf.plan_route(start, end, options={"analyze": True, "surface_dist": True})
    except Exception as e:
        print(colored(f"Error in plan_route: {e}, going back to index", "red"))
        return redirect(url_for('core.index'))

    return render_template('result.html', 
        surfaces=route['surface_dist'],
        surfaceDistLegenda=route['surface_dist_legenda'],
        surfaceDistVisualisation=route['surface_dist_visualisation'],
        path=route['path'],
        path_length=route['path_length'],
        elevation_diff=route['elevation_diff'],
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
    
    try:
        hardened_percentage = int(request.form['hardened_percentage'])
    except:
        hardened_percentage = None
    try:
        route = srmf.plan_circular_route_flower(start, max_length, elevation_diff_input = total_elevation_diff, percentage_hard_input = hardened_percentage, options={"analyze": True, "surface_dist": True})
    except Exception as e:
        print(colored(f"Error in plan_circular_route_flower: {e}, going back to index", "red"))
        return redirect(url_for('core.index'))

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

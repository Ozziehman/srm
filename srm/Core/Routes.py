from flask import Blueprint, render_template, request
from .SmartRouteMaker.Facades import SmartRouteMakerFacade as srm

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

    start = srmf.normalize_coordinates(request.form['start_point'])
    end = srmf.normalize_coordinates(request.form['end_point'])

    route = srmf.plan_route(start, end, options={"analyze": True, "surface_dist": True})

    return render_template('result.html', 
        surfaces=route['surface_dist'],
        surfaceDistLegenda=route['surface_dist_legenda'],
        surfaceDistVisualisation=route['surface_dist_visualisation'],
        path_length=route['path_length'],
        routeVisualisation=route['simple_polylines']
    )
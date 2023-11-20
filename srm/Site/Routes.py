from flask import Blueprint

site = Blueprint('Site', __name__,
    static_folder='Static',
    template_folder='Templates')

@site.route('/site')
def siteindex():
    return 'Placeholder site page.'
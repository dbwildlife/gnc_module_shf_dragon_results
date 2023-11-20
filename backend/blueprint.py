from flask import Blueprint, request
from gncitizen.core.observations.models import ObservationModel
from gncitizen.core.taxonomy.models import Taxref
from utils_flask_sqla.response import json_resp
from server import db
from sqlalchemy.sql.expression import func
from .ref_geo.models import LAreas, BibAreasTypes
from geoalchemy2 import func as geo_func

blueprint = Blueprint("results_url", __name__)

default_id_area_type = (
    BibAreasTypes.query.filter(BibAreasTypes.type_code == "REG").first()
).id_type


@blueprint.route("/area_types/list", methods=["GET"])
def get_area_types():
    return [item.as_dict() for item in BibAreasTypes.query.all()]


@blueprint.route("/areas/list", methods=["GET"])
@json_resp
def get_areas():
    id_type = request.args.get("id_type", default=default_id_area_type)
    query = LAreas.query.filter(LAreas.id_type == id_type)
    for item in query.all():
        print(dir(item))
    return [item.as_dict() for item in query.all()]


@blueprint.route("/synthesis", methods=["GET"])
# @json_resp
def get_synthesis():
    col_name = request.args.get("col_name")
    if not col_name:
        return {"message": "Group by column name required"}, 500
    if col_name not in Taxref.__table__.c:
        return {"message": f"col_name available are {Taxref.__table__.c.keys()}"}, 500
    id_program = request.args.get("id_program")
    id_area = request.args.get("id_area")
    query = ObservationModel.query.join(
        Taxref, ObservationModel.cd_nom == Taxref.cd_nom
    )
    print(query)
    if id_area:
        query = query.join(
            LAreas,
            geo_func.ST_Transform(LAreas.geom, 4326).st_intersects(
                ObservationModel.geom
            ),
        ).filter(LAreas.id_area == id_area)
    if id_program:
        query = query.filter(ObservationModel.id_program == id_program)
    query = query.group_by(Taxref.__table__.c[col_name]).values(
        Taxref.__table__.c[col_name].label("group"),
        func.count(ObservationModel.id_program).label("count"),
    )
    return [item._asdict() for item in query]

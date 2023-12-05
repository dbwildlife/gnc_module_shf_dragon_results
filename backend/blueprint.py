import json

from flask import Blueprint, jsonify, render_template, request
from geoalchemy2 import func as geo_func
from geojson import Feature, FeatureCollection
from gncitizen.core.observations.models import ObservationModel
from gncitizen.core.taxonomy.models import Taxref
from server import db
from sqlalchemy.sql.expression import column, distinct, func, select
from utils_flask_sqla.response import json_resp
from utils_flask_sqla_geo.generic import get_geojson_feature

from .ref_geo.models import BibAreasTypes, LAreas

blueprint = Blueprint("results_url", __name__, template_folder="templates")

default_id_area_type = (
    BibAreasTypes.query.filter(BibAreasTypes.type_code == "REG").first()
).id_type


LAREAS_SRID = LAreas.query.first().geom.srid or 2154


@blueprint.route("/", methods=["GET"])
def index():
    return render_template("index.html")


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
    return {
        "type": "FeatureCollection",
        "features": [item.as_geofeature() for item in query.all()],
    }


@blueprint.route("/synthesis/map", methods=["GET"])
def get_map_synthesis():
    cd_nom = request.args.get("cd_nom")
    # is_valid = request.args.get("is_valid", default=default_id_area_type)
    id_program = request.args.get("id_program")
    id_area = request.args.get("id_area")
    id_type = request.args.get("id_type", default=default_id_area_type)
    query = (
        LAreas.query.filter(LAreas.id_type == id_type)
        .outerjoin(
            ObservationModel,
            LAreas.geom.st_intersects(
                geo_func.ST_Transform(ObservationModel.geom, LAREAS_SRID)
            ),
        )
        .outerjoin(Taxref, ObservationModel.cd_nom == Taxref.cd_nom)
        .filter(LAreas.enable)
    )

    if id_program:
        query = query.filter(ObservationModel.id_program == id_program)
    if id_area:
        query = query.filter(LAreas.id_area == id_area)
    if cd_nom:
        query = query.filter(ObservationModel.cd_nom == cd_nom)

    query = query.group_by(LAreas.id_area).values(
        LAreas.id_area,
        LAreas.area_name,
        LAreas.area_code,
        func.count(distinct(ObservationModel.cd_nom)).label("count_taxa"),
        func.count(ObservationModel.id_observation).label("count_occtax"),
        geo_func.st_asgeojson(geo_func.st_transform(LAreas.geom, 4326)).label(
            "geometry"
        ),
    )

    geojson_features = []
    for item in query:
        dict_item = item._asdict()
        geometry = json.loads(dict_item.pop("geometry"))
        id_area = dict_item.pop("id_area")
        feature = Feature(geometry=geometry, properties=dict_item, id=id_area)
        geojson_features.append(feature)
    return jsonify(FeatureCollection(geojson_features))


@blueprint.route("/synthesis/chart", methods=["GET"])
def get_chart_synthesis():
    cd_nom = request.args.get("cd_nom")
    id_program = request.args.get("id_program")

    delta = ObservationModel.query.values(
        func.min(func.extract("year", ObservationModel.date)).label("min"),
        func.max(func.extract("year", ObservationModel.date)).label("max"),
    )

    for d in delta:
        data = d
        break
    date_list = func.generate_series(data.min, data.max).alias("label")
    label = column("label")
    query = (
        db.session.query(
            label,
            func.count(distinct(ObservationModel.cd_nom)).label("count_taxa"),
            func.count(ObservationModel.id_observation).label("count_occtax"),
        )
        .select_from(date_list)
        .outerjoin(
            ObservationModel,
            label == func.extract("year", ObservationModel.date),
        )
        .group_by(label)
        .order_by(label)
    )

    if id_program:
        query = query.filter(ObservationModel.id_program == id_program)
    if cd_nom:
        query = query.filter(ObservationModel.cd_nom == cd_nom)
    return jsonify([item._asdict() for item in query.all()])


@blueprint.route("/synthesis/list", methods=["GET"])
def getList():
    cd_nom = request.args.get("cd_nom")
    id_program = request.args.get("id_program")

    query = (
        db.session.query(
            ObservationModel.cd_nom,
            Taxref.lb_nom,
            Taxref.nom_vern,
            func.count(ObservationModel.id_observation).label("count_occtax"),
            func.max(ObservationModel.date).label("last_data"),
        )
        .join(Taxref, Taxref.cd_nom == ObservationModel.cd_nom)
        .group_by(ObservationModel.cd_nom, Taxref.lb_nom, Taxref.nom_vern)
        .order_by(func.count(ObservationModel.id_observation).desc())
    )

    if id_program:
        query = query.filter(ObservationModel.id_program == id_program)
    if cd_nom:
        query = query.filter(ObservationModel.cd_nom == cd_nom)

    return jsonify([row._asdict() for row in query.all()])
